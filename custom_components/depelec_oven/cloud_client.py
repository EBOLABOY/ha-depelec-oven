"""Aliyun IoT Cloud Client for Depelec TD55 Ultra Oven."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any
import uuid

import aiohttp

from . import const

_LOGGER = logging.getLogger(__name__)

STORAGE_PATH = "/config/.storage/depelec_oven_auth.json"


class DepelecCloudClient:
    """Async Cloud Client for Depelec Oven via Aliyun IoT API Gateway."""

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        iot_id: str = const.DEFAULT_IOT_ID,
        app_key: str = const.DEFAULT_APP_KEY,
        app_secret: str = const.DEFAULT_APP_SECRET,
        initial_iot_token: str = const.DEFAULT_INITIAL_IOT_TOKEN,
        initial_refresh_token: str = const.DEFAULT_INITIAL_REFRESH_TOKEN,
        identity_id: str = const.DEFAULT_IDENTITY_ID,
        product_key: str = const.DEFAULT_PRODUCT_KEY,
        device_name: str = const.DEFAULT_DEVICE_NAME,
        storage_path: str = STORAGE_PATH,
    ) -> None:
        self._session = session
        self._own_session = False
        self.iot_id = iot_id
        self.app_key = app_key
        self.app_secret = app_secret
        self.identity_id = identity_id
        self.product_key = product_key
        self.device_name = device_name
        self.storage_path = storage_path

        self._iot_token = initial_iot_token
        self._refresh_token = initial_refresh_token
        self._token_issued_at = int(time.time())
        self._lock = asyncio.Lock()

        # Load persisted token if available
        self._load_storage()

    def _load_storage(self) -> None:
        """Load cached tokens from storage file if present."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("iotToken"):
                        self._iot_token = data["iotToken"]
                    if data.get("refreshToken"):
                        self._refresh_token = data["refreshToken"]
                    if data.get("token_issued_at"):
                        self._token_issued_at = data["token_issued_at"]
                    _LOGGER.info("Loaded persisted Aliyun tokens from %s", self.storage_path)
        except Exception as err:
            _LOGGER.warning("Could not read auth storage %s: %s", self.storage_path, err)

    def _save_storage(self) -> None:
        """Save tokens to storage file."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "iotToken": self._iot_token,
                        "refreshToken": self._refresh_token,
                        "identityId": self.identity_id,
                        "token_issued_at": self._token_issued_at,
                    },
                    f,
                    indent=2,
                )
            _LOGGER.debug("Saved refreshed Aliyun tokens to %s", self.storage_path)
        except Exception as err:
            _LOGGER.warning("Could not write auth storage %s: %s", self.storage_path, err)

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
            hmac.new(self.app_secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha1).digest()
        ).decode("utf-8")

        headers = {
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
        return headers

    async def async_check_or_refresh_token(self, force: bool = False) -> bool:
        """Check if iotToken is near expiry (20 hours total, refresh after 18h) and refresh it."""
        async with self._lock:
            # Refresh if older than 18 hours or forced
            now = int(time.time())
            if not force and (now - self._token_issued_at < 18 * 3600):
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
                async with session.post(url, data=body_bytes, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    resp_json = await resp.json(content_type=None)
                    if resp_json.get("code") == 200 and "data" in resp_json:
                        data = resp_json["data"]
                        self._iot_token = data.get("iotToken", self._iot_token)
                        self._refresh_token = data.get("refreshToken", self._refresh_token)
                        self._token_issued_at = int(time.time())
                        self._save_storage()
                        _LOGGER.info("Successfully refreshed Aliyun IoT tokens (valid for next 20h)")
                        return True
                    else:
                        _LOGGER.error("Failed to refresh token: %s", resp_json)
                        return False
            except Exception as err:
                _LOGGER.error("Exception during token refresh: %s", err)
                return False

    async def _async_request(self, path: str, api_ver: str, params: dict[str, Any], retry_on_auth_fail: bool = True) -> dict[str, Any] | None:
        """Execute a signed request to Aliyun IoT Gateway with auto-refresh on 401/460."""
        await self.async_check_or_refresh_token()

        body = {
            "id": str(uuid.uuid4()).upper(),
            "version": "1.0",
            "request": {
                "language": "zh-CN",
                "appKey": self.app_key,
                "apiVer": api_ver,
                "iotToken": self._iot_token,
            },
            "params": {
                **params,
                "iotToken": self._iot_token,
            },
        }
        body_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers = self._sign_headers(path, body_bytes)
        url = f"https://api.link.aliyun.com{path}"

        session = await self._get_session()
        try:
            async with session.post(url, data=body_bytes, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                resp_json = await resp.json(content_type=None)
                code = resp_json.get("code")

                # If token expired/invalid (401, 460, 20621, etc.)
                if code in (401, 460, 20621) and retry_on_auth_fail:
                    _LOGGER.warning("Token expired (code %s), forcing refresh and retrying...", code)
                    refreshed = await self.async_check_or_refresh_token(force=True)
                    if refreshed:
                        return await self._async_request(path, api_ver, params, retry_on_auth_fail=False)

                return resp_json
        except Exception as err:
            _LOGGER.error("Aliyun API request to %s failed: %s", path, err)
            return None

    async def async_get_properties(self) -> dict[str, Any] | None:
        """Fetch all properties for the oven."""
        resp = await self._async_request(
            path="/thing/properties/get",
            api_ver="1.0.4",
            params={"iotId": self.iot_id},
        )
        if resp and resp.get("code") == 200:
            return resp.get("data")
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
