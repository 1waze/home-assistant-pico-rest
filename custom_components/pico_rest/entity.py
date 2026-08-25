"""Base entity for Pico REST."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PicoRestCoordinator


class PicoRestEntity(CoordinatorEntity[PicoRestCoordinator]):
    """Base entity for a Pico REST device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PicoRestCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        info = coordinator.info
        device_id = coordinator.device_id
        device_type = str(info.get("device_type", "pico"))

        self._attr_unique_id = f"{device_id}:{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=str(info.get("device_name") or device_type),
            manufacturer=str(info.get("manufacturer") or "HSZ-IT"),
            model=str(info.get("hardware") or "Raspberry Pi Pico W"),
            serial_number=device_id,
            sw_version=str(info.get("firmware") or "unknown"),
            configuration_url=coordinator.client.base_url,
        )
