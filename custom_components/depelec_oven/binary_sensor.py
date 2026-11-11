"""Binary sensor platform for Depelec TD55 Ultra Oven."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up binary sensors for Depelec Oven from YAML."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN].get("coordinator")
    if coordinator:
        async_add_entities([
            DepelecDoorBinarySensor(coordinator),
            DepelecCisternBinarySensor(coordinator),
            DepelecWaterShortageBinarySensor(coordinator),
        ])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for Depelec Oven from config entry."""
    coordinator: DepelecOvenCoordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities([
        DepelecDoorBinarySensor(coordinator),
        DepelecCisternBinarySensor(coordinator),
        DepelecWaterShortageBinarySensor(coordinator),
    ])


class DepelecBaseBinarySensor(CoordinatorEntity[DepelecOvenCoordinator], BinarySensorEntity):
    """Base binary sensor for Depelec Oven."""

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


class DepelecDoorBinarySensor(DepelecBaseBinarySensor):
    """Binary sensor for oven door open / closed."""

    _attr_translation_key = "oven_door"
    _attr_name = "炉门"
    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_door"

    @property
    def is_on(self) -> bool:
        """Return True if oven door is open (1 = open, 0 = closed)."""
        return bool(self.coordinator.data.get("Door", 0) == 1)


class DepelecCisternBinarySensor(DepelecBaseBinarySensor):
    """Binary sensor for water cistern presence."""

    _attr_translation_key = "oven_cistern"
    _attr_name = "水箱异常/缺位"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_cistern"

    @property
    def is_on(self) -> bool:
        """Return True if water cistern is missing/removed (1 = problem)."""
        return bool(self.coordinator.data.get("Cistern", 0) == 1)


class DepelecWaterShortageBinarySensor(DepelecBaseBinarySensor):
    """Binary sensor for water shortage alarm."""

    _attr_translation_key = "oven_water_shortage"
    _attr_name = "水箱缺水警报"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:water-alert"

    def __init__(self, coordinator: DepelecOvenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_name}_water_shortage"

    @property
    def is_on(self) -> bool:
        """Return True if water level is too low (1 = alert)."""
        return bool(self.coordinator.data.get("WaterShortage", 0) == 1)
