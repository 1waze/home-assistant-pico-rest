"""Binary sensor platform for Pico REST."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .entity import PicoRestEntity

BoolFn = Callable[[dict[str, Any]], bool | None]


@dataclass(frozen=True, kw_only=True)
class PicoBinaryDescription(BinarySensorEntityDescription):
    """Describe a Pico REST binary sensor."""

    value_fn: BoolFn


def _bool(key: str) -> BoolFn:
    def value(data: dict[str, Any]) -> bool | None:
        raw = data.get(key)
        return raw if isinstance(raw, bool) else None

    return value


DEVICE_BINARY_SENSORS: dict[str, tuple[PicoBinaryDescription, ...]] = {
    "pool_controller": (
        PicoBinaryDescription(key="pump", name="Pumpe", value_fn=_bool("pump")),
        PicoBinaryDescription(key="valve", name="Ventil", value_fn=_bool("valve")),
        PicoBinaryDescription(
            key="clean_mode",
            name="Reinigung",
            entity_registry_enabled_default=False,
            value_fn=_bool("clean_mode"),
        ),
        PicoBinaryDescription(
            key="t_pool_anomaly",
            name="Temperaturanomalie",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_fn=_bool("t_pool_anomaly"),
        ),
    ),
    "led_controller": (
        PicoBinaryDescription(
            key="scheduled_on",
            name="Zeitplan aktiv",
            value_fn=_bool("scheduled_on"),
        ),
    ),
    "elevator_monitor": (
        PicoBinaryDescription(
            key="input_conflict",
            name="Eingangskonflikt",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_fn=_bool("input_conflict"),
        ),
        PicoBinaryDescription(
            key="wifi_connected",
            name="WLAN verbunden",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            value_fn=_bool("wifi_connected"),
        ),
    ),
    "sun_wind_monitor": (
        PicoBinaryDescription(
            key="boe",
            name="Böenalarm",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_fn=_bool("boe"),
        ),
        PicoBinaryDescription(key="q1", name="Q1", value_fn=_bool("q1")),
        PicoBinaryDescription(key="q2", name="Q2", value_fn=_bool("q2")),
        PicoBinaryDescription(
            key="wifi_connected",
            name="WLAN verbunden",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            value_fn=_bool("wifi_connected"),
        ),
    ),
    "pool_sensor_monitor": (
        PicoBinaryDescription(
            key="wifi_connected",
            name="WLAN verbunden",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            value_fn=_bool("wifi_connected"),
        ),
    ),
}


class PicoRestBinarySensor(PicoRestEntity, BinarySensorEntity):
    """Generic Pico REST binary sensor."""

    entity_description: PicoBinaryDescription

    def __init__(self, coordinator, description: PicoBinaryDescription) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.data or {})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pico REST binary sensors."""
    coordinator = entry.runtime_data.coordinator
    device_type = str(coordinator.info.get("device_type", ""))
    descriptions = DEVICE_BINARY_SENSORS.get(device_type, ())
    async_add_entities(PicoRestBinarySensor(coordinator, d) for d in descriptions)
