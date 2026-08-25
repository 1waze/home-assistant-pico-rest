"""Sensor platform for Pico REST."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PicoRestConfigEntry
from .const import WEEKDAYS
from .entity import PicoRestEntity

ValueFn = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, kw_only=True)
class PicoSensorDescription(SensorEntityDescription):
    """Describe a Pico REST sensor."""

    value_fn: ValueFn


def _path(*keys: str) -> ValueFn:
    def value(data: dict[str, Any]) -> Any:
        current: Any = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    return value


def _free_mem(data: dict[str, Any]) -> int | None:
    """Return free memory as an integer byte value."""
    raw = data.get("free_mem")
    return int(raw) if raw is not None else None


COMMON_DIAGNOSTIC = (
    PicoSensorDescription(
        key="ip",
        name="IP-Adresse",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_path("ip"),
    ),
    PicoSensorDescription(
        key="wifi_rssi",
        name="WLAN Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_path("wifi_rssi"),
    ),
    PicoSensorDescription(
        key="free_mem",
        name="Freier Speicher",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_free_mem,
    ),
)

DEVICE_SENSORS: dict[str, tuple[PicoSensorDescription, ...]] = {
    "pool_controller": (
        PicoSensorDescription(
            key="t_pool",
            name="Pooltemperatur",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            value_fn=_path("t_pool"),
        ),
        PicoSensorDescription(
            key="t_collector",
            name="Kollektortemperatur",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            value_fn=_path("t_collector"),
        ),
        PicoSensorDescription(
            key="t_cpu",
            name="CPU-Temperatur",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("t_cpu"),
        ),
        PicoSensorDescription(
            key="mode",
            name="Betriebsmodus",
            value_fn=_path("mode"),
        ),
        PicoSensorDescription(
            key="wifi_quality",
            name="WLAN Qualität",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_quality"),
        ),
        PicoSensorDescription(
            key="wifi_reconnects",
            name="WLAN Reconnects",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_reconnects"),
        ),
        PicoSensorDescription(
            key="wifi_interface_resets",
            name="WLAN Interface-Resets",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_interface_resets"),
        ),
        PicoSensorDescription(
            key="wifi_offline_sec",
            name="WLAN Offlinezeit",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_offline_sec"),
        ),
    ),
    "led_controller": (
        PicoSensorDescription(key="effect", name="Effekt", value_fn=_path("effect")),
        PicoSensorDescription(
            key="effect_speed",
            name="Effektgeschwindigkeit",
            value_fn=_path("effect_speed"),
        ),
        PicoSensorDescription(
            key="effect_intensity",
            name="Effektintensität",
            value_fn=_path("effect_intensity"),
        ),
        PicoSensorDescription(
            key="two_color_split",
            name="Zweifarben-Aufteilung",
            value_fn=_path("two_color_split"),
        ),
        PicoSensorDescription(
            key="elevator_state",
            name="Aufzugstatus",
            value_fn=_path("elevator_state"),
        ),
        PicoSensorDescription(
            key="elevator_effect",
            name="Aufzug-Effekt",
            value_fn=_path("elevator_effect"),
        ),
        PicoSensorDescription(
            key="elevator_speed",
            name="Aufzug-Geschwindigkeit",
            value_fn=_path("elevator_speed"),
        ),
    ),
    "elevator_monitor": (
        PicoSensorDescription(key="state", name="Status", value_fn=_path("state")),
        PicoSensorDescription(
            key="gpio_up",
            name="GPIO Auf",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("gpio", "up"),
        ),
        PicoSensorDescription(
            key="gpio_down",
            name="GPIO Ab",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("gpio", "down"),
        ),
        PicoSensorDescription(
            key="wifi_reconnects",
            name="WLAN Reconnects",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_reconnects"),
        ),
        PicoSensorDescription(
            key="wifi_interface_resets",
            name="WLAN Interface-Resets",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_interface_resets"),
        ),
        PicoSensorDescription(
            key="wifi_offline_sec",
            name="WLAN Offlinezeit",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_offline_sec"),
        ),
    ),
    "sun_wind_monitor": (
        PicoSensorDescription(key="wind", name="Wind", value_fn=_path("wind")),
        PicoSensorDescription(key="hell", name="Helligkeit", value_fn=_path("hell")),
        PicoSensorDescription(
            key="cpu",
            name="CPU-Temperatur",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("cpu"),
        ),
        PicoSensorDescription(
            key="uptime_ms",
            name="Uptime",
            native_unit_of_measurement="ms",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("uptime_ms"),
        ),
    ),
    "pool_sensor_monitor": (
        PicoSensorDescription(
            key="sensor_count",
            name="Sensoranzahl",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("sensor_count"),
        ),
        PicoSensorDescription(
            key="uptime_sec",
            name="Uptime",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("uptime_sec"),
        ),
        PicoSensorDescription(
            key="wifi_reconnects",
            name="WLAN Reconnects",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_reconnects"),
        ),
        PicoSensorDescription(
            key="wifi_interface_resets",
            name="WLAN Interface-Resets",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_interface_resets"),
        ),
        PicoSensorDescription(
            key="wifi_offline_sec",
            name="WLAN Offlinezeit",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_path("wifi_offline_sec"),
        ),
    ),
}


class PicoInfoSensor(PicoRestEntity, SensorEntity):
    """Diagnostic value sourced from /api/info."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, key: str, name: str) -> None:
        super().__init__(coordinator, f"info_{key}")
        self._info_key = key
        self._attr_name = name

    @property
    def native_value(self) -> Any:
        """Return a value from the most recently validated device info."""
        return self.coordinator.info.get(self._info_key)


class PicoLastContactSensor(PicoRestEntity, SensorEntity):
    """Diagnostic timestamp of the last successful poll."""

    _attr_name = "Letzter erfolgreicher Kontakt"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "last_successful_contact")

    @property
    def available(self) -> bool:
        """Keep this diagnostic available after the Pico goes offline."""
        return self.coordinator.last_successful_update is not None

    @property
    def native_value(self):
        """Return the last successful coordinator update."""
        return self.coordinator.last_successful_update


class PicoRestSensor(PicoRestEntity, SensorEntity):
    """Generic sensor backed by one key in coordinator data."""

    entity_description: PicoSensorDescription

    def __init__(self, coordinator, description: PicoSensorDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the native sensor value."""
        return self.entity_description.value_fn(self.coordinator.data or {})


class LedScheduleSensor(PicoRestEntity, SensorEntity):
    """One read-only value from the LED controller weekly schedule."""

    def __init__(self, coordinator, day_key: str, day_name: str, field: str) -> None:
        """Initialize a weekly schedule sensor."""
        key = f"schedule_{day_key}_{field}"
        super().__init__(coordinator, key)
        self._day_key = day_key
        self._field = field
        field_names = {
            "on": "Einschaltzeit",
            "off": "Ausschaltzeit",
            "effect": "Effekt",
        }
        self._attr_name = f"{day_name} {field_names[field]}"

    @property
    def native_value(self) -> Any:
        """Return the configured schedule value."""
        config = (self.coordinator.data or {}).get("_config", {})
        if not isinstance(config, dict):
            return None
        days = config.get("days", {})
        if not isinstance(days, dict):
            return None
        day = days.get(self._day_key, {})
        if not isinstance(day, dict):
            return None
        return day.get(self._field)


class PoolProbeSensor(PicoRestEntity, SensorEntity):
    """One metric from one pool distance sensor."""

    def __init__(self, coordinator, index: int, sensor_id: str, metric: str) -> None:
        """Initialize a pool probe sensor."""
        key = f"probe_{index}_{metric}"
        super().__init__(coordinator, key)
        self._index = index
        self._metric = metric
        metric_names = {
            "dist": "Distanz",
            "strength": "Signalstärke",
            "temp": "Temperatur",
        }
        self._attr_name = f"{sensor_id} {metric_names[metric]}"
        if metric == "temp":
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> Any:
        """Return the current probe metric value."""
        sensors = (self.coordinator.data or {}).get("sensors", [])
        if not isinstance(sensors, list) or self._index >= len(sensors):
            return None
        item = sensors[self._index]
        return item.get(self._metric) if isinstance(item, dict) else None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PicoRestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pico REST sensors."""
    coordinator = entry.runtime_data.coordinator
    device_type = str(coordinator.info.get("device_type", ""))
    descriptions = DEVICE_SENSORS.get(device_type, ()) + COMMON_DIAGNOSTIC
    entities: list[SensorEntity] = [
        PicoInfoSensor(coordinator, "api_version", "API-Version"),
        PicoInfoSensor(coordinator, "firmware", "Firmware"),
        PicoLastContactSensor(coordinator),
    ]
    entities.extend(
        PicoRestSensor(coordinator, description) for description in descriptions
    )

    if device_type == "led_controller":
        config = (coordinator.data or {}).get("_config", {})
        days = config.get("days", {}) if isinstance(config, dict) else {}
        if isinstance(days, dict):
            for day_key, day_name in WEEKDAYS:
                if isinstance(days.get(day_key), dict):
                    for field in ("on", "off", "effect"):
                        entities.append(
                            LedScheduleSensor(coordinator, day_key, day_name, field)
                        )

    if device_type == "pool_sensor_monitor":
        sensors = (coordinator.data or {}).get("sensors", [])
        if isinstance(sensors, list):
            for index, item in enumerate(sensors):
                if not isinstance(item, dict):
                    continue
                sensor_id = str(item.get("id") or f"Sensor {index + 1}")
                for metric in ("dist", "strength", "temp"):
                    entities.append(PoolProbeSensor(coordinator, index, sensor_id, metric))

    async_add_entities(entities)
