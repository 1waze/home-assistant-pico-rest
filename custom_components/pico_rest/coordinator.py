"""Coordinator for Pico REST devices."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from time import monotonic
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PicoRestClient, PicoRestError
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVALS, DOMAIN

_LOGGER = logging.getLogger(__name__)
INFO_REFRESH_INTERVAL = 60.0


class PicoRestCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling of one Pico REST device."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: PicoRestClient,
        info: dict[str, Any],
    ) -> None:
        self.client = client
        self.info = info
        self.device_id = str(info["device_id"])
        self.last_successful_update: datetime | None = None
        self._last_info_refresh = monotonic()
        device_type = str(info.get("device_type", "unknown"))
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{self.device_id}",
            update_interval=DEFAULT_SCAN_INTERVALS.get(
                device_type, DEFAULT_SCAN_INTERVAL
            ),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            now = monotonic()
            if now - self._last_info_refresh >= INFO_REFRESH_INTERVAL:
                current_info = await self.client.async_get_info()
                current_device_id = str(current_info["device_id"])
                if current_device_id != self.device_id:
                    raise UpdateFailed(
                        "Device identity changed at configured host "
                        f"({self.device_id} -> {current_device_id})"
                    )
                self.info = current_info
                self._last_info_refresh = now

            data = await self.client.async_get_status()

            capabilities = self.info.get("capabilities", [])
            if isinstance(capabilities, list) and "config" in capabilities:
                data["_config"] = await self.client.async_get_config()

            self.last_successful_update = datetime.now(UTC)
            return data
        except UpdateFailed:
            raise
        except PicoRestError as err:
            raise UpdateFailed(f"Pico REST update failed: {err}") from err
