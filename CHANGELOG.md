# 更新日志（CHANGELOG）

版本命名规则：

- **MQTT 线**：`HA Monitor Display Mqtt vX.Y.Z`（数据全部由 HA 经 MQTT 推送）
- **API 线**：`HA Monitor Display API v0.9.0`（ESPHome Native API 拉取，前身版本）
- **通知线**：`HA Monitor Display Notify v2.0`（开发中）

## [未发布] — 2026-11-02（v2.1 远程控制通道，基于 v2.0 通知线）

**背景**：亮度 / 亮屏时间 / 两个开关原先只走 ESPHome Native API，要求 HA 能主动连到屏幕。
屏幕带出门（无公网 IP、穿过 NAT）后这条控制线必断；而 MQTT 是设备主动往外连，不受影响。
于是数据一直好、控制全废。本版把控制也搬到 MQTT。

### Added

- **设备端 5 个控制主题**（`mqtt.on_message`，QoS1，全部 retain）：
  `cmd/light`（ON/OFF）、`cmd/bright`（10~100）、`cmd/sleep`（15~900）、
  `cmd/autosleep`（ON/OFF）、`cmd/wake`（ON/OFF）
- **状态回发**：`esphome/ha-monitor-display/state`（retain）一帧 JSON
  `{"light":...,"bright":...,"sleep":...,"autosleep":...,"wake":...}`，
  每次控制量变化 + 开机 20 s 后各发一次，HA 面板实时跟随
- **HA 侧新包** `ha/monitor_display_control.yaml`：5 个 `mqtt` 实体
  （1 灯 + 2 数值 + 2 开关），归到一个「HA Monitor Display 远程控制」设备下

### Changed

- 控制动作全部复用现有实体逻辑（滑块 `set_action` / `switch.turn_on` / 休眠脚本），
  不新增状态变量，本机触摸操作与远程下发走同一条路径

### 注意

- `cmd` 主题 retain → 设备重连/重启会重放 HA 最后一次下发的值，
  即「重启后以 HA 侧为准」（比本机 `restore_value` 更可预期）
- 局域网内原生 API 那 5 个实体与远程这 5 个并存，出门后只剩远程这套可用

---

## [v1.1.1] — 2026-11-01（MQTT 线，当前推荐 / v2.0 前回退基线）

本版只做续航优化，**不动任何界面与数据协议**，可从 v1.1.0 直接 OTA 升级。

### Changed

- **WiFi 省电**：`wifi.power_save_mode: light`（modem-sleep）。数据帧仍为 5 s 一推，实测无感知影响；待机电流明显下降（约省 1/3）
- **默认屏幕亮度 60%**：`ui_saved_brightness` 初值 0.6 成为唯一来源——开机点亮（lvgl `on_boot`）与熄屏恢复同源，不再各写各的；亮度滑块调整后自动回写该全局变量

### Fixed

- 开机满亮闪变：灯实体 `restore_mode` 由 `ALWAYS_ON` 改为 `ALWAYS_OFF`，开机不再自带 100% 点亮，由 `on_boot` 按 `ui_saved_brightness` 点亮

### 实测（真机）

| 状态 | 电流 |
| -- | -- |
| 熄屏待机（60% 亮度 / 5s 推送 / modem-sleep） | **≈ 20 mA** |
| 亮屏 | ≈ 150~180 mA |

续航推算：500 mAh ≈ 21 h，1000 mAh ≈ 42 h，18650 3000 mAh ≈ 一周。

---

## [v1.1.0] — 2026-10-31（MQTT 线）

本月最后一轮大改，观感与功能并重：

- **每页背景色 HA 下拉可调**：`Dashboard / Network / System Bg Color` 三个 select，8 档深色预设（石墨 / 深红 / 深黄 / 墨绿 / 浅蓝 / 深蓝 / 深紫 / 深靛），卡片色随选定色、缝隙取选定色 ×0.5
- **白字规则统一**：静态文字一律纯白，配色改由图标承担（TAB 当前页与区块标题图标统一青 `4FD8FA`）；动态语义色保留（涨跌 / 居家模式 / 车位 / 风扇分档 / SIGQ / 告警 / 低电量数字）
- 车位卡改左右分栏：左列图标 + 车位状态，右栏两行车辆距离（12px）
- 居家模式加音量百分比（随模式色）
- 系统页行 1 加当前时间（SNTP 北京时间，前置黄色时钟图标）
- 今日能耗四行改为 电压 / 水压 / 用气 / 用电；三页 TAB 偏移与行 1 左边界对齐

---

## [v1.0.1] — 2026-10-31（MQTT 线）

1.0 线的稳定定版，全部为观感与数据修正，未新增功能：

- 8 个区块标题加 MDI 图标；页面改名（家居 / 网络运行 / NAS 运行）
- 字库补 19 字；第二轮配色方案落地
- 上证指数涨跌动态着色（涨红跌绿）
- `web_server` 认证改 digest
- NAS 的 CPU / 内存未载入时用基色（不再误报告警色）
- 风扇「开 / ≤50%」状态字改黄

---

## [v1.0] — 2026-10-30（MQTT 线首个定版）

- 三页 UI（家庭 / 网络 / 系统）+ 底部 TAB 触摸导航
- 数据通道：HA 自动化每 5 s `mqtt.publish` 推 50 实体 JSON，屏幕 `on_json_message` 解析进 `hd_*` 全局变量
- 熄屏休眠（可调 15~900 s，触摸即醒）、亮度滑块、断电记忆
- 硬件冻结基线，此后 1.x 线只接受参数微调

---

## [API v0.9.0] — 2026-10-29（API 线，前身版本）

- 数据由 ESPHome 通过 **Native API 从 HA 主动拉取**（`platform: homeassistant` 传感器 / text_sensor / binary_sensor，共 51 处 entity_id），刷新率由各 sensor 的 `update_interval` 决定
- 同时保留 **MQTT/TLS 8883 远程通道**（方案 C 双通道设计）：局域网走 API 低延迟，外网走 MQTT 可远程读取
- 三页 UI 与 MQTT 线同源，但字号体系（12/16/20）与字库（453 字白名单）为早期版本
- 部署时需把主配置里的 entity_id 改成自己 HA 的实际实体
