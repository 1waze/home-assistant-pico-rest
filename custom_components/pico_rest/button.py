"""Button platform for Pico REST maintenance actions."""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .entity import PicoRestEntity


class PicoRebootButton(PicoRestEntity, ButtonEntity):
    """Reboot a Pico REST device."""

    _attr_name = "Neustart"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "reboot")

    async def async_press(self) -> None:
        await self.coordinator.client.async_reboot()
        # Device becomes unavailable briefly; do not force an immediate refresh.


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    capabilities = coordinator.info.get("capabilities", [])
    if isinstance(capabilities, list) and "reboot" in capabilities:
        async_add_entities([PicoRebootButton(coordinator)])
