# 更新日志（CHANGELOG）

版本命名规则：

- **MQTT 线**：`HA Monitor Display Mqtt vX.Y.Z`（数据全部由 HA 经 MQTT 推送）
- **API 线**：`HA Monitor Display API v0.9.0`（ESPHome Native API 拉取，前身版本）
- **通知线**：`HA Monitor Display Notify v2.0`（开发中）

## [未发布] — 2026-11-03（v3.1 概览页在线设备两格通用化）

**背景**：概览页右列上下两格的设备名原先写死为 `Nova13` / `Nova12`——不止屏幕文字，
连 JSON 键名（`nova13`/`nova12`）、固件全局变量（`hd_nova13`/`hd_nova12`）、模板实体
（`ha_nova13`/`ha_nova12`）都带着具体产品名，别人拿去用只能显示这两台设备。
本版把这两格彻底通用化：**名称不再固化在固件里，改由 HA 下发**。

### Changed

- JSON 键名：`nova13` / `nova12` → `device_a_online` / `device_b_online`
  （固件 `hd_device_a_online` / `hd_device_b_online`、模板实体
  `ha_device_a_online` / `ha_device_b_online` 同步改名）
- 屏幕两格：图标（固定色）+ **名称（HA 下发，可改）** + 状态（在线绿 / 离线灰），
  **三者排在同一行**（与原版观感一致，不做上下换行）；名称区宽 58px，超出自动截断
  （`long_mode: DOT`），状态固定在 x=88 不会被长名字挤走
- 名称为空时回退到「Nova13 / Nova12」（保留原有观感，仍可由 HA 覆盖）

### Added

- 新增两个**文本槽位** `device_a_name` / `device_b_name`：填纯文本（不是 entity_id），
  由推送包原样带到屏幕。槽位总数 49 → **51**

### 升级注意

- **需要重新编译烧录**（固件改了 JSON 键名与标签），同时替换
  `monitor_display_push.yaml`；两者都换完屏幕两格才恢复显示
- 只换固件不换推送包：两格显示 `--` + 默认名「Nova13/Nova12」，**不影响其他 47 个槽位**

### Changed（OTA 安全）

- `ota:` 去掉明文 `password`，也不再单独设 `encryption`：ESPHome 2026.10.1 强制 OTA 与 API
  的加密密钥一致，省略后自动复用 `api:` 的 `api_key`，不再浪费 Flash/RAM，也消掉编译警告
- `secrets.yaml` 去掉 `ota_password`（不再被引用，可保留，无副作用）

### Added（MQTT 端口可配）

- `mqtt:` 的 `port` 从写死 `1883` 改为 `!secret mqtt_port`，`secrets.yaml` 新增 `mqtt_port`
  （默认 1883）。生成器配置页同步增加「MQTT 端口」输入框，输出时按**裸数字**写入，不加引号
- TLS 8883 仍暂不支持（需额外证书与 `ssl` 配置），端口值留作后续扩展

> ⚠️ **升级注意**：从 `password` 切到加密密钥后，旧固件无法再用无线 OTA 连上，
> 必须 **USB 线刷一次**；之后恢复无线 OTA，密码为 `api_key`。

### 验证

- `esphome config`：Configuration is valid（含 `long_mode: DOT`、标签 `width`；OTA 无警告）
- `esphome compile`：编译通过，可直接线刷
- 推送包：YAML 解析 51 槽 / 渲染 56 键；jinja2 编译 + 双阶段渲染（无 SLOT 兜底 / 带 SLOT）
  均为合法 JSON，中文名称正确转义
- 生成器：按当前值重生成为与正式文件 **payload 一字不差**；模拟图 51 个键全覆盖
- 顺带修复生成页样式丢失（上一版替换 CSS 时误删 60 行基础样式，导致版面错乱）

## [未发布] — 2026-11-03（v3.0 第一档：实体槽位表化）

**背景**：推送包里 49 个实体 ID 硬编码在模板各处，换一个用户/换一个实体都要读懂模板。
v3.0 第一档把实体 ID 集中到文件头部的 `SLOT` 槽位表（49 行，带中文注释），
模板只引用 `SLOT.xxx`。

- **payload 与 v2 完全一致**：JSON 键名、顺序、取值逻辑逐键比对无差异；
  MQTT 主题/频率/retain、设备固件全部不动，**无需重编译烧录**
- 换实体 = 只改 SLOT 表右边 → 开发者工具→YAML→自动化 重新加载即生效
- `screen_bright` 保持硬编码（屏幕自身背光，由控制包创建，不开放选择）
- 为第二档（网页版配置生成器）打底：生成器输出 = 填好的 SLOT 表
- **修复（35f0983）**：v3 首版 payload 的字典字面量内部误放 Jinja 注释导致自动化装载失败
  （template value should be a string）；已移出注释并加固——SLOT 兜底 + 59 处引用
  加 `| default('')`，槽位表填错键名时仅该字段显示 `--`，不再拖垮整条推送

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
