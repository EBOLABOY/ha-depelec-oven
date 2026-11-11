"""DataUpdateCoordinator for Depelec TD55 Ultra Oven."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import const
from .cloud_client import DepelecCloudClient

_LOGGER = logging.getLogger(__name__)


class DepelecOvenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage polling and commands for Depelec Oven."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
        scan_interval: int = const.DEFAULT_SCAN_INTERVAL,
        iot_id: str = const.DEFAULT_IOT_ID,
        device_name: str = const.DEFAULT_DEVICE_NAME,
        product_key: str = const.DEFAULT_PRODUCT_KEY,
        app_key: str = const.DEFAULT_APP_KEY,
        app_secret: str = const.DEFAULT_APP_SECRET,
        identity_id: str = const.DEFAULT_IDENTITY_ID,
        initial_iot_token: str = const.DEFAULT_INITIAL_IOT_TOKEN,
        initial_refresh_token: str = const.DEFAULT_INITIAL_REFRESH_TOKEN,
    ) -> None:
        """Initialize the oven coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=const.DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.port = port
        try:
            from homeassistant.helpers.aiohttp_client import async_get_clientsession
            client_session = async_get_clientsession(hass)
        except Exception:
            client_session = None
        self.client = DepelecCloudClient(
            session=client_session,
            iot_id=iot_id,
            app_key=app_key,
            app_secret=app_secret,
            initial_iot_token=initial_iot_token,
            initial_refresh_token=initial_refresh_token,
            identity_id=identity_id,
            product_key=product_key,
            device_name=device_name,
        )

        # UI state helpers for pre-start configuration
        default_mode_name = "普通蒸"
        default_cfg = const.MODES[default_mode_name]
        self.selected_mode: str = default_mode_name
        self.target_temp: int = default_cfg["default_temp"]
        self.down_target_temp: int = default_cfg["default_temp"]
        self.target_time: int = default_cfg["default_time"]

        # In-memory shadow state
        self._state_data: dict[str, Any] = {
            "CurrentTemperature": 0,
            "DownCurrentTemperature": 0,
            "ToastTemperature": 0,
            "DownToastTemperature": 0,
            "WorkTime": 0,
            "RemainingWorkTime": 0,
            "AppointmentTime": 0,
            "AppointmentRemainingTime": 0,
            "WorkState": const.WORK_STATE_STANDBY,
            "PowerSwitch": 0,
            "LightSwitch": 0,
            "WaterTankState": 0,
            "DoorState": 0,
            "OvenMode": default_cfg["id"],
        }


    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest telemetry from oven."""
        try:
            props = await self.client.async_get_properties()
            if props:
                for k, v in props.items():
                    if isinstance(v, dict) and "value" in v:
                        self._state_data[k] = v["value"]
                    else:
                        self._state_data[k] = v
        except Exception as err:
            _LOGGER.debug("Oven polling error: %s", err)

        return self._state_data

    # -----------------------------------------------------------------------
    # Device Control Actions
    # -----------------------------------------------------------------------

    async def async_set_light(self, state: bool) -> None:
        """Toggle chamber light."""
        val = 1 if state else 0
        self._state_data["LightSwitch"] = val
        self.async_set_updated_data(self._state_data)
        await self.client.async_set_property("LightSwitch", val)

    async def async_set_child_lock(self, state: bool) -> None:
        """Toggle child safety lock."""
        val = 1 if state else 0
        self._state_data["ChildLockSwitch"] = val
        self.async_set_updated_data(self._state_data)
        await self.client.async_set_property("ChildLockSwitch", val)

    def set_selected_mode(self, mode_name: str) -> None:
        """Update selected cooking mode in UI and set default temp and time."""
        if mode_name not in const.MODES:
            return
        cfg = const.MODES[mode_name]
        self.selected_mode = mode_name
        self.target_temp = cfg["default_temp"]
        self.down_target_temp = cfg["default_temp"]
        self.target_time = cfg["default_time"]
        self.async_set_updated_data(self._state_data)

    def set_target_temp(self, temp: int) -> None:
        """Update UI target temperature."""
        self.target_temp = temp
        self.async_set_updated_data(self._state_data)

    def set_down_target_temp(self, temp: int) -> None:
        """Update UI lower-tube target temperature."""
        self.down_target_temp = temp
        self.async_set_updated_data(self._state_data)

    def set_target_time(self, mins: int) -> None:
        """Update UI target cooking duration."""
        self.target_time = mins
        self.async_set_updated_data(self._state_data)

    async def async_start_cooking(self) -> None:
        """Start cooking using current selected mode, temp and duration."""
        cfg = const.MODES.get(self.selected_mode)
        if not cfg:
            return

        identifier = cfg["service"]
        args: dict[str, Any] = {
            "ToastTemperature": int(self.target_temp),
            "WorkTime": int(self.target_time),
            "WorkSwitch": 1,
            "AppointmentTime": 0,
        }
        if cfg["temp_control"] == 1:
            args["DownToastTemperature"] = int(self.down_target_temp)

        _LOGGER.info("Starting oven mode: %s (%s) with %s", self.selected_mode, identifier, args)
        self._state_data["WorkState"] = const.WORK_STATE_HEATING
        self._state_data["Mode"] = cfg["id"]
        self._state_data["ToastTemperature"] = self.target_temp
        self._state_data["WorkTime"] = self.target_time
        self._state_data["RemainingWorkTime"] = self.target_time
        self.async_set_updated_data(self._state_data)

        await self.client.async_invoke_service(identifier, args)

    async def async_pause_cooking(self) -> None:
        """Toggle pause / resume cooking."""
        current_state = self._state_data.get("WorkState", 1)
        if current_state == const.WORK_STATE_PAUSED:
            # Resume
            self._state_data["WorkState"] = const.WORK_STATE_HEATING
            self.async_set_updated_data(self._state_data)
            await self.client.async_set_property("PauseSwitch", 0)
        else:
            # Pause
            self._state_data["WorkState"] = const.WORK_STATE_PAUSED
            self.async_set_updated_data(self._state_data)
            await self.client.async_set_property("PauseSwitch", 1)

    async def async_stop_cooking(self) -> None:
        """Stop cooking operation immediately."""
        self._state_data["WorkState"] = const.WORK_STATE_STANDBY
        self._state_data["RemainingWorkTime"] = 0
        self.async_set_updated_data(self._state_data)
        await self.client.async_set_property("WorkSwitch", 0)
