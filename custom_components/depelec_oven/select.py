"""Select platform for Depelec TD55 Ultra Oven cooking mode & steam/humidity gear."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import const
from .coordinator import DepelecOvenCoordinator


def _build_entities(coordinator: DepelecOvenCoordinator) -> list[SelectEntity]:
    return [
        DepelecModeSelect(coordinator),
        DepelecSteamGearSelect(coordinator),
    ]


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up select entities for Depelec Oven from YAML."""
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
    """Set up select entities for Depelec Oven."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities(_build_entities(coordinator))


class DepelecBaseSelect(CoordinatorEntity[DepelecOvenCoordinator], SelectEntity):
    """Base select entity for Depelec Oven."""

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


class DepelecModeSelect(DepelecBaseSelect):
    """Selector for all 22 preset cooking modes."""

    _attr_name = "预设烹饪模式"
    _attr_icon = "mdi:format-list-bulleted-type"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_mode_select"
        self._attr_options = list(const.MODES.keys())

    @property
    def current_option(self) -> str:
        """Return the currently selected cooking mode."""
        return self.coordinator.selected_mode

    async def async_select_option(self, option: str) -> None:
        """Change the selected cooking mode and load recommended settings."""
        if option in const.MODES:
            self.coordinator.set_selected_mode(option)


class DepelecSteamGearSelect(DepelecBaseSelect):
    """Selector for 3-level steam / humidity gear (普通蒸、高温蒸、蒸汽烤)."""

    _attr_name = "蒸汽/湿度档位"
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_steam_gear_select"
        self._attr_options = list(const.STEAM_GEAR_SELECT_OPTIONS.keys())

    @property
    def available(self) -> bool:
        """Only available when the selected mode supports steam or humidity gear."""
        cfg = const.MODES.get(self.coordinator.selected_mode)
        return super().available and self.coordinator.mode_supports_gear(cfg)

    @property
    def current_option(self) -> str:
        """Return the currently selected steam/humidity gear option."""
        return const.STEAM_GEAR_VALUE_TO_OPTION.get(
            self.coordinator.steam_gear, "低档 (1档)"
        )

    async def async_select_option(self, option: str) -> None:
        """Update selected steam/humidity gear."""
        gear = const.STEAM_GEAR_SELECT_OPTIONS.get(option)
        if gear is not None:
            self.coordinator.set_steam_gear(gear)
