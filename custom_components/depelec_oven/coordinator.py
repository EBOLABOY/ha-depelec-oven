"""DataUpdateCoordinator for Depelec TD55 Ultra Oven."""
from __future__ import annotations

from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import const
from .cloud_client import DepelecCloudClient
from .coap_client import DepelecCoapClient

_LOGGER = logging.getLogger(__name__)


class DepelecOvenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage LAN ALCS / Cloud polling and commands for Depelec Oven."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
        scan_interval: int = const.DEFAULT_SCAN_INTERVAL,
        connection_mode: str = const.DEFAULT_CONNECTION_MODE,
        iot_id: str = const.DEFAULT_IOT_ID,
        device_name: str = const.DEFAULT_DEVICE_NAME,
        product_key: str = const.DEFAULT_PRODUCT_KEY,
        app_key: str = const.DEFAULT_APP_KEY,
        app_secret: str = const.DEFAULT_APP_SECRET,
        identity_id: str = const.DEFAULT_IDENTITY_ID,
        initial_iot_token: str = const.DEFAULT_INITIAL_IOT_TOKEN,
        initial_refresh_token: str = const.DEFAULT_INITIAL_REFRESH_TOKEN,
        alcs_access_key: str = const.DEFAULT_ALCS_ACCESS_KEY,
        alcs_access_token: str = const.DEFAULT_ALCS_ACCESS_TOKEN,
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
        self.connection_mode = connection_mode
        self.active_transport: str = (
            "local" if connection_mode == const.CONNECTION_MODE_LOCAL else "cloud"
        )
        self._last_alcs_bootstrap_try: float = 0.0

        try:
            client_session = async_get_clientsession(hass)
        except Exception:
            client_session = None

        self.cloud_client: DepelecCloudClient | None = None
        if connection_mode != const.CONNECTION_MODE_LOCAL:
            self.cloud_client = DepelecCloudClient(
                hass=hass,
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

        self.coap_client: DepelecCoapClient | None = None
        if connection_mode != const.CONNECTION_MODE_CLOUD and host:
            self.coap_client = DepelecCoapClient(
                host=host,
                port=port,
                product_key=product_key,
                device_name=device_name,
                access_key=alcs_access_key,
                access_token=alcs_access_token,
            )

        # Keep `.client` attribute for compatibility with existing code
        self.client: Any = self.cloud_client or self.coap_client

        # Stable device identifier for entity unique_ids (preserves existing device_name IDs)
        self._configured_device_name = device_name
        self._configured_iot_id = iot_id

        # UI state helpers for pre-start configuration
        default_mode_name = "普通蒸"
        default_cfg = const.MODES[default_mode_name]
        self.selected_mode: str = default_mode_name
        self.target_temp: int = default_cfg["default_temp"]
        self.down_target_temp: int = default_cfg["default_temp"]
        self.target_time: int = default_cfg["default_time"]

        # Shadow state using exact Alink thing-model keys
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
            "Mode": 0,
            "LightSwitch": 0,
            "ChildLockSwitch": 0,
            "Door": 0,
            "Cistern": 0,
            "WaterShortage": 0,
        }

    @property
    def device_identifier(self) -> str:
        """Return a stable identifier for entity unique_ids and device registry."""
        if self._configured_device_name:
            return self._configured_device_name
        if self.coap_client and self.coap_client.device_name:
            return self.coap_client.device_name
        if self.cloud_client and self.cloud_client.device_name:
            return self.cloud_client.device_name
        if self._configured_iot_id:
            return self._configured_iot_id
        return self.host

    async def async_initialize(self) -> None:
        """Load persisted credentials and bootstrap local ALCS access if possible."""
        if self.cloud_client is not None:
            await self.cloud_client.async_load_storage()
            # Copy any cached ALCS credentials into the local CoAP client
            if self.coap_client is not None and not self.coap_client.has_credentials:
                ak, at = self.cloud_client.cached_alcs_credentials
                if ak and at:
                    self.coap_client.set_credentials(
                        ak,
                        at,
                        product_key=self.cloud_client.product_key,
                        device_name=self.cloud_client.device_name,
                    )

        if self.coap_client is not None:
            if not self.coap_client.device_name or not self.coap_client.product_key:
                await self.coap_client.async_discover()

            # In auto mode, fetch ALCS credentials once from cloud if not yet cached
            if (
                self.connection_mode == const.CONNECTION_MODE_AUTO
                and not self.coap_client.has_credentials
                and self.cloud_client is not None
                and self.cloud_client.has_credentials
            ):
                await self._async_bootstrap_alcs_credentials()

    async def _async_bootstrap_alcs_credentials(self) -> bool:
        """Fetch ALCS accessKey/accessToken once from Aliyun cloud and cache locally."""
        if self.cloud_client is None or self.coap_client is None:
            return False
        now = time.monotonic()
        if (
            self._last_alcs_bootstrap_try > 0
            and now - self._last_alcs_bootstrap_try < 600
        ):
            return False
        self._last_alcs_bootstrap_try = now
        info = await self.cloud_client.async_get_alcs_access_info()
        if info:
            self.coap_client.set_credentials(
                info["accessKey"],
                info["accessToken"],
                product_key=info.get("productKey"),
                device_name=info.get("deviceName"),
            )
            return True
        return False

    async def async_shutdown(self) -> None:
        """Close local UDP and cloud HTTP resources cleanly."""
        if self.coap_client is not None:
            await self.coap_client.async_close()
        if self.cloud_client is not None:
            await self.cloud_client.close()

    def _merge_properties(self, props: dict[str, Any]) -> None:
        for k, v in props.items():
            if isinstance(v, dict) and "value" in v:
                self._state_data[k] = v["value"]
            else:
                self._state_data[k] = v

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest telemetry from oven (LAN-first in auto mode, pure LAN in local mode)."""
        props: dict[str, Any] | None = None

        # 1. Try local ALCS CoAP first (auto or local mode)
        if self.coap_client is not None and self.connection_mode in (
            const.CONNECTION_MODE_AUTO,
            const.CONNECTION_MODE_LOCAL,
        ):
            props = await self.coap_client.async_get_properties()
            if props:
                self.active_transport = "local"
                self._merge_properties(props)
                return dict(self._state_data)

        # 2. Fallback to cloud (or primary in cloud mode)
        if self.cloud_client is not None and self.connection_mode in (
            const.CONNECTION_MODE_AUTO,
            const.CONNECTION_MODE_CLOUD,
        ):
            props = await self.cloud_client.async_get_properties()
            if props:
                self.active_transport = "cloud"
                self._merge_properties(props)
                if (
                    self.connection_mode == const.CONNECTION_MODE_AUTO
                    and self.coap_client is not None
                    and not self.coap_client.has_credentials
                ):
                    await self._async_bootstrap_alcs_credentials()
                return dict(self._state_data)

        raise UpdateFailed(
            f"Unable to fetch oven status via {self.connection_mode} mode "
            f"(host={self.host})"
        )

    async def _async_send_property(self, prop: str, value: Any) -> bool:
        """Send a property command via LAN first (if enabled), falling back to cloud."""
        if self.coap_client is not None and self.connection_mode in (
            const.CONNECTION_MODE_AUTO,
            const.CONNECTION_MODE_LOCAL,
        ):
            if await self.coap_client.async_set_property(prop, value):
                self.active_transport = "local"
                return True
            if self.connection_mode == const.CONNECTION_MODE_LOCAL:
                return False

        if self.cloud_client is not None and self.connection_mode in (
            const.CONNECTION_MODE_AUTO,
            const.CONNECTION_MODE_CLOUD,
        ):
            if await self.cloud_client.async_set_property(prop, value):
                self.active_transport = "cloud"
                return True

        return False

    async def _async_send_service(self, identifier: str, args: dict[str, Any]) -> bool:
        """Invoke a cooking service via LAN first (if enabled), falling back to cloud."""
        if self.coap_client is not None and self.connection_mode in (
            const.CONNECTION_MODE_AUTO,
            const.CONNECTION_MODE_LOCAL,
        ):
            if await self.coap_client.async_invoke_service(identifier, args):
                self.active_transport = "local"
                return True
            if self.connection_mode == const.CONNECTION_MODE_LOCAL:
                return False

        if self.cloud_client is not None and self.connection_mode in (
            const.CONNECTION_MODE_AUTO,
            const.CONNECTION_MODE_CLOUD,
        ):
            if await self.cloud_client.async_invoke_service(identifier, args):
                self.active_transport = "cloud"
                return True

        return False

    # -----------------------------------------------------------------------
    # Device Control Actions (verified against transport result, rollback on error)
    # -----------------------------------------------------------------------

    async def async_set_light(self, state: bool) -> None:
        """Toggle chamber light."""
        val = 1 if state else 0
        if not await self._async_send_property("LightSwitch", val):
            raise HomeAssistantError("下发炉灯开关指令失败，请检查网络连接或设备状态")
        self._state_data["LightSwitch"] = val
        self.async_set_updated_data(dict(self._state_data))

    async def async_set_child_lock(self, state: bool) -> None:
        """Toggle child safety lock."""
        val = 1 if state else 0
        if not await self._async_send_property("ChildLockSwitch", val):
            raise HomeAssistantError("下发童锁开关指令失败，请检查网络连接或设备状态")
        self._state_data["ChildLockSwitch"] = val
        self.async_set_updated_data(dict(self._state_data))

    def set_selected_mode(self, mode_name: str) -> None:
        """Update selected cooking mode in UI and load recommended temp/time."""
        if mode_name not in const.MODES:
            return
        cfg = const.MODES[mode_name]
        self.selected_mode = mode_name
        self.target_temp = cfg["default_temp"]
        self.down_target_temp = cfg["default_temp"]
        self.target_time = cfg["default_time"]
        self.async_set_updated_data(dict(self._state_data))

    def set_target_temp(self, temp: int) -> None:
        """Update UI target temperature, clamped to the active mode range."""
        cfg = const.MODES.get(self.selected_mode)
        if cfg:
            temp = max(cfg["min_temp"], min(cfg["max_temp"], int(temp)))
        self.target_temp = int(temp)
        self.async_set_updated_data(dict(self._state_data))

    def set_down_target_temp(self, temp: int) -> None:
        """Update UI lower-tube target temperature, clamped to the active mode range."""
        cfg = const.MODES.get(self.selected_mode)
        if cfg:
            temp = max(cfg["min_temp"], min(cfg["max_temp"], int(temp)))
        self.down_target_temp = int(temp)
        self.async_set_updated_data(dict(self._state_data))

    def set_target_time(self, mins: int) -> None:
        """Update UI target cooking duration."""
        self.target_time = max(1, min(180, int(mins)))
        self.async_set_updated_data(dict(self._state_data))

    async def async_start_cooking(self) -> None:
        """Start cooking using current selected mode, temp and duration."""
        cfg = const.MODES.get(self.selected_mode)
        if not cfg:
            raise HomeAssistantError(f"未知的烹饪模式: {self.selected_mode}")

        identifier = cfg["service"]
        args: dict[str, Any] = {
            "ToastTemperature": int(self.target_temp),
            "WorkTime": int(self.target_time),
            "WorkSwitch": 1,
            "AppointmentTime": 0,
        }
        if cfg["temp_control"] == 1:
            args["DownToastTemperature"] = int(self.down_target_temp)

        _LOGGER.info(
            "Starting oven mode: %s (%s) with %s", self.selected_mode, identifier, args
        )
        if not await self._async_send_service(identifier, args):
            raise HomeAssistantError(f"启动烹饪模式 [{self.selected_mode}] 失败")

        self._state_data["WorkState"] = const.WORK_STATE_HEATING
        self._state_data["Mode"] = cfg["id"]
        self._state_data["ToastTemperature"] = self.target_temp
        if cfg["temp_control"] == 1:
            self._state_data["DownToastTemperature"] = self.down_target_temp
        self._state_data["WorkTime"] = self.target_time
        self._state_data["RemainingWorkTime"] = self.target_time
        self.async_set_updated_data(dict(self._state_data))

    async def async_pause_cooking(self) -> None:
        """Toggle pause / resume cooking (only valid while heating or paused)."""
        current_state = self._state_data.get("WorkState", const.WORK_STATE_STANDBY)
        if current_state == const.WORK_STATE_PAUSED:
            if not await self._async_send_property("PauseSwitch", 0):
                raise HomeAssistantError("恢复烹饪指令下发失败")
            self._state_data["WorkState"] = const.WORK_STATE_HEATING
            self.async_set_updated_data(dict(self._state_data))
        elif current_state == const.WORK_STATE_HEATING:
            if not await self._async_send_property("PauseSwitch", 1):
                raise HomeAssistantError("暂停烹饪指令下发失败")
            self._state_data["WorkState"] = const.WORK_STATE_PAUSED
            self.async_set_updated_data(dict(self._state_data))
        else:
            raise HomeAssistantError("当前蒸烤箱未在运行中，无法执行暂停或继续操作")

    async def async_stop_cooking(self) -> None:
        """Stop cooking operation immediately via StopWork=1."""
        if not await self._async_send_property("StopWork", 1):
            raise HomeAssistantError("停止烹饪指令下发失败")
        self._state_data["WorkState"] = const.WORK_STATE_STANDBY
        self._state_data["Mode"] = 0
        self._state_data["WorkTime"] = 0
        self._state_data["RemainingWorkTime"] = 0
        self._state_data["ToastTemperature"] = 0
        self._state_data["DownToastTemperature"] = 0
        self.async_set_updated_data(dict(self._state_data))
