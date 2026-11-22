"""Sensor platform for Depelec TD55 Ultra Oven."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import const
from .coordinator import DepelecOvenCoordinator


def _build_entities(coordinator: DepelecOvenCoordinator) -> list[SensorEntity]:
    return [
        DepelecCurrentTempSensor(coordinator),
        DepelecDownCurrentTempSensor(coordinator),
        DepelecTargetTempSensor(coordinator),
        DepelecDownTargetTempSensor(coordinator),
        DepelecRemainingTimeSensor(coordinator),
        DepelecTotalTimeSensor(coordinator),
        DepelecWorkStateSensor(coordinator),
        DepelecCurrentModeSensor(coordinator),
        DepelecAppointmentTimeSensor(coordinator),
        DepelecAppointmentRemainingTimeSensor(coordinator),
        DepelecSteamGearSensor(coordinator),
        DepelecCookingProgressSensor(coordinator),
    ]


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up sensors for Depelec Oven from YAML."""
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
    """Set up sensors for Depelec Oven from config entry."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities(_build_entities(coordinator))


class DepelecBaseSensor(CoordinatorEntity[DepelecOvenCoordinator], SensorEntity):
    """Base sensor for Depelec Oven."""

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


class DepelecCurrentTempSensor(DepelecBaseSensor):
    """Sensor for chamber current temperature."""

    _attr_name = "上腔实时温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_current_temp"

    @property
    def native_value(self) -> int | None:
        """Return the current temperature."""
        return self._data.get("CurrentTemperature")


class DepelecDownCurrentTempSensor(DepelecBaseSensor):
    """Sensor for lower zone current temperature."""

    _attr_name = "下腔实时温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_down_current_temp"

    @property
    def native_value(self) -> int | None:
        """Return lower current temperature."""
        return self._data.get("DownCurrentTemperature")


class DepelecTargetTempSensor(DepelecBaseSensor):
    """Sensor for target temperature."""

    _attr_name = "上管设定温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_target_temp"

    @property
    def native_value(self) -> int | None:
        """Return target temperature."""
        return self._data.get("ToastTemperature")


class DepelecDownTargetTempSensor(DepelecBaseSensor):
    """Sensor for lower zone target temperature."""

    _attr_name = "下管设定温度"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_down_target_temp"

    @property
    def native_value(self) -> int | None:
        """Return lower target temperature."""
        return self._data.get("DownToastTemperature")


class DepelecRemainingTimeSensor(DepelecBaseSensor):
    """Sensor for remaining cooking time."""

    _attr_name = "剩余烹饪时间"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_remaining_time"

    @property
    def native_value(self) -> int | None:
        """Return remaining time in minutes."""
        return self._data.get("RemainingWorkTime")


class DepelecTotalTimeSensor(DepelecBaseSensor):
    """Sensor for total cooking duration."""

    _attr_name = "总设定时间"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_total_time"

    @property
    def native_value(self) -> int | None:
        """Return total duration in minutes."""
        return self._data.get("WorkTime")


class DepelecWorkStateSensor(DepelecBaseSensor):
    """Sensor for current oven operating state."""

    _attr_name = "工作状态"
    _attr_icon = "mdi:microwave"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_work_state"

    @property
    def native_value(self) -> str | None:
        """Return human-readable work state."""
        state_code = self._data.get("WorkState")
        if state_code is None:
            return None
        return const.WORK_STATES.get(state_code, f"未知({state_code})")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose active transport and raw codes for diagnostics."""
        return {
            "transport": self.coordinator.active_transport,
            "connection_mode": self.coordinator.connection_mode,
            "work_state_code": self._data.get("WorkState"),
            "mode_id": self._data.get("Mode"),
        }


class DepelecCurrentModeSensor(DepelecBaseSensor):
    """Sensor for active cooking mode name."""

    _attr_name = "当前烹饪模式"
    _attr_icon = "mdi:chef-hat"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_current_mode"

    @property
    def native_value(self) -> str | None:
        """Return current mode name."""
        mode_id = self._data.get("Mode")
        if mode_id is None:
            return None
        return const.ID_TO_MODE_NAME.get(
            mode_id, "无" if mode_id == 0 else f"模式{mode_id}"
        )


class DepelecAppointmentTimeSensor(DepelecBaseSensor):
    """Sensor for configured appointment delay time."""

    _attr_name = "预约设定时间"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_appointment_time"

    @property
    def native_value(self) -> int | None:
        """Return configured appointment duration in minutes."""
        return self._data.get("AppointmentTime")


class DepelecAppointmentRemainingTimeSensor(DepelecBaseSensor):
    """Sensor for remaining appointment countdown time."""

    _attr_name = "预约剩余时间"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-play-outline"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.device_identifier}_appointment_remaining_time"
        )

    @property
    def native_value(self) -> int | None:
        """Return remaining appointment countdown in minutes."""
        return self._data.get("AppointmentRemainingTime")


class DepelecSteamGearSensor(DepelecBaseSensor):
    """Sensor for active steam / humidity gear reported by the oven."""

    _attr_name = "当前蒸汽/湿度档位"
    _attr_icon = "mdi:weather-fog"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_steam_gear"

    @property
    def native_value(self) -> str | None:
        """Return human-readable steam/humidity gear."""
        gear = self._data.get("SteamGear")
        if gear is None:
            return None
        return const.STEAM_GEAR_LABELS.get(gear, f"{gear}档")


class DepelecCookingProgressSensor(DepelecBaseSensor):
    """Sensor for calculated cooking progress percentage."""

    _attr_name = "烹饪进度"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:progress-clock"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_identifier}_cooking_progress"

    @property
    def native_value(self) -> int:
        """Return cooking progress from 0 to 100%."""
        state_code = self._data.get("WorkState", const.WORK_STATE_STANDBY)
        total = self._data.get("WorkTime") or 0
        remaining = self._data.get("RemainingWorkTime") or 0
        if (
            state_code in (const.WORK_STATE_STANDBY, const.WORK_STATE_APPOINTMENT)
            or total <= 0
        ):
            return 0
        elapsed = max(0, min(total, total - remaining))
        return round(elapsed * 100 / total)
