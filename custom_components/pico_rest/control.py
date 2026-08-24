"""Helpers shared by Pico REST writable entities."""

from __future__ import annotations

from typing import Any

from .api import PicoRestError
from .coordinator import PicoRestCoordinator


async def async_write_config(
    coordinator: PicoRestCoordinator, patch: dict[str, Any]
) -> None:
    """Write a config patch and refresh coordinator data."""
    try:
        await coordinator.client.async_update_config(patch)
    except PicoRestError:
        # Let Home Assistant surface the service/entity action failure.
        raise
    await coordinator.async_request_refresh()


def config_value(coordinator: PicoRestCoordinator, *keys: str) -> Any:
    """Read one value from the coordinator's cached /api/config result."""
    data: Any = (coordinator.data or {}).get("_config", {})
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data
