"""Sensor platform for Depelec TD55 Ultra Oven."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
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
    """Set up sensors for Depelec Oven from YAML."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN].get("coordinator")
    if coordinator:
        async_add_entities([
            DepelecCurrentTempSensor(coordinator),
            DepelecDownCurrentTempSensor(coordinator),
            DepelecTargetTempSensor(coordinator),
            DepelecDownTargetTempSensor(coordinator),
            DepelecRemainingTimeSensor(coordinator),
            DepelecTotalTimeSensor(coordinator),
            DepelecWorkStateSensor(coordinator),
            DepelecCurrentModeSensor(coordinator),
        ])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for Depelec Oven from config entry."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities([
        DepelecCurrentTempSensor(coordinator),
        DepelecDownCurrentTempSensor(coordinator),
        DepelecTargetTempSensor(coordinator),
        DepelecDownTargetTempSensor(coordinator),
        DepelecRemainingTimeSensor(coordinator),
        DepelecTotalTimeSensor(coordinator),
        DepelecWorkStateSensor(coordinator),
        DepelecCurrentModeSensor(coordinator),
    ])


class DepelecBaseSensor(CoordinatorEntity[DepelecOvenCoordinator], SensorEntity):
    """Base sensor for Depelec Oven."""

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


class DepelecCurrentTempSensor(DepelecBaseSensor):
    """Sensor for chamber current temperature."""

    _attr_translation_key = "current_temperature"
    _attr_name = "上腔实时温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_current_temp"

    @property
    def native_value(self) -> int | None:
        """Return the current temperature."""
        return self.coordinator.data.get("CurrentTemperature")


class DepelecDownCurrentTempSensor(DepelecBaseSensor):
    """Sensor for lower zone current temperature."""

    _attr_translation_key = "down_current_temperature"
    _attr_name = "下腔实时温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_down_current_temp"

    @property
    def native_value(self) -> int | None:
        """Return lower current temperature."""
        return self.coordinator.data.get("DownCurrentTemperature")


class DepelecTargetTempSensor(DepelecBaseSensor):
    """Sensor for target temperature."""

    _attr_translation_key = "target_temperature"
    _attr_name = "上管设定温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_target_temp"

    @property
    def native_value(self) -> int | None:
        """Return target temperature."""
        return self.coordinator.data.get("ToastTemperature")


class DepelecDownTargetTempSensor(DepelecBaseSensor):
    """Sensor for lower zone target temperature."""

    _attr_translation_key = "down_target_temperature"
    _attr_name = "下管设定温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_down_target_temp"

    @property
    def native_value(self) -> int | None:
        """Return lower target temperature."""
        return self.coordinator.data.get("DownToastTemperature")


class DepelecRemainingTimeSensor(DepelecBaseSensor):
    """Sensor for remaining cooking time."""

    _attr_translation_key = "remaining_work_time"
    _attr_name = "剩余烹饪时间"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_remaining_time"

    @property
    def native_value(self) -> int | None:
        """Return remaining time in minutes."""
        return self.coordinator.data.get("RemainingWorkTime")


class DepelecTotalTimeSensor(DepelecBaseSensor):
    """Sensor for total cooking duration."""

    _attr_translation_key = "total_work_time"
    _attr_name = "总设定时间"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_total_time"

    @property
    def native_value(self) -> int | None:
        """Return total duration in minutes."""
        return self.coordinator.data.get("WorkTime")


class DepelecWorkStateSensor(DepelecBaseSensor):
    """Sensor for current oven operating state."""

    _attr_translation_key = "work_state"
    _attr_name = "工作状态"
    _attr_icon = "mdi:microwave"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_work_state"

    @property
    def native_value(self) -> str:
        """Return human-readable work state."""
        state_code = self.coordinator.data.get("WorkState", 1)
        return const.WORK_STATES.get(state_code, f"未知({state_code})")


class DepelecCurrentModeSensor(DepelecBaseSensor):
    """Sensor for active cooking mode name."""

    _attr_translation_key = "current_mode"
    _attr_name = "当前烹饪模式"
    _attr_icon = "mdi:chef-hat"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_current_mode"

    @property
    def native_value(self) -> str:
        """Return current mode name."""
        mode_id = self.coordinator.data.get("Mode", 0)
        return const.ID_TO_MODE_NAME.get(mode_id, "无" if mode_id == 0 else f"模式{mode_id}")
