"""Switch platform for writable Pico REST configuration values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .control import async_write_config, config_value, has_capability
from .entity import PicoRestEntity


@dataclass(frozen=True, kw_only=True)
class PicoSwitchDescription(SwitchEntityDescription):
    config_key: str


DEVICE_SWITCHES: dict[str, tuple[PicoSwitchDescription, ...]] = {
    "pool_controller": (
        PicoSwitchDescription(
            key="config_clean_mode",
            name="Reinigungsmodus Einstellung",
            config_key="clean_mode",
        ),
    ),
    "led_controller": (
        PicoSwitchDescription(
            key="config_use_sunset",
            name="Sonnenuntergang verwenden",
            config_key="use_sunset",
        ),
    ),
}


class PicoRestSwitch(PicoRestEntity, SwitchEntity):
    """Writable boolean Pico REST configuration value."""

    entity_description: PicoSwitchDescription

    def __init__(self, coordinator, description: PicoSwitchDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value: Any = config_value(self.coordinator, self.entity_description.config_key)
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await async_write_config(
            self.coordinator,
            {self.entity_description.config_key: True},
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await async_write_config(
            self.coordinator,
            {self.entity_description.config_key: False},
        )


class PoolManualActorSwitch(PicoRestEntity, SwitchEntity):
    """Manual pool pump or valve control."""

    def __init__(self, coordinator, field: str, name: str) -> None:
        super().__init__(coordinator, f"manual_{field}_control")
        self._field = field
        self._attr_name = name

    @property
    def available(self) -> bool:
        """Only expose manual actor control while the controller is in manual mode."""
        if not super().available:
            return False
        data = self.coordinator.data or {}
        return str(data.get("mode", "")).lower() == "manual"

    @property
    def is_on(self) -> bool | None:
        value = (self.coordinator.data or {}).get(f"manual_{self._field}")
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await async_write_config(self.coordinator, {f"manual_{self._field}": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await async_write_config(self.coordinator, {f"manual_{self._field}": False})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    device_type = str(coordinator.info.get("device_type", ""))
    if not has_capability(coordinator, "config"):
        return

    entities: list[SwitchEntity] = [
        PicoRestSwitch(coordinator, description)
        for description in DEVICE_SWITCHES.get(device_type, ())
    ]
    if device_type == "pool_controller":
        entities.extend(
            (
                PoolManualActorSwitch(coordinator, "pump", "Pumpe manuell"),
                PoolManualActorSwitch(coordinator, "valve", "Ventil manuell"),
            )
        )

    async_add_entities(entities)
