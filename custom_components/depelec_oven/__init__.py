"""The Depelec TD55 Ultra Oven integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

from . import const
from .coordinator import DepelecOvenCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Depelec Oven component from YAML configuration."""
    hass.data.setdefault(const.DOMAIN, {})

    if const.DOMAIN not in config:
        return True

    conf = config[const.DOMAIN]
    host = conf.get(const.CONF_HOST, const.DEFAULT_HOST)
    port = conf.get(const.CONF_PORT, const.DEFAULT_PORT)
    scan_interval = conf.get(const.CONF_SCAN_INTERVAL, const.DEFAULT_SCAN_INTERVAL)
    iot_id = conf.get(const.CONF_IOT_ID, const.DEFAULT_IOT_ID)
    device_name = conf.get(const.CONF_DEVICE_NAME, const.DEFAULT_DEVICE_NAME)
    product_key = conf.get(const.CONF_PRODUCT_KEY, const.DEFAULT_PRODUCT_KEY)
    app_key = conf.get(const.CONF_APP_KEY, const.DEFAULT_APP_KEY)
    app_secret = conf.get(const.CONF_APP_SECRET, const.DEFAULT_APP_SECRET)
    identity_id = conf.get(const.CONF_IDENTITY_ID, const.DEFAULT_IDENTITY_ID)
    initial_iot_token = conf.get(const.CONF_INITIAL_IOT_TOKEN, const.DEFAULT_INITIAL_IOT_TOKEN)
    initial_refresh_token = conf.get(const.CONF_INITIAL_REFRESH_TOKEN, const.DEFAULT_INITIAL_REFRESH_TOKEN)

    coordinator = DepelecOvenCoordinator(
        hass,
        host=host,
        port=port,
        scan_interval=scan_interval,
        iot_id=iot_id,
        device_name=device_name,
        product_key=product_key,
        app_key=app_key,
        app_secret=app_secret,
        identity_id=identity_id,
        initial_iot_token=initial_iot_token,
        initial_refresh_token=initial_refresh_token,
    )

    await coordinator.async_refresh()

    # Store coordinator by default key
    hass.data[const.DOMAIN]["coordinator"] = coordinator
    hass.data[const.DOMAIN]["default"] = coordinator

    # Forward setup to platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            async_load_platform(
                hass, platform, const.DOMAIN, {}, config
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Depelec Oven from a config entry."""
    hass.data.setdefault(const.DOMAIN, {})

    host = entry.data.get(const.CONF_HOST, const.DEFAULT_HOST)
    port = entry.data.get(const.CONF_PORT, const.DEFAULT_PORT)
    scan_interval = entry.data.get(const.CONF_SCAN_INTERVAL, const.DEFAULT_SCAN_INTERVAL)
    iot_id = entry.data.get(const.CONF_IOT_ID, const.DEFAULT_IOT_ID)
    device_name = entry.data.get(const.CONF_DEVICE_NAME, const.DEFAULT_DEVICE_NAME)
    product_key = entry.data.get(const.CONF_PRODUCT_KEY, const.DEFAULT_PRODUCT_KEY)
    app_key = entry.data.get(const.CONF_APP_KEY, const.DEFAULT_APP_KEY)
    app_secret = entry.data.get(const.CONF_APP_SECRET, const.DEFAULT_APP_SECRET)
    identity_id = entry.data.get(const.CONF_IDENTITY_ID, const.DEFAULT_IDENTITY_ID)
    initial_iot_token = entry.data.get(const.CONF_INITIAL_IOT_TOKEN, const.DEFAULT_INITIAL_IOT_TOKEN)
    initial_refresh_token = entry.data.get(const.CONF_INITIAL_REFRESH_TOKEN, const.DEFAULT_INITIAL_REFRESH_TOKEN)

    coordinator = DepelecOvenCoordinator(
        hass,
        host=host,
        port=port,
        scan_interval=scan_interval,
        iot_id=iot_id,
        device_name=device_name,
        product_key=product_key,
        app_key=app_key,
        app_secret=app_secret,
        identity_id=identity_id,
        initial_iot_token=initial_iot_token,
        initial_refresh_token=initial_refresh_token,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[const.DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[const.DOMAIN].pop(entry.entry_id, None)

    return unload_ok
