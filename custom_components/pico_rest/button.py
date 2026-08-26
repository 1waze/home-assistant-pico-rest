"""Button platform for Pico REST maintenance actions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .api import PicoRestError
from .control import has_capability
from .entity import PicoRestEntity


class PicoActionButton(PicoRestEntity, ButtonEntity):
    """Base class for one Pico REST maintenance action."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator,
        key: str,
        name: str,
        action: Callable[[], Awaitable[dict]],
    ) -> None:
        super().__init__(coordinator, key)
        self._attr_name = name
        self._action = action

    async def async_press(self) -> None:
        try:
            await self._action()
        except PicoRestError as err:
            raise HomeAssistantError(f"Pico REST action failed: {err}") from err


class PicoRebootButton(PicoActionButton):
    """Reboot a Pico REST device."""

    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, coordinator) -> None:
        super().__init__(
            coordinator,
            "reboot",
            "Neustart",
            coordinator.client.async_reboot,
        )


class PicoRollbackButton(PicoActionButton):
    """Rollback to the previous Pico firmware."""

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        super().__init__(
            coordinator,
            "rollback",
            "Firmware-Rollback",
            coordinator.client.async_rollback,
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities: list[ButtonEntity] = []

    if has_capability(coordinator, "reboot"):
        entities.append(PicoRebootButton(coordinator))
    if has_capability(coordinator, "rollback"):
        entities.append(PicoRollbackButton(coordinator))
    async_add_entities(entities)
