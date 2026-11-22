"""Constants for the Depelec TD55 Ultra Oven integration."""
from __future__ import annotations

DOMAIN = "depelec_oven"
INTEGRATION_VERSION = "1.2.0"

# Device hardware & network defaults
DEFAULT_NAME = "德普 TD55 Ultra 蒸烤箱"
DEFAULT_HOST = "192.168.1.100"
DEFAULT_PORT = 5683
DEFAULT_PRODUCT_KEY = "a1Bq3pNE7Er"
DEFAULT_DEVICE_NAME = ""
DEFAULT_IOT_ID = ""
# Public mobile app credentials extracted from the official Depelec app
DEFAULT_APP_KEY = "28770785"
DEFAULT_APP_SECRET = "41fd4a1eb18fa7ace5e2abbbe3867f93"
DEFAULT_INITIAL_IOT_TOKEN = ""
DEFAULT_INITIAL_REFRESH_TOKEN = ""
DEFAULT_IDENTITY_ID = ""
DEFAULT_ALCS_ACCESS_KEY = ""
DEFAULT_ALCS_ACCESS_TOKEN = ""

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 15

# Connection modes
CONF_CONNECTION_MODE = "connection_mode"
CONNECTION_MODE_AUTO = "auto"
CONNECTION_MODE_LOCAL = "local"
CONNECTION_MODE_CLOUD = "cloud"
CONNECTION_MODES = (
    CONNECTION_MODE_AUTO,
    CONNECTION_MODE_LOCAL,
    CONNECTION_MODE_CLOUD,
)
DEFAULT_CONNECTION_MODE = CONNECTION_MODE_AUTO

# Configuration keys
CONF_PRODUCT_KEY = "product_key"
CONF_DEVICE_NAME = "device_name"
CONF_IOT_ID = "iot_id"
CONF_APP_KEY = "app_key"
CONF_APP_SECRET = "app_secret"
CONF_INITIAL_IOT_TOKEN = "initial_iot_token"
CONF_INITIAL_REFRESH_TOKEN = "initial_refresh_token"
CONF_IDENTITY_ID = "identity_id"
CONF_ALCS_ACCESS_KEY = "alcs_access_key"
CONF_ALCS_ACCESS_TOKEN = "alcs_access_token"

# Home Assistant service names
SERVICE_START_COOKING = "start_cooking"

# Duration limits (minutes)
MAX_WORK_TIME = 360
MAX_APPOINTMENT_TIME = 1440

# All 18 Alink Thing-Model properties reported by TD55 Ultra over local ALCS CoAP
OVEN_PROPERTIES: list[str] = [
    "CurrentTemperature",
    "DownCurrentTemperature",
    "ToastTemperature",
    "DownToastTemperature",
    "WorkTime",
    "RemainingWorkTime",
    "AppointmentTime",
    "AppointmentRemainingTime",
    "WorkState",
    "Mode",
    "SteamGear",
    "LightSwitch",
    "ChildLockSwitch",
    "Door",
    "Cistern",
    "WaterShortage",
    "Draining",
    "MandatoryPumping",
]

# Status mappings (bitmask / enum values verified from hardware & Pengke v2.8.2)
WORK_STATE_STANDBY = 1
WORK_STATE_APPOINTMENT = 2
WORK_STATE_PAUSED = 4
WORK_STATE_HEATING = 8
WORK_STATE_PREHEATING = 16
WORK_STATE_KEEP_WARM = 32
WORK_STATE_CLEANING = 64

WORK_STATES: dict[int, str] = {
    WORK_STATE_STANDBY: "待机",
    WORK_STATE_APPOINTMENT: "预约中",
    WORK_STATE_PAUSED: "已暂停",
    WORK_STATE_HEATING: "加热中",
    WORK_STATE_PREHEATING: "预热中",
    WORK_STATE_KEEP_WARM: "保温中",
    WORK_STATE_CLEANING: "清洗中",
}

ACTIVE_COOKING_STATES: tuple[int, ...] = (
    WORK_STATE_HEATING,
    WORK_STATE_PREHEATING,
    WORK_STATE_KEEP_WARM,
)

# 3-level Steam / Humidity Gear mappings (1=低, 2=中, 3=高)
STEAM_GEAR_LABELS: dict[int, str] = {
    0: "无",
    1: "低档 (1档)",
    2: "中档 (2档)",
    3: "高档 (3档)",
}

STEAM_GEAR_SELECT_OPTIONS: dict[str, int] = {
    "低档 (1档)": 1,
    "中档 (2档)": 2,
    "高档 (3档)": 3,
}

STEAM_GEAR_VALUE_TO_OPTION: dict[int, str] = {
    val: label for label, val in STEAM_GEAR_SELECT_OPTIONS.items()
}

# 22 Preset Cooking Modes for TD55 Ultra (Product ID: 96, Lot: a1Bq3pNE7Er)
# Service identifiers and parameter bounds verified against official TD55 Ultra
# product configuration API and Depelec Pengke App v2.8.2.
# Each entry contains:
#   id: pattern_id from official configuration
#   service: Alink LinkKit service identifier
#   min_temp / max_temp: allowed temperature range (°C)
#   default_temp: official default target temperature (°C)
#   default_time: official default duration (minutes)
#   temp_control: 1 if independent upper/lower temperature control is supported
#   fixed_temp: True if temperature is fixed
#   is_steam_gear / steam_gear_default: 3-level steam gear support (普通蒸/高温蒸)
#   is_humidity_gear / humidity_gear_default: 3-level humidity gear support (蒸汽烤)
MODES: dict[str, dict] = {
    "普通蒸": {
        "id": 3,
        "service": "OrdinarySteamed",
        "min_temp": 30,
        "max_temp": 100,
        "default_temp": 100,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 1,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "高温蒸": {
        "id": 2,
        "service": "HighTemperatureSteam",
        "min_temp": 90,
        "max_temp": 120,
        "default_temp": 120,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 1,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "烘焙烤": {
        "id": 7,
        "service": "BakedBaked",
        "min_temp": 60,
        "max_temp": 180,
        "default_temp": 180,
        "default_time": 35,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "风扇烤": {
        "id": 6,
        "service": "TheFanToBake",
        "min_temp": 60,
        "max_temp": 230,
        "default_temp": 230,
        "default_time": 35,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "快烧烤": {
        "id": 5,
        "service": "QuickBarbecue",
        "min_temp": 60,
        "max_temp": 200,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "加湿烤": {
        "id": 1,
        "service": "HumidifyingRoast",
        "min_temp": 60,
        "max_temp": 220,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "慢烧烤": {
        "id": 8,
        "service": "SlowBbarbecue",
        "min_temp": 60,
        "max_temp": 230,
        "default_temp": 180,
        "default_time": 45,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "风焙烤": {
        "id": 16,
        "service": "WindBaked",
        "min_temp": 30,
        "max_temp": 230,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "焙烤": {
        "id": 17,
        "service": "RoasterBaked",
        "min_temp": 30,
        "max_temp": 230,
        "default_temp": 180,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "煎烤": {
        "id": 18,
        "service": "Decoct",
        "min_temp": 60,
        "max_temp": 140,
        "default_temp": 140,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "空气炸": {
        "id": 19,
        "service": "AirFry",
        "min_temp": 30,
        "max_temp": 230,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "串烤": {
        "id": 31,
        "service": "Rotisserie",
        "min_temp": 120,
        "max_temp": 200,
        "default_temp": 190,
        "default_time": 15,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "蒸汽烤": {
        "id": 20,
        "service": "SteamBaked",
        "min_temp": 120,
        "max_temp": 200,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 1,
        "humidity_gear_default": 3,
    },
    "炖煮": {
        "id": 24,
        "service": "Stew",
        "min_temp": 60,
        "max_temp": 150,
        "default_temp": 125,
        "default_time": 40,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "蒸烤同烹": {
        "id": 25,
        "service": "SteamRoast",
        "min_temp": 120,
        "max_temp": 200,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "烘干": {
        "id": 23,
        "service": "Drying",
        "min_temp": 150,
        "max_temp": 150,
        "default_temp": 150,
        "default_time": 10,
        "temp_control": 0,
        "fixed_temp": True,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "保洁": {
        "id": 10,
        "service": "sterilization",
        "min_temp": 80,
        "max_temp": 120,
        "default_temp": 100,
        "default_time": 60,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "解冻": {
        "id": 4,
        "service": "Thaw",
        "min_temp": 60,
        "max_temp": 60,
        "default_temp": 60,
        "default_time": 50,
        "temp_control": 0,
        "fixed_temp": True,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "发酵": {
        "id": 9,
        "service": "fermentation",
        "min_temp": 30,
        "max_temp": 45,
        "default_temp": 30,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "保温": {
        "id": 11,
        "service": "HeatPreservation",
        "min_temp": 50,
        "max_temp": 50,
        "default_temp": 50,
        "default_time": 60,
        "temp_control": 0,
        "fixed_temp": True,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "复热": {
        "id": 21,
        "service": "Reheating",
        "min_temp": 100,
        "max_temp": 100,
        "default_temp": 100,
        "default_time": 10,
        "temp_control": 0,
        "fixed_temp": True,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
    "清洁": {
        "id": 22,
        "service": "Clean",
        "min_temp": 80,
        "max_temp": 80,
        "default_temp": 80,
        "default_time": 5,
        "temp_control": 0,
        "fixed_temp": True,
        "is_steam_gear": 0,
        "steam_gear_default": 1,
        "is_humidity_gear": 0,
        "humidity_gear_default": 3,
    },
}

# Reverse lookups
ID_TO_MODE_NAME = {v["id"]: k for k, v in MODES.items()}
SERVICE_TO_MODE_NAME = {v["service"]: k for k, v in MODES.items()}
