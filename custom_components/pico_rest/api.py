"""HTTP client for Pico REST API v1."""

from __future__ import annotations

from typing import Any

import async_timeout
from aiohttp import ClientError, ClientSession


class PicoRestError(Exception):
    """Base exception for Pico REST API errors."""


class PicoRestConnectionError(PicoRestError):
    """Raised when a Pico cannot be reached."""


class PicoRestInvalidResponse(PicoRestError):
    """Raised when a Pico returns an unexpected response."""


class PicoRestClient:
    """Small async client for Pico REST API v1."""

    def __init__(self, session: ClientSession, host: str, port: int = 80) -> None:
        self._session = session
        self.host = host.strip().removeprefix("http://").removeprefix("https://").rstrip("/")
        self.port = port

    @property
    def base_url(self) -> str:
        """Return HTTP base URL."""
        return f"http://{self.host}:{self.port}"

    async def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with async_timeout.timeout(5):
                async with self._session.get(url) as response:
                    if response.status != 200:
                        raise PicoRestInvalidResponse(
                            f"GET {path} returned HTTP {response.status}"
                        )
                    data = await response.json(content_type=None)
        except (TimeoutError, ClientError) as err:
            raise PicoRestConnectionError(f"Cannot reach {self.host}: {err}") from err
        except ValueError as err:
            raise PicoRestInvalidResponse(f"Invalid JSON from {path}") from err

        if not isinstance(data, dict):
            raise PicoRestInvalidResponse(f"Expected JSON object from {path}")
        return data

    async def _post_json(
        self, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST JSON and return a JSON object."""
        url = f"{self.base_url}{path}"
        try:
            async with async_timeout.timeout(5):
                async with self._session.post(url, json=payload or {}) as response:
                    data = await response.json(content_type=None)
                    if response.status < 200 or response.status >= 300:
                        detail = data.get("error") if isinstance(data, dict) else None
                        raise PicoRestInvalidResponse(
                            f"POST {path} returned HTTP {response.status}"
                            + (f": {detail}" if detail else "")
                        )
        except (TimeoutError, ClientError) as err:
            raise PicoRestConnectionError(f"Cannot reach {self.host}: {err}") from err
        except ValueError as err:
            raise PicoRestInvalidResponse(f"Invalid JSON from POST {path}") from err

        if not isinstance(data, dict):
            raise PicoRestInvalidResponse(f"Expected JSON object from POST {path}")

        if data.get("ok") is False:
            detail = data.get("error") or data.get("message") or "operation failed"
            raise PicoRestInvalidResponse(f"POST {path} failed: {detail}")

        return data

    async def async_get_info(self) -> dict[str, Any]:
        """Read /api/info and validate Pico REST API v1 identity."""
        info = await self._get_json("/api/info")
        if info.get("api") != "pico-rest":
            raise PicoRestInvalidResponse("Device does not identify as pico-rest")
        if info.get("api_version") != 1:
            raise PicoRestInvalidResponse(
                f"Unsupported Pico REST API version: {info.get('api_version')}"
            )
        device_id = info.get("device_id")
        if not isinstance(device_id, str) or not device_id.strip():
            raise PicoRestInvalidResponse(
                "Pico REST API v1 device does not provide a stable device_id"
            )
        info["device_id"] = device_id.strip().lower()
        return info

    async def async_get_status(self) -> dict[str, Any]:
        """Read /api/status."""
        return await self._get_json("/api/status")

    async def async_get_config(self) -> dict[str, Any]:
        """Read /api/config."""
        return await self._get_json("/api/config")

    async def async_update_config(self, patch: dict[str, Any]) -> dict[str, Any]:
        """Update device configuration through Pico REST API v1."""
        return await self._post_json("/api/config", patch)

    async def async_reboot(self) -> dict[str, Any]:
        """Request a device reboot."""
        return await self._post_json("/api/reboot")

    async def async_rollback(self) -> dict[str, Any]:
        """Request a firmware rollback."""
        return await self._post_json("/api/rollback")
