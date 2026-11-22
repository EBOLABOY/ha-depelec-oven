"""Button platform for Depelec TD55 Ultra Oven actions."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import const
from .coordinator import DepelecOvenCoordinator


def _build_entities(coordinator: DepelecOvenCoordinator) -> list[ButtonEntity]:
    return [
        DepelecStartButton(coordinator),
        DepelecPauseButton(coordinator),
        DepelecStopButton(coordinator),
    ]


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up button entities for Depelec Oven from YAML."""
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
    """Set up button entities for Depelec Oven."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities(_build_entities(coordinator))


class DepelecBaseButton(CoordinatorEntity[DepelecOvenCoordinator], ButtonEntity):
    """Base button for Depelec Oven."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(const.DOMAIN, coordinator.device_identifier)},
            name=const.DEFAULT_NAME,
            manufacturer="德普 (Depelec)",
            model="TD55 Ultra",
            sw_version="1.1.0",
        )


class DepelecStartButton(DepelecBaseButton):
    """Button to start cooking with current configured mode, temp and duration."""

    _attr_name = "启动烹饪"
    _attr_icon = "mdi:play-circle-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_start"

    async def async_press(self) -> None:
        """Trigger start cooking."""
        await self.coordinator.async_start_cooking()


class DepelecPauseButton(DepelecBaseButton):
    """Button to pause or resume current cooking program."""

    _attr_name = "暂停/继续"
    _attr_icon = "mdi:pause-circle-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_pause"

    async def async_press(self) -> None:
        """Toggle pause state."""
        await self.coordinator.async_pause_cooking()


class DepelecStopButton(DepelecBaseButton):
    """Button to immediately terminate cooking and return to standby."""

    _attr_name = "停止烹饪"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_stop"

    async def async_press(self) -> None:
        """Trigger stop cooking."""
        await self.coordinator.async_stop_cooking()
