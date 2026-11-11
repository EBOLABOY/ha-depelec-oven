# Depelec TD55 Ultra Steam Oven for Home Assistant
### 德普 TD55 Ultra 智能蒸烤箱 Home Assistant 集成插件

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/EBOLABOY/ha-depelec-oven?style=for-the-badge&color=blue)](https://github.com/EBOLABOY/ha-depelec-oven/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Hassfest](https://img.shields.io/github/actions/workflow/status/EBOLABOY/ha-depelec-oven/validate.yml?label=Hassfest&style=for-the-badge)](https://github.com/EBOLABOY/ha-depelec-oven/actions)

本项目为 **德普 (Depelec) TD55 Ultra 智能嵌入式蒸烤箱** 的 Home Assistant 独立集成插件。通过逆向分析阿里云 LinkKit IoT 云端 API 及局域网 CoAP 控制协议，实现对蒸烤箱全部传感器状态的毫秒级追踪与 22 种专业烹饪模式的全功能智能控制。

---

## ✨ 核心特性

- 🌡️ **双温区温度监测**：实时采集上腔体实际温度与下发热管温度，精准掌握烘焙火候。
- ⏱️ **倒计时与时长跟踪**：实时显示剩余烹饪时长、总工作时间及预约时长。
- 🛡️ **安全与异常检测**：实时感知炉门开合状态（`door`）、缺水报警（`water_lack`）及加热中状态。
- 🎛️ **22 种专业预设烹饪模式**：完整支持普通蒸、高温蒸、加湿烤、风扇烤、快烧烤、烘焙烤、慢烧烤、风焙烤、焙烤、煎烤、空气炸、串烤、蒸汽烤、炖煮、蒸烤同烹、烘干、保洁、解冻、发酵、保温、复热、清洁。
- ⚖️ **上下管独立控温**：针对烘焙烤、空气炸等 7 种专业模式，支持上下管独立设定目标温度（`number` 实体调节）。
- 🕹️ **一键烹饪操作**：提供一键启动、暂停、停止、清空缺水报警按钮，以及电源和炉灯实体开关。
- 🔄 **自动凭据保活与持久化**：内置阿里云 IoT 令牌自动续签与刷新机制，Token 自动缓存于 Home Assistant `.storage` 中，避免凭证过期。

---

## 📦 实体清单 (Entities)

| 实体类型 | 实体名称 (Entity ID) | 说明 |
| :--- | :--- | :--- |
| **Sensor** | `sensor.depelec_current_temperature` | 上腔实时温度 (°C) |
| **Sensor** | `sensor.depelec_down_current_temperature` | 下发热管实时温度 (°C) |
| **Sensor** | `sensor.depelec_target_temperature` | 上部设定目标温度 (°C) |
| **Sensor** | `sensor.depelec_down_target_temperature` | 下部设定目标温度 (°C) |
| **Sensor** | `sensor.depelec_remaining_time` | 剩余烹饪时间 (min) |
| **Sensor** | `sensor.depelec_total_time` | 设定总工作时间 (min) |
| **Sensor** | `sensor.depelec_work_state` | 工作状态 (待机 / 预约中 / 已暂停 / 加热中) |
| **Sensor** | `sensor.depelec_current_mode` | 当前正在运行的烹饪模式名称 |
| **Binary Sensor** | `binary_sensor.depelec_door_state` | 炉门开合状态 (开/关) |
| **Binary Sensor** | `binary_sensor.depelec_water_tank_state` | 水箱状态 (正常 / 缺水警报) |
| **Binary Sensor** | `binary_sensor.depelec_heating_state` | 核心发热管工作状态 (加热中 / 停止) |
| **Binary Sensor** | `binary_sensor.depelec_light_state` | 炉内照明灯状态 |
| **Switch** | `switch.depelec_power` | 蒸烤箱整机电源开关 |
| **Switch** | `switch.depelec_light` | 炉内照明灯开关 |
| **Number** | `number.depelec_target_temperature` | 烹饪上部目标温度滑动调节器 |
| **Number** | `number.depelec_down_target_temperature` | 烹饪下部目标温度滑动调节器 (支持独立控温模式) |
| **Number** | `number.depelec_target_duration` | 烹饪目标时长滑动调节器 (min) |
| **Select** | `select.depelec_cooking_mode` | 22 种烹饪预设模式下拉菜单 |
| **Button** | `button.depelec_start_cooking` | 一键下发指令开始烹饪 |
| **Button** | `button.depelec_pause_cooking` | 暂停当前烹饪 |
| **Button** | `button.depelec_stop_cooking` | 停止烹饪回到待机 |
| **Button** | `button.depelec_clear_tank_alert` | 清空/复位水箱缺水警报 |

---

## 🥘 22 种内置烹饪模式参数表

| 模式名称 | 协议服务名 (Service) | 允许温区 (°C) | 默认温度 | 默认时长 | 上下独立控温 |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **普通蒸** | `OrdinarySteamed` | 30 ~ 100℃ | 100℃ | 30 min | ✕ |
| **高温蒸** | `HighTemperatureSteam` | 90 ~ 120℃ | 110℃ | 30 min | ✕ |
| **烘焙烤** | `Bake` | 60 ~ 180℃ | 180℃ | 35 min | ✔️ |
| **风扇烤** | `FanBake` | 60 ~ 230℃ | 230℃ | 35 min | ✔️ |
| **快烧烤** | `FastRoast` | 60 ~ 200℃ | 200℃ | 30 min | ✔️ |
| **加湿烤** | `HumidBake` | 60 ~ 220℃ | 200℃ | 30 min | ✔️ |
| **慢烧烤** | `SlowRoast` | 60 ~ 230℃ | 180℃ | 45 min | ✔️ |
| **风焙烤** | `WindBaked` | 30 ~ 230℃ | 200℃ | 30 min | ✔️ |
| **焙烤** | `RoasterBaked` | 30 ~ 230℃ | 180℃ | 30 min | ✔️ |
| **煎烤** | `Decoct` | 60 ~ 140℃ | 140℃ | 30 min | ✔️ |
| **空气炸** | `AirFry` | 30 ~ 230℃ | 200℃ | 25 min | ✔️ |
| **串烤** | `RoastSkewer` | 120 ~ 200℃ | 190℃ | 15 min | ✕ |
| **蒸汽烤** | `SteamRoast` | 120 ~ 200℃ | 200℃ | 30 min | ✕ |
| **炖煮** | `Stew` | 60 ~ 150℃ | 125℃ | 40 min | ✕ |
| **蒸烤同烹** | `SteamBakeTogether` | 120 ~ 200℃ | 200℃ | 30 min | ✕ |
| **烘干** | `Drying` | 固定 150℃ | 150℃ | 10 min | ✕ |
| **保洁** | `Sanitize` | 80 ~ 120℃ | 100℃ | 60 min | ✕ |
| **解冻** | `Defrost` | 固定 60℃ | 60℃ | 50 min | ✕ |
| **发酵** | `Ferment` | 30 ~ 45℃ | 30℃ | 30 min | ✕ |
| **保温** | `KeepWarm` | 固定 50℃ | 50℃ | 60 min | ✕ |
| **复热** | `Reheat` | 固定 100℃ | 100℃ | 10 min | ✕ |
| **清洁** | `Clean` | 固定 80℃ | 80℃ | 5 min | ✕ |

---

## 🚀 安装方法

### 方式一：通过 HACS 自定义存储库安装（推荐）

1. 确保已在 Home Assistant 中安装 [HACS](https://hacs.xyz/)。
2. 打开 **HACS** -> 右上角 **三点菜单** -> **自定义存储库 (Custom repositories)**。
3. 输入存储库地址：
   ```
   https://github.com/EBOLABOY/ha-depelec-oven
   ```
4. 类别选择：**集成 (Integration)**，点击 **添加 (Add)**。
5. 在 HACS 集成列表中找到 **Depelec TD55 Ultra Oven** 并点击 **下载 (Download)**。
6. 重启 Home Assistant。

### 方式二：手动安装

1. 下载本仓库发布包或克隆代码：
   ```bash
   git clone https://github.com/EBOLABOY/ha-depelec-oven.git
   ```
2. 将其中的 `custom_components/depelec_oven` 文件夹完整拷贝至您的 Home Assistant 配置目录中的 `custom_components/` 目录下（如 `/config/custom_components/depelec_oven/`）。
3. 重启 Home Assistant。

---

## ⚙️ 配置说明

在您的 `configuration.yaml` 中添加以下配置项：

```yaml
depelec_oven:
  host: "192.168.100.106"                   # 蒸烤箱局域网 IP 地址
  port: 5683                                # 局域网 CoAP 通信端口 (默认 5683)
  device_name: "your_device_name"           # 设备标识 / MAC (可通过抓包或路由器获取)
  iot_id: "your_iot_id"                     # 阿里云 LinkKit 设备 iot_id
  identity_id: "your_identity_id"           # 用户云端身份标识 identityId
  initial_iot_token: "your_iot_token"       # 初始通信 Token (抓包获取一次即可，后续自动续签)
  initial_refresh_token: "your_refresh_token" # 刷新 Token
  scan_interval: 5                          # 状态轮询周期 (秒，默认 5 秒)
```

> [!TIP]
> **如何获取通信凭据？**
> 1. 蒸烤箱接入家庭 Wi-Fi 后，通过手机抓包工具（如 Charles、Fiddler、Reqable 或 Wireshark）捕获德普官方 App 登录与控制数据包；
> 2. 过滤域名 `iotx-api.aliyun.com` 或 `api.link.aliyun.com`；
> 3. 在请求头或返回数据中提取 `iotToken`、`refreshToken`、`identityId` 及 `iotId` 填入配置；
> 4. 配置完成后只需成功通信一次，插件会自动续期 Token 并将最新凭据持久化存储在 HA 内部，后续无需再次抓包。

---

## 📊 Lovelace 仪表盘配置示例

您可以使用标准的 Entities 卡片或 Tile 卡片快速搭建蒸烤箱专属控制面板：

```yaml
type: vertical-stack
cards:
  - type: entities
    title: 德普 TD55 Ultra 蒸烤箱
    entities:
      - entity: switch.depelec_power
        name: 蒸烤箱电源
      - entity: switch.depelec_light
        name: 炉内照明灯
      - entity: sensor.depelec_work_state
        name: 当前运行状态
      - entity: sensor.depelec_current_mode
        name: 运行模式
      - entity: sensor.depelec_current_temperature
        name: 上腔实时温度
      - entity: sensor.depelec_down_current_temperature
        name: 下腔实时温度
      - entity: sensor.depelec_remaining_time
        name: 剩余时间
      - entity: binary_sensor.depelec_door_state
        name: 炉门状态
      - entity: binary_sensor.depelec_water_tank_state
        name: 水箱缺水警报
  - type: entities
    title: 烹饪参数设定
    entities:
      - entity: select.depelec_cooking_mode
        name: 烹饪模式选择
      - entity: number.depelec_target_temperature
        name: 上部设定温度
      - entity: number.depelec_down_target_temperature
        name: 下部设定温度
      - entity: number.depelec_target_duration
        name: 烹饪时长 (分钟)
  - type: horizontal-stack
    cards:
      - type: button
        name: 开始烹饪
        icon: mdi:play-circle-outline
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.depelec_start_cooking
      - type: button
        name: 暂停
        icon: mdi:pause-circle-outline
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.depelec_pause_cooking
      - type: button
        name: 结束停止
        icon: mdi:stop-circle-outline
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.depelec_stop_cooking
```

---

## 🤝 贡献与反馈

欢迎提交 Issue 和 Pull Request！
如果您有其他德普型号蒸烤箱（如 TD55、TD50、TE55 等）并完成测试，欢迎共享模式参数！

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
