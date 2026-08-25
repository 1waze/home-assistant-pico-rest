"""Registry migration helpers for Pico REST."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def migrate_entry_identity(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_type: str,
    device_id: str,
) -> None:
    """Migrate v0.2.x host-based registry identifiers to the hardware device ID."""
    old_identifier = f"{device_type}:{entry.data[CONF_HOST]}"

    if entry.unique_id != device_id:
        hass.config_entries.async_update_entry(entry, unique_id=device_id)

    device_registry = dr.async_get(hass)
    old_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, old_identifier), entry.entry_id
    )
    if old_device is not None:
        device_registry.async_update_device(
            old_device.id,
            new_identifiers={(DOMAIN, device_id)},
            serial_number=device_id,
        )
        _LOGGER.debug(
            "Migrated Pico REST device identifier from %s to %s",
            old_identifier,
            device_id,
        )

    entity_registry = er.async_get(hass)
    old_prefix = f"{old_identifier}:"
    new_prefix = f"{device_id}:"
    for registry_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        unique_id = registry_entry.unique_id
        if unique_id.startswith(old_prefix):
            entity_registry.async_update_entity(
                registry_entry.entity_id,
                new_unique_id=new_prefix + unique_id[len(old_prefix) :],
            )
