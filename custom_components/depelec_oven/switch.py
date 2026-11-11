"""Switch platform for Depelec TD55 Ultra Oven."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import const
from .coordinator import DepelecOvenCoordinator


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up switches for Depelec Oven from YAML."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN].get("coordinator")
    if coordinator:
        async_add_entities([
            DepelecLightSwitch(coordinator),
            DepelecChildLockSwitch(coordinator),
        ])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches for Depelec Oven from config entry."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities([
        DepelecLightSwitch(coordinator),
        DepelecChildLockSwitch(coordinator),
    ])


class DepelecBaseSwitch(CoordinatorEntity[DepelecOvenCoordinator], SwitchEntity):
    """Base switch for Depelec Oven."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(const.DOMAIN, coordinator.client.device_name)},
            name=const.DEFAULT_NAME,
            manufacturer="德普 (Depelec)",
            model="TD55 Ultra",
            sw_version="1.0.0",
        )


class DepelecLightSwitch(DepelecBaseSwitch):
    """Switch to turn the oven chamber light on or off."""

    _attr_translation_key = "oven_light"
    _attr_name = "炉灯"
    _attr_icon = "mdi:lightbulb-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_light"

    @property
    def is_on(self) -> bool:
        """Return True if chamber light is on."""
        return bool(self.coordinator.data.get("LightSwitch", 0) == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn chamber light on."""
        await self.coordinator.async_set_light(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn chamber light off."""
        await self.coordinator.async_set_light(False)


class DepelecChildLockSwitch(DepelecBaseSwitch):
    """Switch to engage or release the oven child lock."""

    _attr_translation_key = "oven_child_lock"
    _attr_name = "童锁"
    _attr_icon = "mdi:lock-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_child_lock"

    @property
    def is_on(self) -> bool:
        """Return True if child lock is engaged."""
        return bool(self.coordinator.data.get("ChildLockSwitch", 0) == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Engage child lock."""
        await self.coordinator.async_set_child_lock(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Release child lock."""
        await self.coordinator.async_set_child_lock(False)
