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

// 与最新一条完全相同时视为重复（QoS1 可能重复投递）
static bool is_dup(const std::string &title, const std::string &msg, uint32_t ts) {
  if (count == 0) return false;
  const Slot &last = slots[(head - 1 + 8) % 8];
  return last.ts == ts && last.title == title && last.msg == msg;
}

static void push(const std::string &title, const std::string &msg, uint32_t ts) {
  Slot &s = slots[head];
  s.title = clip(title.empty() ? std::string("通知") : title, TITLE_MAX);
  s.msg = clip(msg, MSG_MAX);
  s.ts = (ts != 0) ? ts : static_cast<uint32_t>(::time(nullptr));
  head = (head + 1) % 8;
  if (count < 8) count++;
  unread++;
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
