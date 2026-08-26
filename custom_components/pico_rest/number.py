"""Number platform for writable Pico REST configuration values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .control import async_write_config, config_value, has_capability
from .entity import PicoRestEntity


@dataclass(frozen=True, kw_only=True)
class PicoNumberDescription(NumberEntityDescription):
    config_key: str


DEVICE_NUMBERS: dict[str, tuple[PicoNumberDescription, ...]] = {
    "pool_controller": (
        PicoNumberDescription(
            key="config_target_temp",
            name="Solltemperatur",
            config_key="target_temp",
            native_min_value=5,
            native_max_value=40,
            native_step=0.5,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            mode=NumberMode.BOX,
        ),
        PicoNumberDescription(
            key="config_diff_on",
            name="Temperaturdifferenz Ein",
            config_key="diff_on",
            native_min_value=0,
            native_max_value=30,
            native_step=0.5,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            mode=NumberMode.BOX,
        ),
        PicoNumberDescription(
            key="config_diff_off",
            name="Temperaturdifferenz Aus",
            config_key="diff_off",
            native_min_value=0,
            native_max_value=30,
            native_step=0.5,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            mode=NumberMode.BOX,
        ),
    ),
    "led_controller": (
        PicoNumberDescription(
            key="config_brightness",
            name="Helligkeit",
            config_key="brightness",
            native_min_value=0,
            native_max_value=1,
            native_step=0.05,
            mode=NumberMode.SLIDER,
        ),
        PicoNumberDescription(
            key="config_effect_speed",
            name="Effektgeschwindigkeit Einstellung",
            config_key="effect_speed",
            native_min_value=1,
            native_max_value=20,
            native_step=1,
            mode=NumberMode.SLIDER,
        ),
        PicoNumberDescription(
            key="config_effect_intensity",
            name="Effektintensität Einstellung",
            config_key="effect_intensity",
            native_min_value=0,
            native_max_value=1,
            native_step=0.05,
            mode=NumberMode.SLIDER,
        ),
        PicoNumberDescription(
            key="config_two_color_split",
            name="Zweifarben-Aufteilung Einstellung",
            config_key="two_color_split",
            native_min_value=0,
            native_max_value=1,
            native_step=0.05,
            mode=NumberMode.SLIDER,
        ),
        PicoNumberDescription(
            key="config_elevator_speed",
            name="Aufzug-Geschwindigkeit Einstellung",
            config_key="elevator_speed",
            native_min_value=1,
            native_max_value=20,
            native_step=1,
            mode=NumberMode.SLIDER,
        ),
        PicoNumberDescription(
            key="config_effect_delay_ms",
            name="Effekt-Verzögerung",
            config_key="effect_delay_ms",
            native_min_value=0,
            native_max_value=1000,
            native_step=1,
            mode=NumberMode.BOX,
        ),
        PicoNumberDescription(
            key="config_elevator_delay_ms",
            name="Aufzug-Verzögerung",
            config_key="elevator_delay_ms",
            native_min_value=0,
            native_max_value=1000,
            native_step=1,
            mode=NumberMode.BOX,
        ),
        PicoNumberDescription(
            key="config_elevator_poll_seconds",
            name="Aufzug-Abfrageintervall",
            config_key="elevator_poll_seconds",
            native_min_value=0.2,
            native_max_value=60,
            native_step=0.2,
            mode=NumberMode.BOX,
        ),
    ),
    "sun_wind_monitor": (
        PicoNumberDescription(
            key="config_max_wind",
            name="Wind-Grenzwert",
            config_key="max_wind",
            native_min_value=0,
            native_max_value=500,
            native_step=1,
            mode=NumberMode.BOX,
        ),
        PicoNumberDescription(
            key="config_max_boe",
            name="Böen-Zähler Grenzwert",
            config_key="max_boe",
            native_min_value=0,
            native_max_value=100,
            native_step=1,
            mode=NumberMode.BOX,
        ),
        PicoNumberDescription(
            key="config_max_hell",
            name="Helligkeits-Grenzwert",
            config_key="max_hell",
            native_min_value=0,
            native_max_value=1000000,
            native_step=100,
            mode=NumberMode.BOX,
        ),
    ),
}


class PicoRestNumber(PicoRestEntity, NumberEntity):
    """Writable numeric Pico REST configuration value."""

    entity_description: PicoNumberDescription

    def __init__(self, coordinator, description: PicoNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        value: Any = config_value(self.coordinator, self.entity_description.config_key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        step = self.entity_description.native_step
        if step == 1:
            payload_value: int | float = int(round(value))
        else:
            payload_value = float(value)
        await async_write_config(
            self.coordinator,
            {self.entity_description.config_key: payload_value},
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
    async_add_entities(
        PicoRestNumber(coordinator, description)
        for description in DEVICE_NUMBERS.get(device_type, ())
    )
