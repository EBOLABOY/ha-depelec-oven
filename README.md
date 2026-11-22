# Depelec TD55 Ultra Steam Oven for Home Assistant
### 德普 TD55 Ultra 智能蒸烤箱 Home Assistant 集成插件

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/EBOLABOY/ha-depelec-oven?style=for-the-badge&color=blue)](https://github.com/EBOLABOY/ha-depelec-oven/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Validate](https://img.shields.io/github/actions/workflow/status/EBOLABOY/ha-depelec-oven/validate.yml?label=Validate&style=for-the-badge)](https://github.com/EBOLABOY/ha-depelec-oven/actions)

本项目为 **德普 (Depelec) TD55 Ultra 智能嵌入式蒸烤箱** 的 Home Assistant 独立集成插件。支持通过 **局域网 ALCS CoAP (UDP 5683 + AES-128-CBC 加密直连)** 与 **阿里云 LinkKit IoT 云端 API** 双通道控制，实现对蒸烤箱全部传感器状态的实时追踪与 22 种专业烹饪模式的全功能智能控制。

---

## ✨ 核心特性

- 🏠 **局域网 ALCS 本地直连（可彻底脱离云端）**：完整实现阿里云 LinkKit ALCS 本地安全协议（CoAP + SessionId + AES-128-CBC + 心跳保活），支持 `auto`（局域网优先、云端兜底）、`local`（纯局域网、0 云端通信）、`cloud`（纯云端）三种模式。
- 🌡️ **双温区温度监测**：实时采集上腔体实际温度、下发热管实时温度，以及上下管当前设定目标温度。
- ⏱️ **倒计时与时长跟踪**：实时显示剩余烹饪时长与设定总工作时间。
- 🛡️ **安全与异常检测**：实时感知炉门开合状态（`Door`）、水箱缺位/异常（`Cistern`）及水箱缺水报警（`WaterShortage`）。
- 🎛️ **22 种专业预设烹饪模式**：完整支持普通蒸、高温蒸、加湿烤、风扇烤、快烧烤、烘焙烤、慢烧烤、风焙烤、焙烤、煎烤、空气炸、串烤、蒸汽烤、炖煮、蒸烤同烹、烘干、保洁、解冻、发酵、保温、复热、清洁。
- ⚖️ **上下管独立控温**：针对烘焙烤、风扇烤、空气炸等 **9 种**专业模式，支持上下管独立设定目标温度（非独立控温模式下自动禁用下管调节）。
- 🕹️ **一键烹饪操作**：提供启动、暂停/继续、停止按钮，以及炉灯、童锁实体开关；指令下发失败自动反馈错误，避免虚假状态。
- 🔄 **自动凭据保活与 HA 原生异步存储**：自动将刷新后的阿里云 Token 及一次性拉取的局域网 ALCS 密钥持久化到 Home Assistant `.storage` 中，不阻塞事件循环。

---

## 📦 实体清单 (共 20 个实体)

> [!NOTE]
> 以下为集成实际注册的 20 个实体。由于采用中文实体名，Home Assistant 生成的 `entity_id` 以你本地实例“开发者工具 -> 状态”中显示的实际 ID 为准。

| 实体类型 | 实体名称 | `unique_id` 后缀 | 说明 |
| :--- | :--- | :--- | :--- |
| **Sensor** | 上腔实时温度 | `_current_temp` | 上腔实时温度 (°C) |
| **Sensor** | 下腔实时温度 | `_down_current_temp` | 下发热管实时温度 (°C) |
| **Sensor** | 上管设定温度 | `_target_temp` | 当前运行上管目标温度 (°C) |
| **Sensor** | 下管设定温度 | `_down_target_temp` | 当前运行下管目标温度 (°C) |
| **Sensor** | 剩余烹饪时间 | `_remaining_time` | 剩余烹饪时间 (min) |
| **Sensor** | 总设定时间 | `_total_time` | 设定总工作时间 (min) |
| **Sensor** | 工作状态 | `_work_state` | 待机 / 预约中 / 已暂停 / 加热中（属性含当前通信通道 `transport: local/cloud`） |
| **Sensor** | 当前烹饪模式 | `_current_mode` | 当前正在运行的烹饪模式名称 |
| **Binary Sensor** | 炉门 | `_door` | 炉门开合状态 (`Door`) |
| **Binary Sensor** | 水箱异常/缺位 | `_cistern` | 水箱是否未放置到位 (`Cistern`) |
| **Binary Sensor** | 水箱缺水警报 | `_water_shortage` | 水箱水位过低警报 (`WaterShortage`) |
| **Switch** | 炉灯 | `_light` | 炉内照明灯开关 (`LightSwitch`) |
| **Switch** | 童锁 | `_child_lock` | 儿童安全锁开关 (`ChildLockSwitch`) |
| **Select** | 预设烹饪模式 | `_mode_select` | 22 种烹饪预设模式下拉菜单 |
| **Number** | 上管/主腔设定温度 | `_number_target_temp` | 烹饪上部/主腔目标温度设定 (°C) |
| **Number** | 下管设定温度 | `_number_down_target_temp` | 烹饪下部目标温度设定（仅 9 种独立控温模式可用） |
| **Number** | 烹饪时长设定 | `_number_work_time` | 烹饪目标时长设定 (1 ~ 180 min) |
| **Button** | 启动烹饪 | `_start` | 按当前选择的模式、温度和时长启动烹饪 |
| **Button** | 暂停/继续 | `_pause` | 暂停或恢复运行中的烹饪任务 |
| **Button** | 停止烹饪 | `_stop` | 立即停止烹饪并回到待机状态 |

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
   ```text
   https://github.com/EBOLABOY/ha-depelec-oven
   ```
4. 类别选择：**集成 (Integration)**，点击 **添加 (Add)**。
5. 在 HACS 集成列表中找到 **Depelec TD55 Ultra Oven** 并点击 **下载 (Download)**。
6. 重启 Home Assistant。

### 方式二：手动安装

1. 克隆代码：
   ```bash
   git clone https://github.com/EBOLABOY/ha-depelec-oven.git
   ```
2. 将 `custom_components/depelec_oven` 完整拷贝至 Home Assistant 配置目录的 `custom_components/` 下。
3. 重启 Home Assistant。

---

## ⚙️ 配置说明

支持三种连接模式（`connection_mode`）：
- `auto`（默认，推荐）：**局域网优先，云端兜底**。首次启动自动通过阿里云 `/alcs/device/accessInfo/get` 拉取并缓存局域网 ALCS 密钥，之后所有轮询与控制均优先通过局域网 UDP 5683 直连；仅当本地不可达时自动回退云端。
- `local`：**纯局域网模式（彻底脱离云端）**。完全不访问任何阿里云服务器，只需配置局域网 IP 及一次性提取到的 `alcs_access_key` / `alcs_access_token`（若设备在断网离线状态下重启并回落至出厂默认密钥，也可自动尝试默认密钥）。
- `cloud`：**纯云端模式**。适用于 HA 与蒸烤箱跨网段、无法直连 UDP 5683 的场景。

### 方案 A：局域网优先 + 自动获取本地密钥（`auto`，推荐）

```yaml
depelec_oven:
  connection_mode: "auto"                       # auto / local / cloud (默认 auto)
  host: "192.168.100.106"                       # 蒸烤箱局域网 IP 地址
  port: 5683                                    # 局域网 ALCS CoAP 端口 (默认 5683)
  device_name: "your_device_name"               # 设备标识 (可留空由局域网 CoAP 自动发现)
  iot_id: "your_iot_id"                         # 阿里云 LinkKit 设备 iot_id
  identity_id: "your_identity_id"               # 用户云端身份标识 identityId
  initial_iot_token: "your_iot_token"           # 初始通信 Token (首次获取一次，后续自动续签)
  initial_refresh_token: "your_refresh_token"   # 刷新 Token
  scan_interval: 15                             # 状态轮询周期 (秒，默认 15 秒；局域网模式可设 5 秒)
```

> [!TIP]
> 在 `auto` 模式成功运行一次后，插件会自动将本地密钥写入 Home Assistant 的 `.storage/depelec_oven_auth`（字段为 `alcsAccessKey` 和 `alcsAccessToken`）。你可以直接复制出来切换到下方的纯局域网 `local` 模式，此后即可删除所有云端 Token 配置。

### 方案 B：纯局域网模式（`local`，完全脱离云端）

```yaml
depelec_oven:
  connection_mode: "local"
  host: "192.168.100.106"
  port: 5683
  device_name: "your_device_name"               # 可选，留空则自动通过 CoAP 发现
  alcs_access_key: "your_alcs_access_key"       # 从 .storage/depelec_oven_auth 复制
  alcs_access_token: "your_alcs_access_token"   # 从 .storage/depelec_oven_auth 复制
  scan_interval: 5
```

> [!TIP]
> **如何获取初始云端凭据？**
> 1. 蒸烤箱接入家庭 Wi-Fi 后，通过手机抓包工具（Charles、Fiddler、Reqable 等）捕获德普官方 App 请求；
> 2. 过滤域名 `api.link.aliyun.com`；
> 3. 提取 `iotToken`、`refreshToken`、`identityId` 及 `iotId` 填入配置，成功启动一次后即可自动续期并自动拉取局域网 ALCS 密钥。

---

## 📊 Lovelace 仪表盘配置示例

> 请先在 Home Assistant **开发者工具 -> 状态** 中确认你实际的 `entity_id` 后替换下方占位实体名：

```yaml
type: vertical-stack
cards:
  - type: entities
    title: 德普 TD55 Ultra 蒸烤箱
    entities:
      - entity: switch.depelec_oven_light
        name: 炉内照明灯
      - entity: switch.depelec_oven_child_lock
        name: 儿童安全锁
      - entity: sensor.depelec_oven_work_state
        name: 当前运行状态
      - entity: sensor.depelec_oven_current_mode
        name: 运行模式
      - entity: sensor.depelec_oven_current_temp
        name: 上腔实时温度
      - entity: sensor.depelec_oven_down_current_temp
        name: 下腔实时温度
      - entity: sensor.depelec_oven_remaining_time
        name: 剩余时间
      - entity: binary_sensor.depelec_oven_door
        name: 炉门状态
      - entity: binary_sensor.depelec_oven_cistern
        name: 水箱状态
      - entity: binary_sensor.depelec_oven_water_shortage
        name: 水箱缺水警报
  - type: entities
    title: 烹饪参数设定
    entities:
      - entity: select.depelec_oven_mode_select
        name: 烹饪模式选择
      - entity: number.depelec_oven_target_temp
        name: 上部设定温度
      - entity: number.depelec_oven_down_target_temp
        name: 下部设定温度
      - entity: number.depelec_oven_work_time
        name: 烹饪时长 (分钟)
  - type: horizontal-stack
    cards:
      - type: button
        name: 开始烹饪
        icon: mdi:play-circle-outline
        tap_action:
          action: perform-action
          perform_action: button.press
          target:
            entity_id: button.depelec_oven_start
      - type: button
        name: 暂停 / 继续
        icon: mdi:pause-circle-outline
        tap_action:
          action: perform-action
          perform_action: button.press
          target:
            entity_id: button.depelec_oven_pause
      - type: button
        name: 停止烹饪
        icon: mdi:stop-circle-outline
        tap_action:
          action: perform-action
          perform_action: button.press
          target:
            entity_id: button.depelec_oven_stop
```

---

## 🤝 贡献与反馈

欢迎提交 Issue 和 Pull Request！
如果您有其他德普型号蒸烤箱（如 TD55、TD50、TE55 等）并完成测试，欢迎共享模式参数！

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
