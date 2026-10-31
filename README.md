# HA Monitor Display

ESP32-S3 桌面信息屏，跑 ESPHome + LVGL，显示 Home Assistant 的家庭概览 / 网络 / 系统三页数据。

## 硬件

| 项目 | 规格                                           |
| -- | -------------------------------------------- |
| 主控 | ESP32-S3 N16R8（16MB Flash + 8MB octal PSRAM） |
| 屏幕 | 4.0" ST7796S 320×480，SPI                     |
| 触摸 | FT6336U 电容触摸，I2C 地址 0x38                     |
| 供电 | 电池                                           |

引脚：SPI `clk=12 / mosi=11 / miso=13`，`cs=10 / dc=9 / rst=8`，背光 PWM `15`，触摸 I2C `scl=6 / sda=7 / rst=5`。GPIO35/36/37 被 PSRAM 占用，不可用。  
详细接线见 `硬件焊接接线指南.md`。

## 版本说明

**v1.0 — 硬件与外壳阶段的冻结基线。** 功能已定型，此后这条线只接受参数微调（默认亮度、休眠超时、触摸响应、配色观感），发 `v1.0.x`；新增功能一律进 `v2.0`，不混进来。

**v1.0.1 — 1.0 线的稳定定版（2026-10-31）。** 累积内容全部是观感与数据修正，未新增功能：8 个区块标题加 MDI 图标、改名（家居 / 网络运行 / NAS 运行）、字库补 19 字、第二轮配色方案落地、上证涨跌动态着色、`web_server` 认证改 digest、NAS 的 CPU/内存未载入时用基色、风扇「开 / ≤50%」改黄。已真机确认，出包 `HA Monitor Display Mqtt v1.0.1.zip`。

**v1.1.0 — 待真机验证（2026-10-31）。** 新增每页背景色 HA 下拉可调：`Dashboard / Network / System Bg Color` 三个 select，8 档深色预设，卡片色随选定色、屏幕四周 5px 与卡间 3px 缝隙取选定色 ×0.6。代码已同步到 ESPHome 真机目录作备份，**尚未编译验证，暂不出包**。

已知不包含：屏幕通知页（`page_notify.yaml` 与 `NR子流程-推送屏幕通知.json` 作为 v2.0 素材暂存本仓库，v1.0 的主配置未引用它们）。

## 文件结构

> 本仓库里 YAML 平铺在根目录；部署到 ESPHome 时把 `ui_*` / `page_*` 放进 `/config/esphome/ui/`，  
> 主配置 `ha-monitor-display.yaml` 留在 `/config/esphome/` 根下。

```
ha-monitor-display.yaml        主配置（含 esp32/wifi/mqtt/spi/屏/触摸/休眠）
ui_common.yaml                 字体、globals、公共控件        → ui/
page_dashboard.yaml            家庭页（电器、能耗、天气、居家模式、车位） → ui/
page_network.yaml              网络页（总览、NAS、风扇、低电量）  → ui/
page_system.yaml               系统页（三列指标、网络参数、SSID/IP） → ui/
monitor_display_push.yaml      HA 侧推送自动化（放到 /config/packages/）
fonts/                         中文字体 + MDI 图标字体

# v2.0 素材，v1.0 不生效
page_notify.yaml               通知页布局（UI 部分已完成）
NR子流程-推送屏幕通知.json       Node-RED 侧推送子流程
```

## 数据流

```
HA 自动化（每 5s） ──mqtt.publish──▶  home/ha-monitor-display (retain, QoS1)
                                          │
                              ESP32 mqtt.on_json_message 解析
                                          │
                                  hd_* globals  ──▶  LVGL 三页刷新
```

主题约定：数据帧 `home/ha-monitor-display`，通知 `.../notify`（retain=false），滚动新闻预留 `.../news`。broker 走外网，方案见 `外网MQTT方案说明.md`。

## 部署

1. `ha-monitor-display.yaml`、`ui/`、`fonts/` 放进 ESPHome 的 `/config/esphome/`
2. `ha/monitor_display_push.yaml` 放进 HA 的 `/config/packages/`，并在 `configuration.yaml` 里确认 `packages` 已启用
3. 编译烧录后，在 HA 里重载自动化；确认实体 `light.ha_monitor_display_screen_light` 存在（推送里的屏幕亮度取自它）

## v2.0 待办

- [ ] 屏幕通知页：`ui/page_notify.yaml` + 主配置 `mqtt.on_message` 段 + `ui_font_notify`（GB2312 一级 3755 字，12px bpp4，约 310KB）
- [ ] Node-RED 子流程导入 `NR子流程-推送屏幕通知.json`，选好 broker
- [ ] 滚动新闻 `home/ha-monitor-display/news`
- [ ] MQTT 1883 → 8883 + TLS

