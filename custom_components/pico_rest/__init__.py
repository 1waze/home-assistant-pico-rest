"""Pico REST integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    PicoRestClient,
    PicoRestConnectionError,
    PicoRestInvalidResponse,
)
from .const import DEFAULT_PORT, PLATFORMS, SUPPORTED_DEVICE_TYPES
from .coordinator import PicoRestCoordinator
from .migration import apply_v041_entity_cleanup, migrate_entry_identity


@dataclass
class PicoRestRuntimeData:
    """Runtime data for a Pico REST config entry."""

    client: PicoRestClient
    coordinator: PicoRestCoordinator


type PicoRestConfigEntry = ConfigEntry[PicoRestRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: PicoRestConfigEntry) -> bool:
    """Set up Pico REST from a config entry."""
    session = async_get_clientsession(hass)
    client = PicoRestClient(
        session,
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )

    try:
        info = await client.async_get_info()
    except PicoRestConnectionError as err:
        raise ConfigEntryNotReady(f"Cannot reach Pico REST device: {err}") from err
    except PicoRestInvalidResponse as err:
        raise ConfigEntryError(f"Invalid Pico REST device: {err}") from err

    device_type = str(info.get("device_type", ""))
    if device_type not in SUPPORTED_DEVICE_TYPES:
        raise ConfigEntryError(f"Unsupported Pico REST device type: {device_type}")

    device_id = str(info["device_id"])
    migrate_entry_identity(hass, entry, device_type, device_id)
    apply_v041_entity_cleanup(hass, entry, device_type, device_id)

    coordinator = PicoRestCoordinator(hass, entry, client, info)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = PicoRestRuntimeData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PicoRestConfigEntry) -> bool:
    """Unload a Pico REST config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
