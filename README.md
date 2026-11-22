# Depelec TD55 Ultra Steam Oven for Home Assistant
### 德普 TD55 Ultra 智能蒸烤箱 Home Assistant 集成插件

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/EBOLABOY/ha-depelec-oven?style=for-the-badge&color=blue)](https://github.com/EBOLABOY/ha-depelec-oven/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Validate](https://img.shields.io/github/actions/workflow/status/EBOLABOY/ha-depelec-oven/validate.yml?label=Validate&style=for-the-badge)](https://github.com/EBOLABOY/ha-depelec-oven/actions)

本项目为 **德普 (Depelec) TD55 Ultra 智能嵌入式蒸烤箱** 的 Home Assistant 独立集成插件。支持通过 **局域网 ALCS CoAP (UDP 5683 + AES-128-CBC 加密直连)** 与 **阿里云 LinkKit IoT 云端 API** 双通道控制，实现对蒸烤箱全部 18 项硬件遥测状态的实时追踪、22 种专业烹饪模式（含三档蒸汽/湿度调节、上下管独立控温、预约延迟启动、水路维护）及自动化服务的完整支持。

---

## ✨ 核心特性

- 🏠 **局域网 ALCS 本地直连（可彻底脱离云端）**：完整实现阿里云 LinkKit ALCS 本地安全协议（CoAP + SessionId + AES-128-CBC + 心跳保活），支持 `auto`（局域网优先、云端兜底）、`local`（纯局域网、0 云端通信）、`cloud`（纯云端）三种模式。
- 🌡️ **双温区温度与进度监测**：实时采集上腔体实际温度、下发热管实时温度、上下管设定目标温度，以及自动计算的烹饪进度百分比。
- ⏱️ **预约烹饪与双倒计时跟踪**：支持设定 0 ~ 1440 分钟延迟预约启动（`AppointmentTime`），并实时追踪预约设定时间、预约剩余倒计时、总设定时长及剩余烹饪时长。
- 💨 **三档蒸汽 / 湿度档位调节**：针对普通蒸、高温蒸（三档蒸汽）与蒸汽烤（三档湿度）完整下发 `SteamGear`（低/中/高三档），并实时回显当前运行档位。
- 💧 **水路与安全全监控**：实时监测炉门（`Door`）、水箱在位/闭合（`Cistern`）、水箱缺水（`WaterShortage`），并提供**一键排水**（`Draining`）、**强制抽水**（`MandatoryPumping`）和**弹出水箱**（`WaterMoto`）控制实体。
- 🎛️ **22 种专业预设烹饪模式（全协议实证校准）**：全部 22 种模式的 Alink 服务标识符与默认温时均已对照德普官方 TD55 Ultra 配置与最新版烹客 App v2.8.2 完整校准。
- ⚖️ **上下管独立控温**：针对烘焙烤、风扇烤、空气炸等 **9 种**专业模式支持上下管独立控温；修改上管温度时未拆分的下管温度自动联动，拆分后独立调节。
- ⚡ **原生 HA 自动化服务 (`depelec_oven.start_cooking`)**：支持在自动化/脚本/语音助手中用单次服务调用一键指定模式、温度、时长、蒸汽档位和预约时间。
- 🔄 **自动凭据保活与 HA 原生异步存储**：自动将刷新后的阿里云 Token 及一次性拉取的局域网 ALCS 密钥持久化到 Home Assistant `.storage` 中，不阻塞事件循环。

---

## 📦 实体清单 (共 29 个实体)

> [!NOTE]
> 以下为集成实际注册的 29 个实体。由于采用中文实体名，Home Assistant 生成的 `entity_id` 以你本地实例“开发者工具 -> 状态”中显示的实际 ID 为准。

| 实体类型 | 实体名称 | `unique_id` 后缀 | 说明 |
| :--- | :--- | :--- | :--- |
| **Sensor** | 上腔实时温度 | `_current_temp` | 上腔实时温度 (°C) |
| **Sensor** | 下腔实时温度 | `_down_current_temp` | 下发热管实时温度 (°C) |
| **Sensor** | 上管设定温度 | `_target_temp` | 当前运行上管目标温度 (°C) |
| **Sensor** | 下管设定温度 | `_down_target_temp` | 当前运行下管目标温度 (°C) |
| **Sensor** | 剩余烹饪时间 | `_remaining_time` | 剩余烹饪时间 (min) |
| **Sensor** | 总设定时间 | `_total_time` | 设定总工作时间 (min) |
| **Sensor** | 工作状态 | `_work_state` | 待机 / 预约中 / 已暂停 / 加热中 / 预热中 / 保温中 / 清洗中（属性含 `transport`、`work_state_code`、`mode_id`） |
| **Sensor** | 当前烹饪模式 | `_current_mode` | 当前正在运行的烹饪模式名称 |
| **Sensor** | 预约设定时间 | `_appointment_time` | 当前已下发的预约延迟时间 (min) |
| **Sensor** | 预约剩余时间 | `_appointment_remaining_time` | 预约启动剩余倒计时 (min) |
| **Sensor** | 当前蒸汽/湿度档位 | `_steam_gear` | 蒸烤箱当前运行的蒸汽/湿度档位（无 / 低档 / 中档 / 高档） |
| **Sensor** | 烹饪进度 | `_cooking_progress` | 根据总时长与剩余时长计算的实时烹饪进度 (%) |
| **Binary Sensor** | 炉门 | `_door` | 炉门开合状态 (`Door`) |
| **Binary Sensor** | 水箱异常/缺位 | `_cistern` | 水箱是否未放置到位/弹出 (`Cistern`) |
| **Binary Sensor** | 水箱缺水警报 | `_water_shortage` | 水箱水位过低警报 (`WaterShortage`) |
| **Switch** | 炉灯 | `_light` | 炉内照明灯开关 (`LightSwitch`) |
| **Switch** | 童锁 | `_child_lock` | 儿童安全锁开关 (`ChildLockSwitch`) |
| **Switch** | 一键排水 | `_draining` | 余水管路排水状态显示与开关 (`Draining`) |
| **Switch** | 强制抽水 | `_mandatory_pumping` | 强制抽水状态显示与开关 (`MandatoryPumping`) |
| **Select** | 预设烹饪模式 | `_mode_select` | 22 种烹饪预设模式下拉菜单 |
| **Select** | 蒸汽/湿度档位 | `_steam_gear_select` | 低档 (1档) / 中档 (2档) / 高档 (3档)（仅普通蒸、高温蒸、蒸汽烤可用） |
| **Number** | 上管/主腔设定温度 | `_number_target_temp` | 烹饪上部/主腔目标温度设定 (°C) |
| **Number** | 下管设定温度 | `_number_down_target_temp` | 烹饪下部目标温度设定（仅 9 种独立控温模式可用） |
| **Number** | 烹饪时长设定 | `_number_work_time` | 烹饪目标时长设定 (1 ~ 360 min) |
| **Number** | 预约延迟时间 | `_number_appointment_time` | 延迟启动时间设定 (0 ~ 1440 min，0 表示立即启动) |
| **Button** | 启动烹饪 | `_start` | 按当前选择的模式、温度、时长、档位及预约时间启动烹饪 |
| **Button** | 暂停/继续 | `_pause` | 暂停或恢复运行中的烹饪任务 (`PauseSwitch`) |
| **Button** | 停止烹饪 | `_stop` | 立即停止烹饪或取消预约并回到待机状态 (`StopWork=1`) |
| **Button** | 弹出水箱 | `_open_water_tank` | 电动弹出水箱 (`WaterMoto=1`) |

---

## 🥘 22 种内置烹饪模式参数表

| 模式名称 | `pattern_id` | 协议服务名 (Service) | 允许温区 (°C) | 默认温度 | 默认时长 | 上下独立控温 | 三档蒸汽/湿度 |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **普通蒸** | 3 | `OrdinarySteamed` | 30 ~ 100℃ | 100℃ | 30 min | ✕ | 蒸汽档 (默认 1 档) |
| **高温蒸** | 2 | `HighTemperatureSteam` | 90 ~ 120℃ | 120℃ | 30 min | ✕ | 蒸汽档 (默认 1 档) |
| **烘焙烤** | 7 | `BakedBaked` | 60 ~ 180℃ | 180℃ | 35 min | ✔️ | ✕ |
| **风扇烤** | 6 | `TheFanToBake` | 60 ~ 230℃ | 230℃ | 35 min | ✔️ | ✕ |
| **快烧烤** | 5 | `QuickBarbecue` | 60 ~ 200℃ | 200℃ | 30 min | ✔️ | ✕ |
| **加湿烤** | 1 | `HumidifyingRoast` | 60 ~ 220℃ | 200℃ | 30 min | ✔️ | ✕ |
| **慢烧烤** | 8 | `SlowBbarbecue` | 60 ~ 230℃ | 180℃ | 45 min | ✔️ | ✕ |
| **风焙烤** | 16 | `WindBaked` | 30 ~ 230℃ | 200℃ | 30 min | ✔️ | ✕ |
| **焙烤** | 17 | `RoasterBaked` | 30 ~ 230℃ | 180℃ | 30 min | ✔️ | ✕ |
| **煎烤** | 18 | `Decoct` | 60 ~ 140℃ | 140℃ | 30 min | ✔️ | ✕ |
| **空气炸** | 19 | `AirFry` | 30 ~ 230℃ | 200℃ | 30 min | ✔️ | ✕ |
| **串烤** | 31 | `Rotisserie` | 120 ~ 200℃ | 190℃ | 15 min | ✕ | ✕ |
| **蒸汽烤** | 20 | `SteamBaked` | 120 ~ 200℃ | 200℃ | 30 min | ✕ | 湿度档 (默认 3 档) |
| **炖煮** | 24 | `Stew` | 60 ~ 150℃ | 125℃ | 40 min | ✕ | ✕ |
| **蒸烤同烹** | 25 | `SteamRoast` | 120 ~ 200℃ | 200℃ | 30 min | ✕ | ✕ |
| **烘干** | 23 | `Drying` | 固定 150℃ | 150℃ | 10 min | ✕ | ✕ |
| **保洁** | 10 | `sterilization` | 80 ~ 120℃ | 100℃ | 60 min | ✕ | ✕ |
| **解冻** | 4 | `Thaw` | 固定 60℃ | 60℃ | 50 min | ✕ | ✕ |
| **发酵** | 9 | `fermentation` | 30 ~ 45℃ | 30℃ | 30 min | ✕ | ✕ |
| **保温** | 11 | `HeatPreservation` | 固定 50℃ | 50℃ | 60 min | ✕ | ✕ |
| **复热** | 21 | `Reheating` | 固定 100℃ | 100℃ | 10 min | ✕ | ✕ |
| **清洁** | 22 | `Clean` | 固定 80℃ | 80℃ | 5 min | ✕ | ✕ |

---

## ⚡ 自动化服务 (`depelec_oven.start_cooking`)

在自动化、脚本或快捷按钮中，无需多步设置实体，可直接一次调用启动或预约：

```yaml
action: depelec_oven.start_cooking
data:
  mode: "蒸汽烤"
  temperature: 200
  duration: 25
  steam_gear: 3
  appointment_time: 60  # 60 分钟后自动开始（0 为立即启动）
```

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

---

## 🤝 贡献与反馈

欢迎提交 Issue 和 Pull Request！
如果您有其他德普型号蒸烤箱（如 TD55、TD50、TE55 等）并完成测试，欢迎共享模式参数！

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
