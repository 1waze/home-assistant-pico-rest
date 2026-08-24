"""Select platform for writable Pico REST configuration values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .const import LED_EFFECTS, LED_ELEVATOR_EFFECTS, WEEKDAYS
from .control import async_write_config, config_value
from .entity import PicoRestEntity


@dataclass(frozen=True, kw_only=True)
class PicoSelectDescription(SelectEntityDescription):
    config_key: str


DEVICE_SELECTS: dict[str, tuple[PicoSelectDescription, ...]] = {
    "pool_controller": (
        PicoSelectDescription(
            key="config_mode",
            name="Betriebsmodus Einstellung",
            config_key="mode",
            options=("auto", "manual"),
        ),
    ),
    "led_controller": (
        PicoSelectDescription(
            key="config_effect",
            name="Standard-Effekt",
            config_key="effect",
            options=LED_EFFECTS,
        ),
        PicoSelectDescription(
            key="config_elevator_effect",
            name="Aufzug-Effekt Einstellung",
            config_key="elevator_effect",
            options=LED_ELEVATOR_EFFECTS,
        ),
    ),
}


class PicoRestSelect(PicoRestEntity, SelectEntity):
    """Writable select Pico REST configuration value."""

    entity_description: PicoSelectDescription

    def __init__(self, coordinator, description: PicoSelectDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def current_option(self) -> str | None:
        value: Any = config_value(self.coordinator, self.entity_description.config_key)
        return str(value) if value is not None else None

    async def async_select_option(self, option: str) -> None:
        await async_write_config(
            self.coordinator,
            {self.entity_description.config_key: option},
        )


class LedScheduleEffectSelect(PicoRestEntity, SelectEntity):
    """Writable LED effect for one weekday."""

    _attr_options = list(LED_EFFECTS)

    def __init__(self, coordinator, day_key: str, day_name: str) -> None:
        super().__init__(coordinator, f"schedule_control_{day_key}_effect")
        self._day_key = day_key
        self._attr_name = f"{day_name} Effekt Einstellung"

    @property
    def current_option(self) -> str | None:
        value = config_value(self.coordinator, "days", self._day_key, "effect")
        return str(value) if value is not None else None

    async def async_select_option(self, option: str) -> None:
        await async_write_config(
            self.coordinator,
            {"days": {self._day_key: {"effect": option}}},
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    device_type = str(coordinator.info.get("device_type", ""))
    entities: list[SelectEntity] = [
        PicoRestSelect(coordinator, description)
        for description in DEVICE_SELECTS.get(device_type, ())
    ]

    if device_type == "led_controller":
        for day_key, day_name in WEEKDAYS:
            entities.append(LedScheduleEffectSelect(coordinator, day_key, day_name))

    async_add_entities(entities)
