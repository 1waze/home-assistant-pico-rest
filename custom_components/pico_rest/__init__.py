"""Pico REST integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PicoRestClient
from .const import DEFAULT_PORT, PLATFORMS
from .coordinator import PicoRestCoordinator


@dataclass
class PicoRestRuntimeData:
    """Runtime data for a Pico REST config entry."""

    client: PicoRestClient
    coordinator: PicoRestCoordinator


PicoRestConfigEntry: TypeAlias = ConfigEntry[PicoRestRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: PicoRestConfigEntry) -> bool:
    """Set up Pico REST from a config entry."""
    session = async_get_clientsession(hass)
    client = PicoRestClient(
        session,
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    info = await client.async_get_info()
    coordinator = PicoRestCoordinator(hass, client, info)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = PicoRestRuntimeData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PicoRestConfigEntry) -> bool:
    """Unload a Pico REST config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
