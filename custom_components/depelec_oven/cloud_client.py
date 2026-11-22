"""Aliyun IoT Cloud Client for Depelec TD55 Ultra Oven."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Any
import uuid

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from . import const

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{const.DOMAIN}_auth"


def _token_fingerprint(iot_token: str, refresh_token: str) -> str:
    """Compute a short hash of configured initial tokens to detect YAML updates."""
    raw = f"{iot_token}|{refresh_token}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


class DepelecCloudClient:
    """Async Cloud Client for Depelec Oven via Aliyun IoT API Gateway."""

    def __init__(
        self,
        hass: HomeAssistant | None = None,
        session: aiohttp.ClientSession | None = None,
        iot_id: str = const.DEFAULT_IOT_ID,
        app_key: str = const.DEFAULT_APP_KEY,
        app_secret: str = const.DEFAULT_APP_SECRET,
        initial_iot_token: str = const.DEFAULT_INITIAL_IOT_TOKEN,
        initial_refresh_token: str = const.DEFAULT_INITIAL_REFRESH_TOKEN,
        identity_id: str = const.DEFAULT_IDENTITY_ID,
        product_key: str = const.DEFAULT_PRODUCT_KEY,
        device_name: str = const.DEFAULT_DEVICE_NAME,
    ) -> None:
        self._hass = hass
        self._session = session
        self._own_session = False
        self.iot_id = iot_id
        self.app_key = app_key
        self.app_secret = app_secret
        self.identity_id = identity_id
        self.product_key = product_key
        self.device_name = device_name

        self._iot_token = initial_iot_token
        self._refresh_token = initial_refresh_token
        self._initial_fingerprint = _token_fingerprint(
            initial_iot_token, initial_refresh_token
        )
        self._token_issued_at = 0  # Unknown age until refreshed or loaded from store
        self._alcs_access_key = ""
        self._alcs_access_token = ""
        self._lock = asyncio.Lock()

        self._store: Store[dict[str, Any]] | None = (
            Store(hass, STORAGE_VERSION, STORAGE_KEY) if hass is not None else None
        )

    @property
    def has_credentials(self) -> bool:
        """Return True if cloud credentials are configured."""
        return bool(
            self.iot_id
            and self.identity_id
            and (self._iot_token or self._refresh_token)
        )

    @property
    def cached_alcs_credentials(self) -> tuple[str, str]:
        """Return persisted ALCS (accessKey, accessToken) if available."""
        return self._alcs_access_key, self._alcs_access_token

    async def async_load_storage(self) -> None:
        """Load cached tokens and ALCS credentials asynchronously via HA Store."""
        if self._store is None:
            return
        try:
            all_data = await self._store.async_load()
            if not isinstance(all_data, dict):
                return

            # Support both per-iot_id keyed format and legacy single-entry format
            key = self.iot_id or "default"
            entry = all_data.get(key)
            if not isinstance(entry, dict) and "iotToken" in all_data:
                entry = all_data

            if not isinstance(entry, dict):
                return

            # Always restore cached local ALCS credentials if present
            if entry.get("alcsAccessKey") and entry.get("alcsAccessToken"):
                self._alcs_access_key = entry["alcsAccessKey"]
                self._alcs_access_token = entry["alcsAccessToken"]
            if not self.product_key and entry.get("productKey"):
                self.product_key = entry["productKey"]
            if not self.device_name and entry.get("deviceName"):
                self.device_name = entry["deviceName"]

            # Only use cached cloud tokens if the user hasn't updated initial tokens in YAML
            saved_fp = entry.get("initial_fingerprint")
            if saved_fp and saved_fp != self._initial_fingerprint and (
                self._iot_token or self._refresh_token
            ):
                _LOGGER.info(
                    "Detected updated initial cloud tokens in configuration; ignoring stale cached cloud tokens"
                )
                return

            if entry.get("iotToken"):
                self._iot_token = entry["iotToken"]
            if entry.get("refreshToken"):
                self._refresh_token = entry["refreshToken"]
            if isinstance(entry.get("token_issued_at"), (int, float)):
                self._token_issued_at = int(entry["token_issued_at"])
            _LOGGER.info("Loaded persisted Aliyun credentials from HA storage")
        except Exception as err:
            _LOGGER.warning("Could not read auth storage: %s", err)

    async def async_save_storage(self) -> None:
        """Persist refreshed tokens and ALCS credentials atomically via HA Store."""
        if self._store is None:
            return
        try:
            all_data = await self._store.async_load()
            if not isinstance(all_data, dict) or "iotToken" in all_data:
                all_data = {}

            key = self.iot_id or "default"
            all_data[key] = {
                "iotToken": self._iot_token,
                "refreshToken": self._refresh_token,
                "identityId": self.identity_id,
                "token_issued_at": self._token_issued_at,
                "initial_fingerprint": self._initial_fingerprint,
                "alcsAccessKey": self._alcs_access_key,
                "alcsAccessToken": self._alcs_access_token,
                "productKey": self.product_key,
                "deviceName": self.device_name,
            }
            await self._store.async_save(all_data)
            _LOGGER.debug("Saved refreshed Aliyun credentials to HA storage")
        except Exception as err:
            _LOGGER.warning("Could not write auth storage: %s", err)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close session if created internally."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    def _sign_headers(self, path: str, body_bytes: bytes) -> dict[str, str]:
        """Sign request according to Alibaba Cloud API Gateway HMAC-SHA1 specification."""
        c_md5 = base64.b64encode(hashlib.md5(body_bytes).digest()).decode("utf-8")
        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4()).upper()
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        sign_headers = {
            "x-ca-key": self.app_key,
            "x-ca-nonce": nonce,
            "x-ca-stage": "RELEASE",
            "x-ca-timestamp": timestamp,
            "x-ca-version": "1",
        }
        canonical = (
            f"POST\napplication/json; charset=utf-8\n{c_md5}\napplication/octet-stream\n{date}\n"
            + "\n".join(f"{k}:{sign_headers[k]}" for k in sorted(sign_headers))
            + f"\n{path}"
        )
        signature = base64.b64encode(
            hmac.new(
                self.app_secret.encode("utf-8"),
                canonical.encode("utf-8"),
                hashlib.sha1,
            ).digest()
        ).decode("utf-8")

        return {
            "Content-Type": "application/octet-stream",
            "Accept": "application/json; charset=utf-8",
            "Content-MD5": c_md5,
            "Date": date,
            "X-Ca-Key": self.app_key,
            "X-Ca-Nonce": nonce,
            "X-Ca-Timestamp": timestamp,
            "X-Ca-Stage": "RELEASE",
            "X-Ca-Version": "1",
            "X-Ca-Signature-Headers": ",".join(sorted(sign_headers)),
            "X-Ca-Signature-Method": "HmacSHA1",
            "X-Ca-Signature": signature,
        }

    async def async_check_or_refresh_token(
        self,
        force: bool = False,
        failed_token: str | None = None,
    ) -> bool:
        """Check if iotToken is near expiry (refresh after 18h) and refresh it."""
        if not self._refresh_token:
            return bool(self._iot_token)

        async with self._lock:
            # If another concurrent coroutine already refreshed past failed_token, reuse it
            if failed_token and self._iot_token and self._iot_token != failed_token:
                return True

            now = int(time.time())
            if (
                not force
                and self._iot_token
                and self._token_issued_at > 0
                and (now - self._token_issued_at < 18 * 3600)
            ):
                return True

            # On first boot with a fresh YAML iotToken and no stored timestamp yet, try it first
            if not force and self._iot_token and self._token_issued_at == 0:
                self._token_issued_at = now
                return True

            _LOGGER.info("Refreshing Aliyun IoT token via /account/checkOrRefreshSession...")
            path = "/account/checkOrRefreshSession"
            body = {
                "id": str(uuid.uuid4()).upper(),
                "version": "1.0",
                "request": {
                    "language": "zh-CN",
                    "appKey": self.app_key,
                    "apiVer": "1.0.4",
                },
                "params": {
                    "request": {
                        "refreshToken": self._refresh_token,
                        "identityId": self.identity_id,
                    }
                },
            }
            body_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
            headers = self._sign_headers(path, body_bytes)
            url = f"https://api.link.aliyun.com{path}"

            session = await self._get_session()
            try:
                async with session.post(
                    url,
                    data=body_bytes,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.error(
                            "Token refresh HTTP %s: %s", resp.status, text[:200]
                        )
                        return False
                    resp_json = await resp.json(content_type=None)
                    data = resp_json.get("data") if isinstance(resp_json, dict) else None
                    if (
                        isinstance(resp_json, dict)
                        and resp_json.get("code") == 200
                        and isinstance(data, dict)
                    ):
                        new_iot = data.get("iotToken")
                        new_refresh = data.get("refreshToken")
                        if new_iot:
                            self._iot_token = new_iot
                        if new_refresh:
                            self._refresh_token = new_refresh
                        self._token_issued_at = int(time.time())
                        await self.async_save_storage()
                        _LOGGER.info(
                            "Successfully refreshed Aliyun IoT tokens (valid for next 20h)"
                        )
                        return True

                    _LOGGER.error("Failed to refresh token: %s", resp_json)
                    return False
            except Exception as err:
                _LOGGER.error("Exception during token refresh: %s", err)
                return False

    async def _async_request(
        self,
        path: str,
        api_ver: str,
        params: dict[str, Any],
        retry_on_auth_fail: bool = True,
    ) -> dict[str, Any] | None:
        """Execute a signed request to Aliyun IoT Gateway with auto-refresh on auth error."""
        if not self.has_credentials:
            return None

        await self.async_check_or_refresh_token()
        used_token = self._iot_token

        body = {
            "id": str(uuid.uuid4()).upper(),
            "version": "1.0",
            "request": {
                "language": "zh-CN",
                "appKey": self.app_key,
                "apiVer": api_ver,
                "iotToken": used_token,
            },
            "params": {
                **params,
                "iotToken": used_token,
            },
        }
        body_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers = self._sign_headers(path, body_bytes)
        url = f"https://api.link.aliyun.com{path}"

        session = await self._get_session()
        try:
            async with session.post(
                url,
                data=body_bytes,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error(
                        "Aliyun API %s returned HTTP %s: %s", path, resp.status, text[:200]
                    )
                    return None

                resp_json = await resp.json(content_type=None)
                if not isinstance(resp_json, dict):
                    return None

                code = resp_json.get("code")
                if code in (401, 460, 20621) and retry_on_auth_fail:
                    _LOGGER.warning(
                        "Token expired (code %s), forcing refresh and retrying...", code
                    )
                    refreshed = await self.async_check_or_refresh_token(
                        force=True, failed_token=used_token
                    )
                    if refreshed:
                        return await self._async_request(
                            path, api_ver, params, retry_on_auth_fail=False
                        )

                return resp_json
        except Exception as err:
            _LOGGER.error("Aliyun API request to %s failed: %s", path, err)
            return None

    async def async_get_alcs_access_info(self) -> dict[str, str] | None:
        """Fetch local ALCS accessKey/accessToken once from Aliyun Cloud and cache them."""
        if not self.iot_id or not self.has_credentials:
            return None

        resp = await self._async_request(
            path="/alcs/device/accessInfo/get",
            api_ver="1.0.0",
            params={"iotIdList": [self.iot_id]},
        )
        if not resp or resp.get("code") != 200:
            _LOGGER.warning("Failed to fetch ALCS local access info: %s", resp)
            return None

        data = resp.get("data")
        dto_list = data.get("alcsDeviceDTOList") if isinstance(data, dict) else None
        if not isinstance(dto_list, list) or not dto_list:
            return None

        info = dto_list[0]
        if not isinstance(info, dict):
            return None

        access_key = info.get("accessKey")
        access_token = info.get("accessToken")
        if not access_key or not access_token:
            return None

        self._alcs_access_key = access_key
        self._alcs_access_token = access_token
        if info.get("productKey"):
            self.product_key = info["productKey"]
        if info.get("deviceName"):
            self.device_name = info["deviceName"]

        await self.async_save_storage()
        _LOGGER.info(
            "Fetched and persisted ALCS local accessKey for device %s",
            self.device_name or self.iot_id,
        )
        return {
            "accessKey": access_key,
            "accessToken": access_token,
            "productKey": self.product_key,
            "deviceName": self.device_name,
        }

    async def async_get_properties(self) -> dict[str, Any] | None:
        """Fetch all properties for the oven."""
        resp = await self._async_request(
            path="/thing/properties/get",
            api_ver="1.0.4",
            params={"iotId": self.iot_id},
        )
        if resp and resp.get("code") == 200 and isinstance(resp.get("data"), dict):
            return resp["data"]
        return None

    async def async_set_properties(self, items: dict[str, Any]) -> bool:
        """Set one or more properties on the oven."""
        resp = await self._async_request(
            path="/thing/properties/set",
            api_ver="1.0.2",
            params={
                "iotId": self.iot_id,
                "items": items,
            },
        )
        if resp and resp.get("code") == 200:
            return True
        _LOGGER.warning("Set properties %s failed: %s", items, resp)
        return False

    async def async_set_property(self, prop: str, value: Any) -> bool:
        """Set a single property on the oven."""
        return await self.async_set_properties({prop: value})

    async def async_invoke_service(self, identifier: str, args: dict[str, Any]) -> bool:
        """Invoke a cooking program or device service."""
        resp = await self._async_request(
            path="/thing/service/invoke",
            api_ver="1.0.5",
            params={
                "iotId": self.iot_id,
                "identifier": identifier,
                "args": args,
            },
        )
        if resp and resp.get("code") == 200:
            return True
        _LOGGER.warning("Invoke service %s with %s failed: %s", identifier, args, resp)
        return False
