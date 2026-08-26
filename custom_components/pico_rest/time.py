"""Time platform for Pico REST schedules."""

from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .const import WEEKDAYS
from .control import async_write_config, config_value, has_capability
from .entity import PicoRestEntity


def _parse_hhmm(value: Any) -> time | None:
    if not isinstance(value, str):
        return None
    try:
        hour_s, minute_s = value.split(":", 1)
        return time(hour=int(hour_s), minute=int(minute_s))
    except (TypeError, ValueError):
        return None


def _format_hhmm(value: time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}"


class PoolScheduleTime(PicoRestEntity, TimeEntity):
    """Pool pump schedule time."""

    def __init__(self, coordinator, field: str, name: str) -> None:
        super().__init__(coordinator, f"config_{field}_time")
        self._field = field
        self._attr_name = name

    @property
    def native_value(self) -> time | None:
        return _parse_hhmm(config_value(self.coordinator, self._field))

    async def async_set_value(self, value: time) -> None:
        await async_write_config(self.coordinator, {self._field: _format_hhmm(value)})


class LedScheduleTime(PicoRestEntity, TimeEntity):
    """Writable LED on/off time for one weekday."""

    def __init__(self, coordinator, day_key: str, day_name: str, field: str) -> None:
        super().__init__(coordinator, f"schedule_control_{day_key}_{field}_time")
        self._day_key = day_key
        self._field = field
        label = "Einschaltzeit Einstellung" if field == "on" else "Ausschaltzeit Einstellung"
        self._attr_name = f"{day_name} {label}"

    @property
    def native_value(self) -> time | None:
        return _parse_hhmm(
            config_value(self.coordinator, "days", self._day_key, self._field)
        )

    async def async_set_value(self, value: time) -> None:
        await async_write_config(
            self.coordinator,
            {"days": {self._day_key: {self._field: _format_hhmm(value)}}},
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    device_type = str(coordinator.info.get("device_type", ""))
    if not has_capability(coordinator, "config"):
        return
    entities: list[TimeEntity] = []

    if device_type == "pool_controller":
        entities.extend(
            (
                PoolScheduleTime(coordinator, "pump_on", "Pumpen-Einschaltzeit"),
                PoolScheduleTime(coordinator, "pump_off", "Pumpen-Ausschaltzeit"),
            )
        )
    elif device_type == "led_controller":
        for day_key, day_name in WEEKDAYS:
            entities.append(LedScheduleTime(coordinator, day_key, day_name, "on"))
            entities.append(LedScheduleTime(coordinator, day_key, day_name, "off"))

    async_add_entities(entities)
