"""Low-level CoAP client for Depelec TD55 Ultra Oven (LinkKit ALCS)."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import random
import socket
import struct
import time
from typing import Any

from . import const

_LOGGER = logging.getLogger(__name__)

# RFC 7252 Constants
COAP_TYPE_CON = 0
COAP_TYPE_NON = 1
COAP_TYPE_ACK = 2
COAP_TYPE_RST = 3

COAP_CODE_EMPTY = 0
COAP_CODE_GET = 1
COAP_CODE_POST = 2
COAP_CODE_PUT = 3

COAP_RESP_CONTENT = 69   # 2.05
COAP_RESP_CHANGED = 68   # 2.04
COAP_RESP_UNAUTHORIZED = 129 # 4.01
COAP_RESP_FORBIDDEN = 131 # 4.03
COAP_RESP_NOT_FOUND = 132 # 4.04

OPTION_URI_PATH = 11
OPTION_CONTENT_FORMAT = 12
CONTENT_FORMAT_APP_JSON = 50

# Default ALCS setup keys
DEFAULT_AC = "Xtau@iot"
DEFAULT_AS = "Yx3DdsyetbSezlvc"


def _encode_option(delta: int, value: bytes) -> bytes:
    out = bytearray()
    if delta < 13:
        out.append(delta << 4)
    elif delta < 269:
        out.append(13 << 4)
        out.append(delta - 13)
    else:
        out.append(14 << 4)
        out.append((delta - 269) >> 8)
        out.append((delta - 269) & 0xFF)

    length = len(value)
    if length < 13:
        out[0] |= length
    elif length < 269:
        out[0] |= 13
        out.append(length - 13)
    else:
        out[0] |= 14
        out.append((length - 269) >> 8)
        out.append((length - 269) & 0xFF)

    return bytes(out) + value


def build_coap_packet(
    msg_type: int,
    code: int,
    msg_id: int,
    token: bytes,
    uri_path: str,
    payload: bytes = b"",
) -> bytes:
    """Build an RFC 7252 compliant CoAP packet."""
    byte0 = (1 << 6) | ((msg_type & 0x03) << 4) | (len(token) & 0x0F)
    header = bytes([byte0, code, (msg_id >> 8) & 0xFF, msg_id & 0xFF]) + token

    opts = bytearray()
    last = 0
    all_opts: list[tuple[int, bytes]] = []

    for seg in uri_path.strip("/").split("/"):
        if seg:
            all_opts.append((OPTION_URI_PATH, seg.encode("utf-8")))

    if payload:
        all_opts.append((OPTION_CONTENT_FORMAT, bytes([CONTENT_FORMAT_APP_JSON])))

    for opt_num, opt_val in all_opts:
        opts += _encode_option(opt_num - last, opt_val)
        last = opt_num

    if payload:
        return header + bytes(opts) + b"\xff" + payload
    return header + bytes(opts)


def parse_coap_packet(data: bytes) -> dict[str, Any]:
    """Parse an incoming CoAP packet."""
    if len(data) < 4:
        raise ValueError("Packet too short")

    byte0 = data[0]
    ver = byte0 >> 6
    msg_type = (byte0 >> 4) & 0x03
    tkl = byte0 & 0x0F
    code = data[1]
    msg_id = struct.unpack("!H", data[2:4])[0]
    token = data[4:4 + tkl]

    pos = 4 + tkl
    options: list[tuple[int, bytes]] = []
    opt_num = 0

    while pos < len(data):
        b = data[pos]
        if b == 0xFF:
            pos += 1
            break
        delta = (b >> 4) & 0x0F
        length = b & 0x0F
        pos += 1
        if delta == 13:
            delta = data[pos] + 13
            pos += 1
        elif delta == 14:
            delta = int.from_bytes(data[pos:pos + 2], "big") + 269
            pos += 2
        if length == 13:
            length = data[pos] + 13
            pos += 1
        elif length == 14:
            length = int.from_bytes(data[pos:pos + 2], "big") + 269
            pos += 2
        opt_num += delta
        options.append((opt_num, data[pos:pos + length]))
        pos += length

    payload = data[pos:]
    return {
        "ver": ver,
        "type": msg_type,
        "code": code,
        "msg_id": msg_id,
        "token": token,
        "options": options,
        "payload": payload,
    }


def _hmac_sha1_b64(key: bytes, msg: bytes) -> str:
    return base64.b64encode(hmac.new(key, msg, hashlib.sha1).digest()).decode("utf-8")


class DepelecCoapClient:
    """Async CoAP client communicating directly with the TG7100C oven module."""

    def __init__(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
        product_key: str = const.DEFAULT_PRODUCT_KEY,
        device_name: str = const.DEFAULT_DEVICE_NAME,
    ) -> None:
        self.host = host
        self.port = port
        self.product_key = product_key
        self.device_name = device_name
        self._msg_id = random.randint(1000, 50000)
        self._session_key: bytes | None = None
        self._session_id: int | None = None

    def _next_mid(self) -> int:
        self._msg_id = (self._msg_id + 1) & 0xFFFF
        if self._msg_id == 0:
            self._msg_id = 1
        return self._msg_id

    async def _send_coap_raw(
        self,
        method_code: int,
        path: str,
        payload_dict: dict | None = None,
        timeout: float = 3.0,
    ) -> dict[str, Any] | None:
        """Send a CoAP CON packet and await ACK or separate response."""
        loop = asyncio.get_running_loop()
        mid = self._next_mid()
        token = struct.pack("!I", mid)
        payload_bytes = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8") if payload_dict else b""

        pkt = build_coap_packet(COAP_TYPE_CON, method_code, mid, token, path, payload_bytes)

        def _do_udp() -> bytes | None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(timeout)
            try:
                s.sendto(pkt, (self.host, self.port))
                start = time.time()
                while time.time() - start < timeout:
                    try:
                        data, addr = s.recvfrom(4096)
                        parsed = parse_coap_packet(data)
                        # Check if this matches our token or MID
                        if parsed["token"] == token or parsed["msg_id"] == mid:
                            if parsed["code"] != COAP_CODE_EMPTY:
                                return data
                            # Empty ACK: wait for separate response
                    except socket.timeout:
                        break
                return None
            except Exception as e:
                _LOGGER.debug("UDP sendto/recv error on %s:%s: %s", self.host, self.port, e)
                return None
            finally:
                s.close()

        raw_resp = await loop.run_in_executor(None, _do_udp)
        if not raw_resp:
            return None

        try:
            parsed = parse_coap_packet(raw_resp)
            if parsed["payload"]:
                return json.loads(parsed["payload"].decode("utf-8", errors="replace"))
        except Exception as e:
            _LOGGER.debug("Failed to decode response payload: %s", e)

        return None

    async def async_auth(self, prefix: str = DEFAULT_AC, secret: str = DEFAULT_AS) -> bool:
        """Perform ALCS auth handshake to obtain a local session."""
        access_key = f"{prefix}_1001"
        access_token = _hmac_sha1_b64(secret.encode("utf-8"), access_key.encode("utf-8"))
        random_key = "".join([random.choice("0123456789abcdef") for _ in range(16)])
        sign = _hmac_sha1_b64(access_token.encode("utf-8"), random_key.encode("utf-8"))

        auth_payload = {
            "version": "1.0",
            "method": "core/service/auth",
            "id": self._next_mid(),
            "params": {
                "prodKey": self.product_key,
                "deviceName": self.device_name,
                "encrypt": "payload",
                "randomKey": random_key,
                "sign": sign,
                "accessKey": access_key,
            },
        }

        path = f"/dev/{self.product_key}/{self.device_name}/core/service/auth"
        resp = await self._send_coap_raw(COAP_CODE_GET, path, auth_payload)
        if resp and resp.get("code") == 200:
            _LOGGER.info("Local ALCS auth successful with %s", self.host)
            return True
        return False

    async def async_get_properties(self) -> dict[str, Any] | None:
        """Fetch all device properties over local CoAP."""
        mid = self._next_mid()
        req_payload = {
            "id": mid,
            "version": "1.0",
            "method": "thing.service.property.get",
            "params": {},
        }
        path = f"/sys/{self.product_key}/{self.device_name}/thing/service/property/get"
        resp = await self._send_coap_raw(COAP_CODE_GET, path, req_payload)
        if resp and "data" in resp:
            return resp["data"]
        return None

    async def async_set_property(self, prop_name: str, value: Any) -> bool:
        """Set a property (e.g. LightSwitch, ChildLockSwitch) on the oven."""
        mid = self._next_mid()
        req_payload = {
            "id": mid,
            "version": "1.0",
            "method": "thing.service.property.set",
            "params": {prop_name: value},
        }
        path = f"/sys/{self.product_key}/{self.device_name}/thing/service/property/set"
        resp = await self._send_coap_raw(COAP_CODE_GET, path, req_payload)
        return resp is not None and resp.get("code") == 200

    async def async_invoke_service(self, identifier: str, args: dict[str, Any]) -> bool:
        """Invoke a cooking service mode on the oven."""
        mid = self._next_mid()
        req_payload = {
            "id": mid,
            "version": "1.0",
            "method": f"thing.service.{identifier}",
            "params": args,
        }
        path = f"/sys/{self.product_key}/{self.device_name}/thing/service/{identifier}"
        resp = await self._send_coap_raw(COAP_CODE_GET, path, req_payload)
        return resp is not None and resp.get("code") == 200
