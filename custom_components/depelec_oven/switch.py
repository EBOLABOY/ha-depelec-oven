"""Switch platform for Depelec TD55 Ultra Oven."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import const
from .coordinator import DepelecOvenCoordinator


def _build_entities(coordinator: DepelecOvenCoordinator) -> list[SwitchEntity]:
    return [
        DepelecLightSwitch(coordinator),
        DepelecChildLockSwitch(coordinator),
        DepelecDrainingSwitch(coordinator),
        DepelecMandatoryPumpingSwitch(coordinator),
    ]


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up switches for Depelec Oven from YAML."""
    coordinator: DepelecOvenCoordinator | None = hass.data[const.DOMAIN].get(
        "coordinator"
    )
    if coordinator:
        async_add_entities(_build_entities(coordinator))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches for Depelec Oven from config entry."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities(_build_entities(coordinator))


class DepelecBaseSwitch(CoordinatorEntity[DepelecOvenCoordinator], SwitchEntity):
    """Base switch for Depelec Oven."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        if coordinator.attach_device_info:
            self._attr_device_info = DeviceInfo(
                identifiers={(const.DOMAIN, coordinator.device_identifier)},
                name=const.DEFAULT_NAME,
                manufacturer="德普 (Depelec)",
                model="TD55 Ultra",
                sw_version=const.INTEGRATION_VERSION,
            )

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data or {}


class DepelecLightSwitch(DepelecBaseSwitch):
    """Switch to turn the oven chamber light on or off."""

    _attr_name = "炉灯"
    _attr_icon = "mdi:lightbulb-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_light"

    @property
    def is_on(self) -> bool | None:
        """Return True if chamber light is on."""
        val = self._data.get("LightSwitch")
        if val is None:
            return None
        return bool(val == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn chamber light on."""
        await self.coordinator.async_set_light(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn chamber light off."""
        await self.coordinator.async_set_light(False)


class DepelecChildLockSwitch(DepelecBaseSwitch):
    """Switch to engage or release the oven child lock."""

    _attr_name = "童锁"
    _attr_icon = "mdi:lock-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_child_lock"

    @property
    def is_on(self) -> bool | None:
        """Return True if child lock is engaged."""
        val = self._data.get("ChildLockSwitch")
        if val is None:
            return None
        return bool(val == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Engage child lock."""
        await self.coordinator.async_set_child_lock(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Release child lock."""
        await self.coordinator.async_set_child_lock(False)


class DepelecDrainingSwitch(DepelecBaseSwitch):
    """Switch reflecting and controlling residual water draining (Draining)."""

    _attr_name = "一键排水"
    _attr_icon = "mdi:water-minus-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_draining"

    @property
    def is_on(self) -> bool | None:
        """Return True if draining is active."""
        val = self._data.get("Draining")
        if val is None:
            return None
        return bool(val == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Trigger water-circuit draining."""
        await self.coordinator.async_set_draining(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop water-circuit draining."""
        await self.coordinator.async_set_draining(False)


class DepelecMandatoryPumpingSwitch(DepelecBaseSwitch):
    """Switch reflecting and controlling mandatory pumping (MandatoryPumping)."""

    _attr_name = "强制抽水"
    _attr_icon = "mdi:water-pump"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_mandatory_pumping"

    @property
    def is_on(self) -> bool | None:
        """Return True if mandatory pumping is active."""
        val = self._data.get("MandatoryPumping")
        if val is None:
            return None
        return bool(val == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Trigger mandatory water pumping."""
        await self.coordinator.async_set_mandatory_pumping(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop mandatory water pumping."""
        await self.coordinator.async_set_mandatory_pumping(False)
