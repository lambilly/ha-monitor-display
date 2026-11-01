// ==========================================================
// v2.0 NOTIFY：通知环形缓冲（8 槽）
// ----------------------------------------------------------
// 设计要点：
//   · 热点在 MQTT 回调里写入、在页面 1s 巡检里读取，两边都在主线程，
//     不需要加锁；只是把“存哪、怎么截断、怎么判重复”收在一处，
//     避免 lambda 里堆一大堆字符串处理代码。
//   · 截断按 UTF-8 字节边界回退，绝不切出半个汉字（屏幕会显示方块/乱码）。
//   · rev 是内容版本号：页面只在 rev 变化时重刷 label，
//     否则每秒 12 次 lv_label_set_text 会白耗 SPI 与 CPU。
// ==========================================================
#pragma once

#include <cstdint>
#include <cstring>
#include <ctime>
#include <string>
#include <vector>

#include "notify_charset.h"   // 自动生成的字形码表（.workbuddy/gen_charset_h.py）

namespace ns_notify {

struct Slot {
  std::string title;
  std::string msg;
  uint32_t ts = 0;
};

static Slot slots[8];
static int count = 0;     // 有效条数 0..8
static int head = 0;      // 下一条写入位置
static int unread = 0;    // 未读条数（进通知页清零）
static int view = 0;      // 当前浏览位置：0 = 最新，越大越旧
static uint32_t rev = 1;  // 内容版本号

// 单条正文上限（字节）。ESP-IDF 的 MQTT 接收缓冲是 4096，
// 留出 topic 与协议开销，正文封顶 3500；家居简报（约 3.3KB）刚好装下。
static const size_t MSG_MAX = 3500;
static const size_t TITLE_MAX = 90;   // ≈30 汉字

// 按 UTF-8 字符边界截断，超长补省略号
static std::string clip(const std::string &s, size_t maxb) {
  if (s.size() <= maxb) return s;
  size_t cut = maxb;
  while (cut > 0 && (static_cast<unsigned char>(s[cut]) & 0xC0) == 0x80) cut--;
  return s.substr(0, cut) + "…";
}

static inline bool is_space(char c) { return c == ' ' || c == '\t'; }

// 文本规整（11-01 用户反馈「没有按原通知换行」后新增）
//   1) CRLF / CR 统一成 LF，去掉 BOM
//   2) 字面量转义还原：MQTT 载荷若被上游多转义一层，换行会变成两个字符 \ 和 n
//      —— 这里还原成真换行，否则整条通知挤成一行
//   3) 制表符变空格，逐行去首尾空格，连续 3 个以上换行压成 2 个
static std::string normalize(const std::string &in) {
  std::string s;
  s.reserve(in.size());

  size_t i = 0;
  if (in.size() >= 3 && (unsigned char) in[0] == 0xEF && (unsigned char) in[1] == 0xBB &&
      (unsigned char) in[2] == 0xBF) {
    i = 3;                                     // UTF-8 BOM
  }
  for (; i < in.size(); i++) {
    const char c = in[i];
    if (c == '\r') continue;                   // CRLF / CR → 只留 LF
    if (c == '\\' && i + 1 < in.size()) {
      const char n = in[i + 1];
      if (n == 'n') { s += '\n'; i++; continue; }
      if (n == 't') { s += ' ';  i++; continue; }
      if (n == '"') { s += '"';  i++; continue; }
      if (n == '\\') { s += '\\'; i++; continue; }
    }
    s += (c == '\t') ? ' ' : c;
  }

  // 逐行 trim + 连续空行压缩成 1 个
  std::vector<std::string> lines;
  size_t pos = 0;
  while (true) {
    const size_t nl = s.find('\n', pos);
    const size_t end = (nl == std::string::npos) ? s.size() : nl;
    size_t b = pos, e = end;
    while (b < e && is_space(s[b])) b++;
    while (e > b && is_space(s[e - 1])) e--;
    lines.push_back(s.substr(b, e - b));
    if (nl == std::string::npos) break;
    pos = nl + 1;
  }
  while (!lines.empty() && lines.back().empty()) lines.pop_back();

  std::string out;
  out.reserve(s.size());
  int blanks = 0;
  for (const auto &ln : lines) {
    if (ln.empty()) { blanks++; continue; }
    if (!out.empty()) out += (blanks > 0) ? "\n\n" : "\n";
    out += ln;
    blanks = 0;
  }
  return out;
}

// 与最新一条完全相同时视为重复（QoS1 可能重复投递）
static bool is_dup(const std::string &title, const std::string &msg, uint32_t ts) {
  if (count == 0) return false;
  const Slot &last = slots[(head - 1 + 8) % 8];
  return last.ts == ts && last.title == title && last.msg == msg;
}

static void push(const std::string &title, const std::string &msg, uint32_t ts) {
  Slot &s = slots[head];
  // normalize：换行/制表/转义归一；filter_known：挖掉字库没有的字（否则是方框）
  s.title = clip(filter_known(normalize(title.empty() ? std::string("通知") : title)), TITLE_MAX);
  s.msg = clip(filter_known(normalize(msg)), MSG_MAX);
  s.ts = (ts != 0) ? ts : static_cast<uint32_t>(::time(nullptr));
  head = (head + 1) % 8;
  if (count < 8) count++;
  unread++;
  rev++;
}

// 清空全部（切换条「全部删除」用）
static void clear_all() {
  for (int i = 0; i < 8; i++) {
    slots[i].title.clear();
    slots[i].msg.clear();
    slots[i].ts = 0;
  }
  count = 0;
  head = 0;
  unread = 0;
  view = 0;
  rev++;
}

// i = 0 是最新一条；越界返回空槽
static const Slot &at(int i) {
  static Slot empty_slot;
  if (i < 0 || i >= count) return empty_slot;
  return slots[((head - 1 - i) % 8 + 8) % 8];
}

// 删除第 i 条（0 = 最新）：把剩下的按“旧→新”重排回数组，保持环形不变式
static void remove_at(int i) {
  if (i < 0 || i >= count) return;
  Slot tmp[8];
  int n = 0;
  for (int k = count - 1; k >= 0; k--) {     // 从最旧到最新
    if (k == i) continue;
    tmp[n++] = at(k);
  }
  for (int k = 0; k < n; k++) slots[k] = tmp[k];
  count = n;
  head = n % 8;
  if (view > count - 1) view = (count > 0) ? count - 1 : 0;
  rev++;
}

}  // namespace ns_notify
