# HA Monitor Display

ESP32-S3 电池供电的家庭信息屏：4.0" 触摸屏跑 ESPHome + LVGL，显示 Home Assistant 的家庭概览 / 网络 / 系统三页数据。本仓库提供两条数据通道的版本——**Native API 拉取（v0.9.0）** 与 **MQTT 推送（v1.x，推荐）**；屏幕通知页（Notify v2.0）开发中。

## 功能一览

- **三页信息 + 底部 TAB 触摸导航**（家庭 → 网络 → 系统）
  - 家庭页：电器 / 能耗 / 天气 / 居家模式（含音量、活动轨迹）/ 车位（状态 + 两辆车距离）
  - 网络页：网络总览 / NAS 运行 / 四路风扇（转速、温度、分档着色）/ 低电量
  - 系统页：CPU / 内存 / 存储三列指标、网络参数（RSSI / SIGQ / MQTT / WiFi）、SSID 与 IP、当前时间
- **熄屏休眠**：可调超时（15~900 s），触摸即醒；亮度滑块 + 断电记忆
- **每页背景色 8 档可调**（v1.1.0 起，HA 下拉选择，石墨 / 深红 / 深黄 / 墨绿 / 浅蓝 / 深蓝 / 深紫 / 深靛）
- 白字 + 图标承担配色的统一视觉规则；动态语义色（涨跌 / 居家模式 / 车位 / 风扇分档 / 信号分档 / 告警）保留

## 硬件

| 项目 | 规格 |
| -- | -- |
| 主控 | ESP32-S3 N16R8（16MB Flash + 8MB octal PSRAM） |
| 屏幕 | 4.0" ST7796S 320×480，SPI（横屏 480×320） |
| 触摸 | FT6336U 电容触摸，I2C 地址 0x38 |
| 供电 | 锂电池（实测熄屏待机约 20 mA） |

关键引脚：SPI `clk=12 / mosi=11 / miso=13`，屏幕 `cs=10 / dc=9 / rst=8`，背光 PWM `15`，触摸 I2C `scl=6 / sda=7 / rst=5`。
⚠️ GPIO35/36/37 被 octal PSRAM 占用不可用；GPIO26~32 接 Flash。详细接线（含 TF 卡槽预留、CTP_INT 说明）见 `硬件焊接接线指南.md`。

## 版本线

| 版本 | 发布包 | 数据通道 | 说明 |
| -- | -- | -- | -- |
| **API v0.9.0** | `HA Monitor Display API v0.9.0.zip` | ESPHome Native API 拉取 + MQTT/TLS 8883 远程（双通道） | 2026-10-29 快照，前身版本 |
| **Mqtt v1.0** | `HA Monitor Display Mqtt v1.0.zip` | HA 每 5 s `mqtt.publish` 推送 JSON | MQTT 线首个定版 |
| **Mqtt v1.0.1** | `HA Monitor Display Mqtt v1.0.1.zip` | 同上 | 观感与数据修正累积 |
| **Mqtt v1.1.0** | `HA Monitor Display Mqtt v1.1.0.zip` | 同上 | 背景色 8 档 + 白字规则等大改 |
| **Mqtt v1.1.1** | `HA Monitor Display Mqtt v1.1.1.zip` | 同上 | 续航优化，**当前推荐**，v2.0 前回退基线 |
| Notify v2.0 | 开发中 | MQTT + Node-RED 清洗链 | 屏幕通知页，发布名 `HA Monitor Display Notify v2.0` |

各版本详细变更见 [CHANGELOG.md](CHANGELOG.md)。

## 快速开始（MQTT 版 v1.1.1，推荐）

### 1. 准备 MQTT broker

任选 Mosquitto / EMQX。局域网 1883 即可跑通；走外网务必上 8883 + TLS（方案见 `项目外网MQTT方案说明.md`）。主题约定：

```
home/ha-monitor-display          数据帧（retain, QoS1，HA → 屏幕）
esphome/ha-monitor-display/...   设备侧前缀（日志等）
```

### 2. 写 `secrets.yaml`（与主配置同目录）

```yaml
wifi_ssid: your-wifi
wifi_password: your-wifi-password
ap_password: your-fallback-ap-password
ota_password: your-ota-password
api_key: "运行 esphome 时自动生成，或自填 32 字节 base64"
mqtt_broker: your-mqtt-broker-address   # 例如 home.example.top
mqtt_username: your-mqtt-username
mqtt_password: your-mqtt-password
web_password: your-web-password
```

> Mqtt 版主配置的 broker 地址与用户名同样走 `!secret`（`mqtt_broker` / `mqtt_username`），
> 上面模板已含全部 9 项。

### 3. 部署文件

```
/config/esphome/
├── ha-monitor-display.yaml      主配置
├── ui/                          page_dashboard / page_network / page_system / ui_common
└── fonts/                       NotoSansSC-SemiBold.ttf + materialdesignicons-webfont.ttf
/config/packages/
└── monitor_display_push.yaml    HA 侧 5 秒推送自动化
```

### 4. 编译烧录 + 启用自动化

ESPHome 里 Install（USB 首次，之后可 OTA）；在 HA 里重载自动化，确认 `packages` 已在 `configuration.yaml` 启用。设备上线后即可看到三页数据（5 s 一刷）。

## 快速开始（API 版 v0.9.0）

适合完全跑在局域网内、不想配 broker 的场景：数据由 ESPHome 通过 Native API 从 HA **主动拉取**（`platform: homeassistant` 传感器，51 处 entity_id），MQTT/TLS 8883 仅作远程备用通道。

1. 发布包解压后，`ha-monitor-display.yaml` 放 `/config/esphome/`，4 个 `page_*/ui_*` 放 `ui/`，`fonts/` 同级
2. `secrets.yaml` 模板同上（`mqtt_host` / `mqtt_password` 不用 broker 时可留占位）
3. **把主配置里的 `entity_id` 改成你家 HA 的实际实体**——这 51 处是按我家设备命名的（如 `sensor.lamnas_ws_cpu_utilization_total`）
4. 编译烧录后数据即拉即显（刷新率由各 sensor 的 `update_interval` 决定）

## 目录结构

```
ha-monitor-display.yaml     主配置（板型 / WiFi / MQTT / API / 屏 / 触摸 / 休眠 / LVGL 全局）
ui_common.yaml              字体、globals、公共控件              → ui/
page_dashboard.yaml         家庭页                              → ui/
page_network.yaml           网络页                              → ui/
page_system.yaml            系统页                              → ui/
monitor_display_push.yaml   HA 推送自动化（MQTT 版专用）          → /config/packages/
fonts/                      中文字体 + MDI 图标字体
项目外网MQTT方案说明.md      外网 MQTT/TLS 方案与踩坑
硬件焊接接线指南.md          接线 / 排针 / 焊接注意事项
CHANGELOG.md                更新日志
```

> 仓库内 YAML 平铺在根目录；发布包（zip）里已按 `ui/` 子目录组织，解压即用。

## 数据流（MQTT 版）

```
HA 自动化（每 5s，Jinja 组装 50 实体 JSON）
        │ mqtt.publish  →  home/ha-monitor-display (retain, QoS1)
        ▼
ESP32 mqtt.on_json_message ─▶ hd_* globals ─▶ LVGL 三页刷新
```

- 屏幕判"HA 离线"用数据新鲜度（>15 s 无新帧），不依赖 WiFi 状态
- 设备侧全局变量统一 `hd_*` 前缀；开关三态（null 显示 `--`）

## 功耗实测（真机，v1.1.1）

| 状态 | 电流 |
| -- | -- |
| 熄屏待机（60% 亮度 / 5s 推送 / modem-sleep） | **≈ 20 mA** |
| 亮屏 | ≈ 150~180 mA（每亮 1 分钟 ≈ 3 mAh） |

续航推算：500 mAh ≈ 21 h，1000 mAh ≈ 42 h，18650 3000 mAh ≈ 一周。

## 开发注意事项（踩过的坑）

- **中文字库是白名单制**：所有 `text:` 与 lambda 字符串里出现的汉字必须在字体 `glyphs` 里，改文案后要补字（有配套缺字扫描脚本）
- 字号三档 12 / 16 / 20（NotoSansSC-SemiBold），配 16px 文字的 MDI 图标用 20px 字体 + label 高 18，否则偏小偏上
- LVGL v9 的 label 未显式给宽度时是 `SIZE_CONTENT`（宽度随文本），依赖固定宽度的布局必须显式 `width`
- ESPHome `logs:` 的 tag 级别不能比全局 `level` 更细；`!include` 相对包含文件所在目录
- broker 走 1883 明文仅限局域网调试，外网务必 8883 + TLS

## 文档索引

- [CHANGELOG.md](CHANGELOG.md) — 各版本更新日志
- `硬件焊接接线指南.md` — 接线、排针定义、焊接顺序
- `项目外网MQTT方案说明.md` — 外网 MQTT/TLS 方案（DDNS / 端口映射 / 证书）
- `v2.0-NOTIFY方案.md` — 通知页设计稿（开发中）
