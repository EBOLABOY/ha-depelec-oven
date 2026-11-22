"""Async local CoAP client for Depelec TD55 Ultra Oven (Aliyun LinkKit ALCS)."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import random
import string
import struct
import time
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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

COAP_RESP_CHANGED = 68       # 2.04
COAP_RESP_CONTENT = 69       # 2.05
COAP_RESP_UNAUTHORIZED = 129 # 4.01
COAP_RESP_FORBIDDEN = 131    # 4.03
COAP_RESP_NOT_FOUND = 132    # 4.04

OPTION_URI_PATH = 11
OPTION_CONTENT_FORMAT = 12
OPTION_SESSIONID = 71        # Aliyun ALCS CoAP option (COAP_OPTION_SESSIONID)

CONTENT_FORMAT_APP_OCTET_STREAM = 42
CONTENT_FORMAT_APP_JSON = 50

# Aliyun LinkKit ALCS constants (from aliyun/iotkit-embedded alcs_api.c & alcs_localsetup.c)
ALCS_AES_IV = b"a1b1c1d1e1f1g1h1"
DEFAULT_ALCS_PREFIX = "Xtau@iot"
DEFAULT_ALCS_SECRET = "Yx3DdsyetbSezlvc"
ALCS_HEARTBEAT_INTERVAL = 60.0  # Server expires sessions after 120s without heartbeat
_RANDOM_KEY_ALPHABET = string.ascii_letters + string.digits


def _encode_uint(val: int) -> bytes:
    """Encode an unsigned integer using minimal big-endian bytes per RFC 7252."""
    if val == 0:
        return b""
    return val.to_bytes((val.bit_length() + 7) // 8, "big")


def _encode_option(delta: int, value: bytes) -> bytes:
    """Encode a single CoAP option."""
    if delta < 0:
        raise ValueError(f"CoAP options must be sorted ascending (delta={delta})")

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
    content_format: int | None = None,
    session_id: int | None = None,
) -> bytes:
    """Build an RFC 7252 compliant CoAP packet with optional ALCS SessionId."""
    if len(token) > 8:
        raise ValueError("CoAP token length cannot exceed 8 bytes")

    byte0 = (1 << 6) | ((msg_type & 0x03) << 4) | (len(token) & 0x0F)
    header = bytes([byte0, code, (msg_id >> 8) & 0xFF, msg_id & 0xFF]) + token

    all_opts: list[tuple[int, bytes]] = []
    for seg in uri_path.strip("/").split("/"):
        if seg:
            all_opts.append((OPTION_URI_PATH, seg.encode("utf-8")))

    if payload:
        fmt = CONTENT_FORMAT_APP_JSON if content_format is None else content_format
        all_opts.append((OPTION_CONTENT_FORMAT, _encode_uint(fmt)))

    if session_id is not None:
        all_opts.append((OPTION_SESSIONID, _encode_uint(session_id)))

    # CoAP options must appear in non-decreasing option number order
    all_opts.sort(key=lambda item: item[0])

    opts = bytearray()
    last = 0
    for opt_num, opt_val in all_opts:
        opts += _encode_option(opt_num - last, opt_val)
        last = opt_num

    if payload:
        return header + bytes(opts) + b"\xff" + payload
    return header + bytes(opts)


def parse_coap_packet(data: bytes) -> dict[str, Any]:
    """Parse an incoming CoAP packet with bounds checking."""
    data_len = len(data)
    if data_len < 4:
        raise ValueError("CoAP packet too short")

    byte0 = data[0]
    ver = byte0 >> 6
    msg_type = (byte0 >> 4) & 0x03
    tkl = byte0 & 0x0F
    if tkl > 8 or 4 + tkl > data_len:
        raise ValueError(f"Invalid CoAP token length: {tkl}")

    code = data[1]
    msg_id = struct.unpack("!H", data[2:4])[0]
    token = data[4 : 4 + tkl]

    pos = 4 + tkl
    options: list[tuple[int, bytes]] = []
    opt_num = 0

    while pos < data_len:
        b = data[pos]
        if b == 0xFF:
            pos += 1
            break
        delta = (b >> 4) & 0x0F
        length = b & 0x0F
        pos += 1

        if delta == 13:
            if pos >= data_len:
                raise ValueError("Truncated CoAP option delta (13)")
            delta = data[pos] + 13
            pos += 1
        elif delta == 14:
            if pos + 2 > data_len:
                raise ValueError("Truncated CoAP option delta (14)")
            delta = int.from_bytes(data[pos : pos + 2], "big") + 269
            pos += 2
        elif delta == 15:
            raise ValueError("Invalid CoAP option delta (15)")

        if length == 13:
            if pos >= data_len:
                raise ValueError("Truncated CoAP option length (13)")
            length = data[pos] + 13
            pos += 1
        elif length == 14:
            if pos + 2 > data_len:
                raise ValueError("Truncated CoAP option length (14)")
            length = int.from_bytes(data[pos : pos + 2], "big") + 269
            pos += 2
        elif length == 15:
            raise ValueError("Invalid CoAP option length (15)")

        if pos + length > data_len:
            raise ValueError("Truncated CoAP option value")

        opt_num += delta
        options.append((opt_num, data[pos : pos + length]))
        pos += length

    session_id: int | None = None
    for num, val in options:
        if num == OPTION_SESSIONID:
            session_id = int.from_bytes(val, "big") if val else 0
            break

    return {
        "ver": ver,
        "type": msg_type,
        "code": code,
        "msg_id": msg_id,
        "token": token,
        "options": options,
        "session_id": session_id,
        "payload": data[pos:],
    }


def _hmac_sha1_bytes(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha1).digest()


def _hmac_sha1_b64(key: bytes, msg: bytes) -> str:
    return base64.b64encode(_hmac_sha1_bytes(key, msg)).decode("utf-8")


def alcs_encrypt(plaintext: bytes, session_key: bytes) -> bytes:
    """Encrypt payload using Aliyun ALCS split AES-128-CBC scheme (alcs_api.c).

    In Alibaba's iotkit-embedded ALCS implementation, the leading full 16-byte blocks
    are encrypted with AES-128-CBC using ALCS_AES_IV, and the final PKCS7-padded block
    is encrypted in a separate AES-128-CBC call re-initialized with the same IV.
    """
    key = session_key[:16]
    len1 = len(plaintext) & ~0xF
    pad = 16 - (len(plaintext) - len1)
    out = bytearray()

    if len1:
        enc = Cipher(algorithms.AES(key), modes.CBC(ALCS_AES_IV)).encryptor()
        out.extend(enc.update(plaintext[:len1]) + enc.finalize())

    last_block = plaintext[len1:] + bytes([pad]) * pad
    enc = Cipher(algorithms.AES(key), modes.CBC(ALCS_AES_IV)).encryptor()
    out.extend(enc.update(last_block) + enc.finalize())
    return bytes(out)


def alcs_decrypt(ciphertext: bytes, session_key: bytes) -> bytes:
    """Decrypt payload using Aliyun ALCS split AES-128-CBC scheme (alcs_api.c)."""
    if not ciphertext or len(ciphertext) % 16 != 0:
        raise ValueError(f"Invalid ALCS ciphertext length: {len(ciphertext)}")

    key = session_key[:16]
    n_blocks = len(ciphertext) >> 4
    out = bytearray()

    if n_blocks > 1:
        dec = Cipher(algorithms.AES(key), modes.CBC(ALCS_AES_IV)).decryptor()
        out.extend(dec.update(ciphertext[: (n_blocks - 1) * 16]) + dec.finalize())

    dec = Cipher(algorithms.AES(key), modes.CBC(ALCS_AES_IV)).decryptor()
    last_plain = dec.update(ciphertext[(n_blocks - 1) * 16 :]) + dec.finalize()
    out.extend(last_plain)

    pad = out[-1]
    if pad < 1 or pad > 16 or out[-pad:] != bytes([pad]) * pad:
        raise ValueError(f"Invalid ALCS PKCS7 padding byte: {pad}")
    return bytes(out[:-pad])


def build_default_alcs_credentials(
    prefix: str = DEFAULT_ALCS_PREFIX,
    secret: str = DEFAULT_ALCS_SECRET,
) -> tuple[str, str]:
    """Derive 13-char ALCS accessKey and accessToken from prefix and secret."""
    # Format per alcs_server.c: KEYPREFIX_LEN(8) + version(1) + sep(1) + KEYSEQ_LEN(3) = 13 chars
    access_key = f"{prefix}1_001"
    access_token = _hmac_sha1_b64(secret.encode("utf-8"), access_key.encode("utf-8"))
    return access_key, access_token


class _CoapDatagramProtocol(asyncio.DatagramProtocol):
    """Persistent async UDP protocol to keep a fixed local port for ALCS sessions."""

    def __init__(self) -> None:
        self.transport: asyncio.DatagramTransport | None = None
        self.queue: asyncio.Queue[tuple[bytes, tuple[str, int]]] = asyncio.Queue()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.queue.put_nowait((data, addr))

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("ALCS UDP socket error: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        self.transport = None


class DepelecCoapClient:
    """Async ALCS CoAP client communicating directly with the oven over LAN."""

    def __init__(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
        product_key: str = const.DEFAULT_PRODUCT_KEY,
        device_name: str = const.DEFAULT_DEVICE_NAME,
        access_key: str = const.DEFAULT_ALCS_ACCESS_KEY,
        access_token: str = const.DEFAULT_ALCS_ACCESS_TOKEN,
    ) -> None:
        self.host = host
        self.port = port
        self.product_key = product_key
        self.device_name = device_name
        self.access_key = access_key
        self.access_token = access_token

        self._msg_id = random.randint(1000, 50000)
        self._session_key: bytes | None = None
        self._session_id: int | None = None
        self._last_heartbeat: float = 0.0
        self._protocol: _CoapDatagramProtocol | None = None
        self._lock = asyncio.Lock()

    @property
    def has_credentials(self) -> bool:
        """Return True if explicit ALCS accessKey/accessToken are configured."""
        return bool(self.access_key and self.access_token)

    def set_credentials(
        self,
        access_key: str,
        access_token: str,
        product_key: str | None = None,
        device_name: str | None = None,
    ) -> None:
        """Update ALCS credentials and clear any existing session."""
        self.access_key = access_key
        self.access_token = access_token
        if product_key:
            self.product_key = product_key
        if device_name:
            self.device_name = device_name
        self._session_key = None
        self._session_id = None

    def _next_mid(self) -> int:
        self._msg_id = (self._msg_id + 1) & 0xFFFF
        if self._msg_id == 0:
            self._msg_id = 1
        return self._msg_id

    async def _ensure_transport(self) -> _CoapDatagramProtocol:
        """Open a persistent UDP socket so source IP:port stays bound to the ALCS session."""
        if self._protocol is not None and self._protocol.transport is not None:
            if not self._protocol.transport.is_closing():
                return self._protocol

        loop = asyncio.get_running_loop()
        _, protocol = await loop.create_datagram_endpoint(
            _CoapDatagramProtocol,
            local_addr=("0.0.0.0", 0),
        )
        self._protocol = protocol
        # A new local UDP port invalidates any server-side session tied to the old port
        self._session_key = None
        self._session_id = None
        return protocol

    async def async_close(self) -> None:
        """Close the persistent UDP transport and clear session state."""
        self._session_key = None
        self._session_id = None
        if self._protocol is not None and self._protocol.transport is not None:
            self._protocol.transport.close()
        self._protocol = None

    async def _send_and_recv(
        self,
        pkt: bytes,
        mid: int,
        token: bytes,
        timeout: float = 3.0,
    ) -> dict[str, Any] | None:
        """Send a CoAP packet over the persistent UDP socket and await its response."""
        protocol = await self._ensure_transport()
        assert protocol.transport is not None

        # Drain stale buffered packets before sending
        while not protocol.queue.empty():
            try:
                protocol.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        protocol.transport.sendto(pkt, (self.host, self.port))
        deadline = time.monotonic() + timeout

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                raw, _addr = await asyncio.wait_for(protocol.queue.get(), timeout=remaining)
            except asyncio.TimeoutError:
                return None

            try:
                parsed = parse_coap_packet(raw)
            except ValueError as err:
                _LOGGER.debug("Ignoring malformed CoAP packet from %s: %s", self.host, err)
                continue

            if parsed["token"] != token and parsed["msg_id"] != mid:
                continue

            # Empty ACK means the device will send a separate response packet
            if parsed["code"] == COAP_CODE_EMPTY:
                continue

            # Acknowledge separate CON responses from the device
            if parsed["type"] == COAP_TYPE_CON and protocol.transport is not None:
                ack = build_coap_packet(
                    COAP_TYPE_ACK,
                    COAP_CODE_EMPTY,
                    parsed["msg_id"],
                    b"",
                    "",
                )
                protocol.transport.sendto(ack, (self.host, self.port))

            return parsed

    async def async_discover(self, timeout: float = 2.5) -> dict[str, str] | None:
        """Query /dev/core/service/dev on LAN to auto-discover productKey and deviceName."""
        async with self._lock:
            return await self._async_discover_locked(timeout=timeout)

    async def _async_discover_locked(self, timeout: float = 2.5) -> dict[str, str] | None:
        mid = self._next_mid()
        token = struct.pack("!I", mid)
        req = {"id": str(mid), "version": "1.0", "method": "core.service.dev", "params": {}}
        pkt = build_coap_packet(
            COAP_TYPE_CON,
            COAP_CODE_GET,
            mid,
            token,
            "/dev/core/service/dev",
            json.dumps(req, separators=(",", ":")).encode("utf-8"),
            content_format=CONTENT_FORMAT_APP_JSON,
        )
        resp = await self._send_and_recv(pkt, mid, token, timeout=timeout)
        if not resp or not resp["payload"]:
            return None

        try:
            body = json.loads(resp["payload"].decode("utf-8", errors="replace"))
            profiles = body.get("data", {}).get("devices", {}).get("profile", [])
            if profiles and isinstance(profiles, list):
                profile = profiles[0]
                pk = profile.get("productKey")
                dn = profile.get("deviceName")
                if pk and dn:
                    self.product_key = pk
                    self.device_name = dn
                    _LOGGER.info(
                        "Discovered local ALCS oven at %s:%s (pk=%s, dn=%s)",
                        self.host,
                        self.port,
                        pk,
                        dn,
                    )
                    return {"productKey": pk, "deviceName": dn}
        except Exception as err:
            _LOGGER.debug("Failed to parse ALCS discovery response: %s", err)
        return None

    async def _async_auth_with_key_locked(
        self,
        access_key: str,
        access_token: str,
        timeout: float = 3.0,
    ) -> bool:
        """Execute ALCS /core/service/auth handshake with a specific key/token pair."""
        if not self.product_key or not self.device_name:
            await self._async_discover_locked()
        if not self.product_key or not self.device_name:
            _LOGGER.debug("ALCS auth aborted: missing product_key or device_name")
            return False

        mid = self._next_mid()
        token = struct.pack("!I", mid)
        client_random_key = "".join(random.choices(_RANDOM_KEY_ALPHABET, k=16))
        sign = _hmac_sha1_b64(
            access_token.encode("utf-8"),
            client_random_key.encode("utf-8"),
        )

        auth_payload = {
            "version": "1.0",
            "method": "core/service/auth",
            "id": str(mid),
            "params": {
                "prodKey": self.product_key,
                "deviceName": self.device_name,
                "encrypt": "payload",
                "randomKey": client_random_key,
                "sign": sign,
                "accessKey": access_key,
            },
        }
        path = f"/dev/{self.product_key}/{self.device_name}/core/service/auth"
        pkt = build_coap_packet(
            COAP_TYPE_CON,
            COAP_CODE_GET,
            mid,
            token,
            path,
            json.dumps(auth_payload, separators=(",", ":")).encode("utf-8"),
            content_format=CONTENT_FORMAT_APP_JSON,
        )
        resp = await self._send_and_recv(pkt, mid, token, timeout=timeout)
        if not resp or not resp["payload"]:
            return False

        try:
            body = json.loads(resp["payload"].decode("utf-8", errors="replace"))
        except Exception as err:
            _LOGGER.debug("Failed to parse ALCS auth response: %s", err)
            return False

        data = body.get("data")
        if body.get("code") != 200 or not isinstance(data, dict):
            _LOGGER.debug("ALCS auth rejected by %s: %s", self.host, body)
            return False

        session_id = data.get("sessionId")
        server_random_key = data.get("randomKey")
        if not session_id or not server_random_key:
            # alcs_server.c returns code=200 with empty data={} when accessKey length is invalid
            _LOGGER.debug("ALCS auth incomplete response from %s: %s", self.host, body)
            return False

        self._session_id = int(session_id)
        self._session_key = _hmac_sha1_bytes(
            access_token.encode("utf-8"),
            f"{client_random_key}{server_random_key}".encode("utf-8"),
        )
        self._last_heartbeat = time.monotonic()
        _LOGGER.info(
            "Local ALCS session established with %s:%s (sessionId=%s)",
            self.host,
            self.port,
            self._session_id,
        )
        return True

    async def _async_ensure_auth_locked(self) -> bool:
        """Ensure an active ALCS session exists, refreshing heartbeat if needed."""
        if self._session_id is not None and self._session_key is not None:
            if time.monotonic() - self._last_heartbeat > ALCS_HEARTBEAT_INTERVAL:
                if not await self._async_heartbeat_locked():
                    self._session_id = None
                    self._session_key = None
            if self._session_id is not None and self._session_key is not None:
                return True

        # Try configured / cloud-fetched credentials first, then offline factory default
        candidates: list[tuple[str, str]] = []
        if self.access_key and self.access_token:
            candidates.append((self.access_key, self.access_token))
        default_pair = build_default_alcs_credentials()
        if default_pair not in candidates:
            candidates.append(default_pair)

        for key, tok in candidates:
            if await self._async_auth_with_key_locked(key, tok):
                return True
        return False

    async def _async_heartbeat_locked(self) -> bool:
        """Send ALCS heartbeat to keep the 120s device-side session alive."""
        if self._session_id is None or self._session_key is None:
            return False

        mid = self._next_mid()
        token = struct.pack("!I", mid)
        req = {"id": str(mid), "version": "1.0", "params": {"delayTime": 5000}}
        pkt = build_coap_packet(
            COAP_TYPE_CON,
            COAP_CODE_GET,
            mid,
            token,
            "/dev/core/service/heartBeat",
            json.dumps(req, separators=(",", ":")).encode("utf-8"),
            content_format=CONTENT_FORMAT_APP_JSON,
        )
        resp = await self._send_and_recv(pkt, mid, token, timeout=2.5)
        if not resp or not resp["payload"]:
            return False

        try:
            if resp["session_id"] is not None:
                plain = alcs_decrypt(resp["payload"], self._session_key)
            else:
                plain = resp["payload"]
            body = json.loads(plain.decode("utf-8", errors="replace"))
            if body.get("code") == 200:
                self._last_heartbeat = time.monotonic()
                return True
        except Exception as err:
            _LOGGER.debug("ALCS heartbeat failed: %s", err)
        return False

    async def _async_secure_request(
        self,
        path: str,
        payload_dict: dict[str, Any],
        timeout: float = 3.0,
    ) -> dict[str, Any] | None:
        """Send an encrypted ALCS CoAP request and return decrypted JSON response."""
        async with self._lock:
            for attempt in range(2):
                if not await self._async_ensure_auth_locked():
                    return None
                assert self._session_key is not None
                assert self._session_id is not None

                mid = self._next_mid()
                token = struct.pack("!I", mid)
                plain_bytes = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
                enc_bytes = alcs_encrypt(plain_bytes, self._session_key)

                pkt = build_coap_packet(
                    COAP_TYPE_CON,
                    COAP_CODE_GET,
                    mid,
                    token,
                    path,
                    enc_bytes,
                    content_format=CONTENT_FORMAT_APP_OCTET_STREAM,
                    session_id=self._session_id,
                )
                resp = await self._send_and_recv(pkt, mid, token, timeout=timeout)
                if resp is None:
                    return None

                if resp["code"] == COAP_RESP_UNAUTHORIZED:
                    _LOGGER.debug("ALCS 4.01 on %s (attempt %s), re-authenticating", path, attempt + 1)
                    self._session_id = None
                    self._session_key = None
                    continue

                if not resp["payload"]:
                    return None

                try:
                    if resp["session_id"] is not None:
                        dec = alcs_decrypt(resp["payload"], self._session_key)
                    else:
                        dec = resp["payload"]
                    return json.loads(dec.decode("utf-8", errors="replace"))
                except Exception as err:
                    _LOGGER.debug("Failed to decrypt/parse ALCS response for %s: %s", path, err)
                    # Session key might be out of sync after oven reboot
                    self._session_id = None
                    self._session_key = None
                    continue

            return None

    async def async_auth(self) -> bool:
        """Public helper to authenticate an ALCS session."""
        async with self._lock:
            return await self._async_ensure_auth_locked()

    async def async_get_properties(
        self,
        properties: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch device properties over local ALCS CoAP."""
        if not self.product_key or not self.device_name:
            await self.async_discover()
        if not self.product_key or not self.device_name:
            return None

        mid = self._next_mid()
        prop_list = properties if properties is not None else const.OVEN_PROPERTIES
        req_payload = {
            "id": str(mid),
            "version": "1.0",
            "method": "thing.service.property.get",
            "params": prop_list,
        }
        path = f"/sys/{self.product_key}/{self.device_name}/thing/service/property/get"
        resp = await self._async_secure_request(path, req_payload)
        if resp and resp.get("code") == 200 and isinstance(resp.get("data"), dict):
            return resp["data"]
        return None

    async def async_set_properties(self, items: dict[str, Any]) -> bool:
        """Set one or more properties on the oven over local ALCS CoAP."""
        if not self.product_key or not self.device_name:
            await self.async_discover()
        if not self.product_key or not self.device_name:
            return False

        mid = self._next_mid()
        req_payload = {
            "id": str(mid),
            "version": "1.0",
            "method": "thing.service.property.set",
            "params": items,
        }
        path = f"/sys/{self.product_key}/{self.device_name}/thing/service/property/set"
        resp = await self._async_secure_request(path, req_payload)
        return resp is not None and resp.get("code") == 200

    async def async_set_property(self, prop_name: str, value: Any) -> bool:
        """Set a single property on the oven over local ALCS CoAP."""
        return await self.async_set_properties({prop_name: value})

    async def async_invoke_service(self, identifier: str, args: dict[str, Any]) -> bool:
        """Invoke a cooking service mode on the oven over local ALCS CoAP."""
        if not self.product_key or not self.device_name:
            await self.async_discover()
        if not self.product_key or not self.device_name:
            return False

        mid = self._next_mid()
        req_payload = {
            "id": str(mid),
            "version": "1.0",
            "method": f"thing.service.{identifier}",
            "params": args,
        }
        path = f"/sys/{self.product_key}/{self.device_name}/thing/service/{identifier}"
        resp = await self._async_secure_request(path, req_payload)
        return resp is not None and resp.get("code") == 200
