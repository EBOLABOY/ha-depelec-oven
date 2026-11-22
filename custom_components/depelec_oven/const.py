"""Constants for the Depelec TD55 Ultra Oven integration."""
from __future__ import annotations

DOMAIN = "depelec_oven"

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

# Known Alink Thing-Model properties queried over local ALCS CoAP
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
    "LightSwitch",
    "ChildLockSwitch",
    "Door",
    "Cistern",
    "WaterShortage",
]

# Status mappings
WORK_STATE_STANDBY = 1
WORK_STATE_APPOINTMENT = 2
WORK_STATE_PAUSED = 4
WORK_STATE_HEATING = 8

WORK_STATES: dict[int, str] = {
    1: "待机",
    2: "预约中",
    4: "已暂停",
    8: "加热中",
}

# 22 Preset Cooking Modes for TD55 Ultra (Product ID: 96, Lot: 22192528)
# Each entry contains:
# id: pattern_id from official configuration
# service: LinkKit service identifier
# min_temp: minimum allowed temperature (°C)
# max_temp: maximum allowed temperature (°C)
# default_temp: default target temperature (°C)
# default_time: default duration (minutes)
# temp_control: 1 if independent upper/lower temperature control is supported, else 0
# fixed_temp: True if temperature is fixed
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
    },
    "高温蒸": {
        "id": 2,
        "service": "HighTemperatureSteam",
        "min_temp": 90,
        "max_temp": 120,
        "default_temp": 110,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
    },
    "烘焙烤": {
        "id": 7,
        "service": "Bake",
        "min_temp": 60,
        "max_temp": 180,
        "default_temp": 180,
        "default_time": 35,
        "temp_control": 1,
        "fixed_temp": False,
    },
    "风扇烤": {
        "id": 6,
        "service": "FanBake",
        "min_temp": 60,
        "max_temp": 230,
        "default_temp": 230,
        "default_time": 35,
        "temp_control": 1,
        "fixed_temp": False,
    },
    "快烧烤": {
        "id": 5,
        "service": "FastRoast",
        "min_temp": 60,
        "max_temp": 200,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
    },
    "加湿烤": {
        "id": 1,
        "service": "HumidBake",
        "min_temp": 60,
        "max_temp": 220,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 1,
        "fixed_temp": False,
    },
    "慢烧烤": {
        "id": 8,
        "service": "SlowRoast",
        "min_temp": 60,
        "max_temp": 230,
        "default_temp": 180,
        "default_time": 45,
        "temp_control": 1,
        "fixed_temp": False,
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
    },
    "空气炸": {
        "id": 19,
        "service": "AirFry",
        "min_temp": 30,
        "max_temp": 230,
        "default_temp": 200,
        "default_time": 25,
        "temp_control": 1,
        "fixed_temp": False,
    },
    "串烤": {
        "id": 31,
        "service": "RoastSkewer",
        "min_temp": 120,
        "max_temp": 200,
        "default_temp": 190,
        "default_time": 15,
        "temp_control": 0,
        "fixed_temp": False,
    },
    "蒸汽烤": {
        "id": 20,
        "service": "SteamRoast",
        "min_temp": 120,
        "max_temp": 200,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
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
    },
    "蒸烤同烹": {
        "id": 25,
        "service": "SteamBakeTogether",
        "min_temp": 120,
        "max_temp": 200,
        "default_temp": 200,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
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
    },
    "保洁": {
        "id": 10,
        "service": "Sanitize",
        "min_temp": 80,
        "max_temp": 120,
        "default_temp": 100,
        "default_time": 60,
        "temp_control": 0,
        "fixed_temp": False,
    },
    "解冻": {
        "id": 4,
        "service": "Defrost",
        "min_temp": 60,
        "max_temp": 60,
        "default_temp": 60,
        "default_time": 50,
        "temp_control": 0,
        "fixed_temp": True,
    },
    "发酵": {
        "id": 9,
        "service": "Ferment",
        "min_temp": 30,
        "max_temp": 45,
        "default_temp": 30,
        "default_time": 30,
        "temp_control": 0,
        "fixed_temp": False,
    },
    "保温": {
        "id": 11,
        "service": "KeepWarm",
        "min_temp": 50,
        "max_temp": 50,
        "default_temp": 50,
        "default_time": 60,
        "temp_control": 0,
        "fixed_temp": True,
    },
    "复热": {
        "id": 21,
        "service": "Reheat",
        "min_temp": 100,
        "max_temp": 100,
        "default_temp": 100,
        "default_time": 10,
        "temp_control": 0,
        "fixed_temp": True,
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
    },
}

# Reverse lookup by mode ID
ID_TO_MODE_NAME = {v["id"]: k for k, v in MODES.items()}
SERVICE_TO_MODE_NAME = {v["service"]: k for k, v in MODES.items()}
