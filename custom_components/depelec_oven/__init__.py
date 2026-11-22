"""The Depelec TD55 Ultra Oven integration."""
from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
import homeassistant.helpers.config_validation as cv
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

OVEN_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(const.CONF_HOST, default=const.DEFAULT_HOST): cv.string,
        vol.Optional(const.CONF_PORT, default=const.DEFAULT_PORT): cv.port,
        vol.Optional(
            const.CONF_SCAN_INTERVAL, default=const.DEFAULT_SCAN_INTERVAL
        ): cv.positive_int,
        vol.Optional(
            const.CONF_CONNECTION_MODE, default=const.DEFAULT_CONNECTION_MODE
        ): vol.In(const.CONNECTION_MODES),
        vol.Optional(const.CONF_IOT_ID, default=const.DEFAULT_IOT_ID): cv.string,
        vol.Optional(
            const.CONF_DEVICE_NAME, default=const.DEFAULT_DEVICE_NAME
        ): cv.string,
        vol.Optional(
            const.CONF_PRODUCT_KEY, default=const.DEFAULT_PRODUCT_KEY
        ): cv.string,
        vol.Optional(const.CONF_APP_KEY, default=const.DEFAULT_APP_KEY): cv.string,
        vol.Optional(
            const.CONF_APP_SECRET, default=const.DEFAULT_APP_SECRET
        ): cv.string,
        vol.Optional(
            const.CONF_IDENTITY_ID, default=const.DEFAULT_IDENTITY_ID
        ): cv.string,
        vol.Optional(
            const.CONF_INITIAL_IOT_TOKEN, default=const.DEFAULT_INITIAL_IOT_TOKEN
        ): cv.string,
        vol.Optional(
            const.CONF_INITIAL_REFRESH_TOKEN,
            default=const.DEFAULT_INITIAL_REFRESH_TOKEN,
        ): cv.string,
        vol.Optional(
            const.CONF_ALCS_ACCESS_KEY, default=const.DEFAULT_ALCS_ACCESS_KEY
        ): cv.string,
        vol.Optional(
            const.CONF_ALCS_ACCESS_TOKEN, default=const.DEFAULT_ALCS_ACCESS_TOKEN
        ): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(const.DOMAIN): OVEN_CONFIG_SCHEMA},
    extra=vol.ALLOW_EXTRA,
)


def _create_coordinator(
    hass: HomeAssistant, conf: dict
) -> DepelecOvenCoordinator:
    return DepelecOvenCoordinator(
        hass,
        host=conf.get(const.CONF_HOST, const.DEFAULT_HOST),
        port=conf.get(const.CONF_PORT, const.DEFAULT_PORT),
        scan_interval=conf.get(const.CONF_SCAN_INTERVAL, const.DEFAULT_SCAN_INTERVAL),
        connection_mode=conf.get(
            const.CONF_CONNECTION_MODE, const.DEFAULT_CONNECTION_MODE
        ),
        iot_id=conf.get(const.CONF_IOT_ID, const.DEFAULT_IOT_ID),
        device_name=conf.get(const.CONF_DEVICE_NAME, const.DEFAULT_DEVICE_NAME),
        product_key=conf.get(const.CONF_PRODUCT_KEY, const.DEFAULT_PRODUCT_KEY),
        app_key=conf.get(const.CONF_APP_KEY, const.DEFAULT_APP_KEY),
        app_secret=conf.get(const.CONF_APP_SECRET, const.DEFAULT_APP_SECRET),
        identity_id=conf.get(const.CONF_IDENTITY_ID, const.DEFAULT_IDENTITY_ID),
        initial_iot_token=conf.get(
            const.CONF_INITIAL_IOT_TOKEN, const.DEFAULT_INITIAL_IOT_TOKEN
        ),
        initial_refresh_token=conf.get(
            const.CONF_INITIAL_REFRESH_TOKEN, const.DEFAULT_INITIAL_REFRESH_TOKEN
        ),
        alcs_access_key=conf.get(
            const.CONF_ALCS_ACCESS_KEY, const.DEFAULT_ALCS_ACCESS_KEY
        ),
        alcs_access_token=conf.get(
            const.CONF_ALCS_ACCESS_TOKEN, const.DEFAULT_ALCS_ACCESS_TOKEN
        ),
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Depelec Oven component from YAML configuration."""
    hass.data.setdefault(const.DOMAIN, {})

    if const.DOMAIN not in config:
        return True

    conf = config[const.DOMAIN]
    coordinator = _create_coordinator(hass, conf)
    await coordinator.async_initialize()
    await coordinator.async_refresh()

    hass.data[const.DOMAIN]["coordinator"] = coordinator
    hass.data[const.DOMAIN]["default"] = coordinator

    async def _async_stop(_event: Event) -> None:
        await coordinator.async_shutdown()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)

    await asyncio.gather(
        *(
            async_load_platform(hass, platform, const.DOMAIN, {}, config)
            for platform in PLATFORMS
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Depelec Oven from a config entry."""
    hass.data.setdefault(const.DOMAIN, {})

    coordinator = _create_coordinator(hass, dict(entry.data))
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()

    hass.data[const.DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: DepelecOvenCoordinator | None = hass.data[const.DOMAIN].pop(
            entry.entry_id, None
        )
        if coordinator is not None:
            await coordinator.async_shutdown()

    return unload_ok
