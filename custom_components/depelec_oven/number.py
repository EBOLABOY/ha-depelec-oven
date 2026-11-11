"""Number platform for Depelec TD55 Ultra Oven target temperature and duration."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
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
    """Set up number entities for Depelec Oven from YAML."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN].get("coordinator")
    if coordinator:
        async_add_entities([
            DepelecTargetTempNumber(coordinator),
            DepelecDownTargetTempNumber(coordinator),
            DepelecWorkTimeNumber(coordinator),
        ])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities for Depelec Oven."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities([
        DepelecTargetTempNumber(coordinator),
        DepelecDownTargetTempNumber(coordinator),
        DepelecWorkTimeNumber(coordinator),
    ])


class DepelecBaseNumber(CoordinatorEntity[DepelecOvenCoordinator], NumberEntity):
    """Base number entity for Depelec Oven."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(const.DOMAIN, coordinator.client.device_name)},
            name=const.DEFAULT_NAME,
            manufacturer="德普 (Depelec)",
            model="TD55 Ultra",
            sw_version="1.0.0",
        )


class DepelecTargetTempNumber(DepelecBaseNumber):
    """Adjust target temperature for upper zone / main chamber."""

    _attr_translation_key = "target_temp_number"
    _attr_name = "上管/主腔设定温度"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_step = 1.0
    _attr_icon = "mdi:thermometer-chevron-up"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_number_target_temp"

    @property
    def native_min_value(self) -> float:
        """Dynamic minimum temperature based on selected mode."""
        cfg = const.MODES.get(self.coordinator.selected_mode)
        return float(cfg["min_temp"] if cfg else 30)

    @property
    def native_max_value(self) -> float:
        """Dynamic maximum temperature based on selected mode."""
        cfg = const.MODES.get(self.coordinator.selected_mode)
        return float(cfg["max_temp"] if cfg else 230)

    @property
    def native_value(self) -> float:
        """Return the current target temperature setting."""
        return float(self.coordinator.target_temp)

    async def async_set_native_value(self, value: float) -> None:
        """Update target temperature."""
        self.coordinator.set_target_temp(int(value))
        self.async_write_ha_state()


class DepelecDownTargetTempNumber(DepelecBaseNumber):
    """Adjust target temperature for lower heating tube (for dual-tube modes)."""

    _attr_translation_key = "down_target_temp_number"
    _attr_name = "下管设定温度"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_step = 1.0
    _attr_icon = "mdi:thermometer-chevron-down"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_number_down_target_temp"

    @property
    def native_min_value(self) -> float:
        cfg = const.MODES.get(self.coordinator.selected_mode)
        return float(cfg["min_temp"] if cfg else 30)

    @property
    def native_max_value(self) -> float:
        cfg = const.MODES.get(self.coordinator.selected_mode)
        return float(cfg["max_temp"] if cfg else 230)

    @property
    def native_value(self) -> float:
        return float(self.coordinator.down_target_temp)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.set_down_target_temp(int(value))
        self.async_write_ha_state()


class DepelecWorkTimeNumber(DepelecBaseNumber):
    """Adjust cooking duration (minutes)."""

    _attr_translation_key = "work_time_number"
    _attr_name = "烹饪时长设定"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_step = 1.0
    _attr_native_min_value = 1.0
    _attr_native_max_value = 180.0
    _attr_icon = "mdi:clock-edit-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_number_work_time"

    @property
    def native_value(self) -> float:
        return float(self.coordinator.target_time)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.set_target_time(int(value))
        self.async_write_ha_state()
