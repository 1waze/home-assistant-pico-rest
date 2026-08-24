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
        host = coordinator.client.host
        device_type = str(info.get("device_type", "pico"))

        # Temporary identifier until Pico REST API exposes a stable hardware UID.
        device_identifier = f"{device_type}:{host}"
        self._attr_unique_id = f"{device_identifier}:{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_identifier)},
            name=str(info.get("device_name") or device_type),
            manufacturer=str(info.get("manufacturer") or "HSZ-IT"),
            model=str(info.get("hardware") or "Raspberry Pi Pico W"),
            sw_version=str(info.get("firmware") or "unknown"),
            configuration_url=coordinator.client.base_url,
        )
