"""Select platform for Depelec TD55 Ultra Oven cooking mode selection."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import const
from .coordinator import DepelecOvenCoordinator


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up select entities for Depelec Oven from YAML."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN].get("coordinator")
    if coordinator:
        async_add_entities([
            DepelecModeSelect(coordinator),
        ])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities for Depelec Oven."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities([
        DepelecModeSelect(coordinator),
    ])


class DepelecModeSelect(CoordinatorEntity[DepelecOvenCoordinator], SelectEntity):
    """Selector for all 22 preset cooking modes."""

    _attr_has_entity_name = True
    _attr_translation_key = "cooking_mode_select"
    _attr_name = "预设烹饪模式"
    _attr_icon = "mdi:format-list-bulleted-type"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_mode_select"
        self._attr_options = list(const.MODES.keys())
        self._attr_device_info = DeviceInfo(
            identifiers={(const.DOMAIN, coordinator.client.device_name)},
            name=const.DEFAULT_NAME,
            manufacturer="德普 (Depelec)",
            model="TD55 Ultra",
            sw_version="1.0.0",
        )

    @property
    def current_option(self) -> str:
        """Return the currently selected cooking mode."""
        return self.coordinator.selected_mode

    async def async_select_option(self, option: str) -> None:
        """Change the selected cooking mode and load recommended settings."""
        if option in const.MODES:
            self.coordinator.set_selected_mode(option)
            self.async_write_ha_state()
