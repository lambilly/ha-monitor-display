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
// 标题上限 72 字节 ≈ 24 汉字。为什么不给更大：标题 label 的 DOT 省略号依赖
//   宽度约束才生效，而宽度在运行期未必稳；24 字 × 12px = 288px，加左边距 23
//   到 311px，仍然不会压到 x348 的时间，版式靠长度兜住而不是靠布局。
static const size_t TITLE_MAX = 72;

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

// ----------------------------------------------------------
// 硬折行（11-01 第三轮，用户「内容仍然没有换行、右边没有留白」后新增）
//   为什么不能只靠 LVGL 的 LV_LABEL_LONG_WRAP：
//     正文 label 的宽度在 set_text 之后会被文本重算覆盖（退成内容宽），
//     一旦宽度失守，WRAP 没有可用的「行宽」参照，整条正文就变成一行，
//     右端直接顶到卡片边框——连试两轮 set_width + update_layout 都没稳住。
//   所以在入库时就把长行自己切开，插真换行符：
//     · 换行符是硬断行，宽度策略再怎么变都照断；
//     · 每行最多 420px（12px 字号 35 个汉字），而正文可用宽 450px，
//       于是右侧天然留出 30px（用户 11-01 要求再宽 12px：432→420）；
//     · 行首避头点：，。！？、；：）」』】》 这类标点若正好落在行首，
//       就跟着上一行一起收尾（允许该行超宽 12px，仍在 450px 内）。
//   宽度口径（fontTools 实测 NotoSansSC-SemiBold，12px）：
//     汉字/全角/符号 12px，ASCII 字母数字 7px，空格 3px
//   LVGL 的 #RRGGBB 着色标记不计宽（两个 # 之间的六位十六进制原样透传）。
// ----------------------------------------------------------
static const int WRAP_PX = 420;

static inline int ch_px(uint32_t cp) {
  if (cp == ' ') return 3;
  if (cp < 0x80) return 7;
  return 12;
}

// 行首禁则标点（出现在行首会让版面难看）
static inline bool no_line_head(uint32_t cp) {
  switch (cp) {
    case ',' : case '.' : case '!' : case '?' : case ';' : case ':':
    case 0xFF0C: case 0x3002: case 0xFF01: case 0xFF1F: case 0x3001:   // ，。！？、
    case 0xFF1B: case 0xFF1A:                                            // ；：
    case 0xFF09: case 0x300D: case 0x300F: case 0x3011: case 0x300B:     // ）」』】》
    case 0x201D: case 0x2019:                                            // ” ’
      return true;
    default:
      return false;
  }
}

static inline bool is_hex6(const std::string &s, size_t p) {
  if (p + 6 > s.size()) return false;
  for (size_t k = 0; k < 6; k++) {
    const char c = s[p + k];
    const bool hex = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
    if (!hex) return false;
  }
  return true;
}

static std::string wrap_hard(const std::string &s) {
  std::string out;
  out.reserve(s.size() + s.size() / 24);

  int w = 0;            // 当前行已占宽度
  size_t i = 0;
  while (i < s.size()) {
    const unsigned char b = static_cast<unsigned char>(s[i]);

    // LVGL recolor 标记 #RRGGBB：原样抄，不占宽度（● 的色由它决定）
    if (b == '#' && is_hex6(s, i + 1)) {
      out.append(s, i, 7);
      i += 7;
      continue;
    }
    if (b == '#') {           // recolor 的收尾 #
      out += '#';
      i++;
      continue;
    }

    uint32_t cp = 0;
    size_t n = 1;
    if (b < 0x80)                { cp = b;          n = 1; }
    else if ((b & 0xE0) == 0xC0) { cp = b & 0x1F;   n = 2; }
    else if ((b & 0xF0) == 0xE0) { cp = b & 0x0F;   n = 3; }
    else if ((b & 0xF8) == 0xF0) { cp = b & 0x07;   n = 4; }
    else { i++; continue; }
    if (i + n > s.size()) break;
    for (size_t k = 1; k < n; k++) {
      const unsigned char c = static_cast<unsigned char>(s[i + k]);
      if ((c & 0xC0) != 0x80) { cp = 0; break; }
      cp = (cp << 6) | (c & 0x3F);
    }

    if (cp == '\n') {         // 原文换行：直接过，重新计宽
      out += '\n';
      w = 0;
      i += n;
      continue;
    }

    const int pw = ch_px(cp);
    // 放不下就断行；但禁则标点宁可挤在本行末尾，也不放到下一行行首
    if (w > 0 && w + pw > WRAP_PX && !no_line_head(cp)) {
      out += '\n';
      w = 0;
    }
    out.append(s, i, n);
    w += pw;
    i += n;
  }
  return out;
}

// 去重已并入 push（见下），这里不再单独暴露 is_dup

static void push(const std::string &title, const std::string &msg, uint32_t ts) {
  // normalize：换行/制表/转义归一
  // filter_known：挖掉字库没有的字（否则是方框）
  // wrap_hard：长行自己切成 ≤432px 的短行（不指望 LVGL 的 WRAP）
  std::string t = clip(filter_known(normalize(title.empty() ? std::string("通知") : title)), TITLE_MAX);
  std::string body = filter_known(normalize(msg));
  if (body.size() > 3300) body = clip(body, 3300);   // 先给折行留出 \n 的余量
  std::string b = clip(wrap_hard(body), MSG_MAX);
  const uint32_t tt = (ts != 0) ? ts : static_cast<uint32_t>(::time(nullptr));

  // 去重必须拿「处理后的值」比对（11-01 修）：以前在上层用原始载荷比，
  //   而缓冲区里存的是 normalize + filter + 折行之后的结果，两者永不相等，
  //   QoS1 的重投会重复入列。现在挪到入库前一刻做。
  if (count > 0) {
    const Slot &last = slots[(head - 1 + 8) % 8];
    if (last.ts == tt && last.title == t && last.msg == b) return;
  }

  Slot &s = slots[head];
  s.title = t;
  s.msg = b;
  s.ts = tt;
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
