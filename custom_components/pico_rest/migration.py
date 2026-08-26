"""Registry migration helpers for Pico REST."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

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


UX_CLEANUP_OPTION = "_ux_cleanup_v041"

UX_DISABLED_KEYS_COMMON = {
    "info_api_version",
    "info_firmware",
    "ip",
    "last_successful_contact",
    "wifi_quality",
    "wifi_reconnects",
    "wifi_interface_resets",
    "wifi_offline_sec",
}

UX_DISABLED_KEYS_BY_DEVICE = {
    "pool_controller": {"mode", "clean_mode"},
    "sun_wind_monitor": {"cpu", "uptime_ms"},
    "pool_sensor_monitor": {"uptime_sec"},
    "led_controller": {
        "effect",
        "effect_speed",
        "effect_intensity",
        "two_color_split",
        "elevator_effect",
        "elevator_speed",
        *(f"schedule_{day}_{field}" for day in range(7) for field in ("on", "off", "effect")),
    },
}


def apply_v041_entity_cleanup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_type: str,
    device_id: str,
) -> None:
    """Disable redundant v0.4.0 entities while preserving their registry entries."""
    if entry.options.get(UX_CLEANUP_OPTION):
        return

    registry = er.async_get(hass)
    keys = set(UX_DISABLED_KEYS_COMMON)
    keys.update(UX_DISABLED_KEYS_BY_DEVICE.get(device_type, set()))
    prefix = f"{device_id}:"

    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        unique_id = registry_entry.unique_id
        if not unique_id.startswith(prefix):
            continue
        key = unique_id[len(prefix) :]
        if key not in keys or registry_entry.disabled_by is not None:
            continue
        registry.async_update_entity(
            registry_entry.entity_id,
            disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        )
        _LOGGER.debug("Disabled redundant Pico REST entity %s", registry_entry.entity_id)

    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, UX_CLEANUP_OPTION: True},
    )

