"""Coordinator for Pico REST devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PicoRestClient, PicoRestError
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVALS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PicoRestCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling of one Pico REST device."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PicoRestClient,
        info: dict[str, Any],
    ) -> None:
        self.client = client
        self.info = info
        device_type = str(info.get("device_type", "unknown"))
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{client.host}",
            update_interval=DEFAULT_SCAN_INTERVALS.get(device_type, DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_get_status()

            # Config is fetched only for devices that advertise it.  It is kept
            # in a private top-level key so all v0.1.0 status paths remain stable.
            capabilities = self.info.get("capabilities", [])
            if isinstance(capabilities, list) and "config" in capabilities:
                data["_config"] = await self.client.async_get_config()

            return data
        except PicoRestError as err:
            raise UpdateFailed(f"Pico REST update failed: {err}") from err
