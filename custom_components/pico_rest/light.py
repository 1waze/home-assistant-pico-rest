"""RGB color controls for Pico REST LED devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .const import WEEKDAYS
from .control import async_write_config, config_value, has_capability
from .entity import PicoRestEntity


def _rgb(value: Any) -> tuple[int, int, int] | None:
    """Convert a Pico RGB list to a Home Assistant RGB tuple."""
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    try:
        rgb = tuple(max(0, min(255, int(component))) for component in value)
    except (TypeError, ValueError):
        return None
    return rgb  # type: ignore[return-value]


class PicoRestColorLight(PicoRestEntity, LightEntity):
    """Base class for an RGB configuration color."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    @property
    def is_on(self) -> bool:
        """Return whether the configured color is non-black."""
        rgb = self.rgb_color
        return rgb is not None and any(rgb)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Set the configured color to black."""
        await self._async_set_rgb((0, 0, 0))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set the configured RGB color when supplied by Home Assistant."""
        rgb = kwargs.get("rgb_color")
        if rgb is None:
            return
        await self._async_set_rgb(tuple(int(component) for component in rgb))

    async def _async_set_rgb(self, rgb: tuple[int, int, int]) -> None:
        raise NotImplementedError


class LedGlobalColor(PicoRestColorLight):
    """Writable global LED effect color."""

    def __init__(self, coordinator, field: str, name: str) -> None:
        super().__init__(coordinator, f"config_{field}_color")
        self._field = field
        self._attr_name = name

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        return _rgb(config_value(self.coordinator, self._field))

    async def _async_set_rgb(self, rgb: tuple[int, int, int]) -> None:
        await async_write_config(self.coordinator, {self._field: list(rgb)})


class LedScheduleColor(PicoRestColorLight):
    """Writable LED color for one weekday."""

    def __init__(self, coordinator, day_key: str, day_name: str) -> None:
        super().__init__(coordinator, f"schedule_control_{day_key}_color")
        self._day_key = day_key
        self._attr_name = f"{day_name} Farbe"

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        return _rgb(config_value(self.coordinator, "days", self._day_key, "color"))

    async def _async_set_rgb(self, rgb: tuple[int, int, int]) -> None:
        await async_write_config(
            self.coordinator,
            {"days": {self._day_key: {"color": list(rgb)}}},
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    if str(coordinator.info.get("device_type", "")) != "led_controller":
        return
    if not has_capability(coordinator, "config"):
        return

    entities: list[LightEntity] = [
        LedGlobalColor(coordinator, "color1", "Farbe 1"),
        LedGlobalColor(coordinator, "color2", "Farbe 2"),
    ]
    entities.extend(
        LedScheduleColor(coordinator, day_key, day_name)
        for day_key, day_name in WEEKDAYS
    )
    async_add_entities(entities)
