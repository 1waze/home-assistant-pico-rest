"""Frontend panel and websocket API for Pico REST LED colors."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.frontend import add_extra_js_url, async_panel_exists
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, WEEKDAYS
from .control import async_write_config, config_value

PANEL_URL = "pico-rest-colors"
STATIC_URL = "/pico_rest_static"
PANEL_ELEMENT = "pico-rest-color-panel"

LED_GLOBAL_CONFIG_KEYS = (
    "brightness",
    "effect",
    "effect_speed",
    "effect_intensity",
    "effect_delay_ms",
    "color1",
    "color2",
    "two_color_split",
    "use_sunset",
    "latitude",
    "longitude",
    "timezone",
    "elevator_url",
    "elevator_effect",
    "elevator_speed",
    "elevator_delay_ms",
    "elevator_poll_seconds",
    "special_mode",
    "led_pin",
    "led_count",
)

LED_EFFECTS = {
    "solid",
    "two_color",
    "rainbow",
    "pulse",
    "theater",
    "scanner",
    "sparkle",
    "matrix",
    "chevrons",
}
LED_ELEVATOR_EFFECTS = {"chevrons", "scanner", "theater"}


def _rgb(value: Any) -> list[int]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return [0, 0, 0]
    try:
        return [max(0, min(255, int(component))) for component in value]
    except (TypeError, ValueError):
        return [0, 0, 0]


def _led_entries(hass: HomeAssistant):
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            continue
        coordinator = runtime.coordinator
        if str(coordinator.info.get("device_type", "")) == "led_controller":
            yield entry, coordinator


def _global_config(coordinator) -> dict[str, Any]:
    config = (coordinator.data or {}).get("_config", {})
    if not isinstance(config, dict):
        return {}
    return {key: config.get(key) for key in LED_GLOBAL_CONFIG_KEYS if key in config}


def _validated_global_value(key: str, value: Any) -> Any:
    if key in {"use_sunset", "special_mode"}:
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be boolean")
        return value

    if key in {"effect", "elevator_effect", "timezone", "elevator_url"}:
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        value = value.strip()
        if key == "effect" and value not in LED_EFFECTS:
            raise ValueError("unsupported effect")
        if key == "elevator_effect" and value not in LED_ELEVATOR_EFFECTS:
            raise ValueError("unsupported elevator effect")
        if key in {"timezone", "elevator_url"} and not value:
            raise ValueError(f"{key} must not be empty")
        return value

    try:
        numeric = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"{key} must be numeric") from err

    ranges: dict[str, tuple[float, float]] = {
        "brightness": (0.0, 1.0),
        "effect_speed": (1.0, 20.0),
        "effect_intensity": (0.0, 1.0),
        "effect_delay_ms": (0.0, 1000.0),
        "two_color_split": (0.0, 1.0),
        "latitude": (-90.0, 90.0),
        "longitude": (-180.0, 180.0),
        "elevator_speed": (1.0, 20.0),
        "elevator_delay_ms": (0.0, 1000.0),
        "elevator_poll_seconds": (0.2, 60.0),
        "led_pin": (0.0, 29.0),
        "led_count": (1.0, 5000.0),
    }
    low, high = ranges[key]
    if not low <= numeric <= high:
        raise ValueError(f"{key} must be between {low:g} and {high:g}")
    if key in {
        "effect_speed",
        "effect_delay_ms",
        "elevator_speed",
        "elevator_delay_ms",
        "led_pin",
        "led_count",
    }:
        return int(round(numeric))
    return numeric


@websocket_api.websocket_command({vol.Required("type"): "pico_rest/led_colors"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_led_colors(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all configured LED colors."""
    devices = []
    for entry, coordinator in _led_entries(hass):
        colors = {
            "color1": _rgb(config_value(coordinator, "color1")),
            "color2": _rgb(config_value(coordinator, "color2")),
        }
        for day_key, _day_name in WEEKDAYS:
            colors[f"day_{day_key}"] = _rgb(
                config_value(coordinator, "days", day_key, "color")
            )
        devices.append(
            {
                "entry_id": entry.entry_id,
                "name": str(
                    coordinator.info.get("device_name") or "Pico REST LED-Steuerung"
                ),
                "available": coordinator.last_update_success,
                "colors": colors,
                "config": _global_config(coordinator),
                "elevator_state": coordinator.data.get("elevator_state"),
                "days": {
                    day_key: {
                        "on": config_value(coordinator, "days", day_key, "on"),
                        "off": config_value(coordinator, "days", day_key, "off"),
                        "effect": config_value(coordinator, "days", day_key, "effect"),
                        "color": _rgb(
                            config_value(coordinator, "days", day_key, "color")
                        ),
                    }
                    for day_key, _day_name in WEEKDAYS
                },
            }
        )
    connection.send_result(msg["id"], devices)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "pico_rest/set_led_color",
        vol.Required("entry_id"): str,
        vol.Required("target"): vol.In(
            ["color1", "color2", *(f"day_{day}" for day, _name in WEEKDAYS)]
        ),
        vol.Required("rgb"): vol.All(
            [vol.All(vol.Coerce(int), vol.Range(min=0, max=255))], vol.Length(min=3, max=3)
        ),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_set_led_color(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Write one LED RGB configuration value."""
    selected = None
    for entry, coordinator in _led_entries(hass):
        if entry.entry_id == msg["entry_id"]:
            selected = coordinator
            break
    if selected is None:
        connection.send_error(msg["id"], "not_found", "LED controller not found")
        return

    rgb = list(msg["rgb"])
    target = msg["target"]
    if target in ("color1", "color2"):
        patch = {target: rgb}
    else:
        day_key = target.removeprefix("day_")
        patch = {"days": {day_key: {"color": rgb}}}

    try:
        await async_write_config(selected, patch)
    except Exception as err:  # HomeAssistantError is serialized for the frontend here.
        connection.send_error(msg["id"], "write_failed", str(err))
        return

    connection.send_result(msg["id"], {"rgb": rgb})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "pico_rest/set_led_config",
        vol.Required("entry_id"): str,
        vol.Required("key"): vol.In(LED_GLOBAL_CONFIG_KEYS),
        vol.Required("value"): vol.Any(bool, int, float, str),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_set_led_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Update one global LED configuration value."""
    selected = None
    for entry, coordinator in _led_entries(hass):
        if entry.entry_id == msg["entry_id"]:
            selected = coordinator
            break
    if selected is None:
        connection.send_error(msg["id"], "not_found", "LED controller not found")
        return

    key = msg["key"]
    if key in {"color1", "color2"}:
        connection.send_error(
            msg["id"],
            "invalid_format",
            "Use pico_rest/set_led_color for RGB values",
        )
        return
    try:
        value = _validated_global_value(key, msg["value"])
        await async_write_config(selected, {key: value})
    except (ValueError, TypeError) as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    except Exception as err:
        connection.send_error(msg["id"], "write_failed", str(err))
        return

    connection.send_result(msg["id"], {"key": key, "value": value})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "pico_rest/set_led_day",
        vol.Required("entry_id"): str,
        vol.Required("day"): vol.In([day for day, _name in WEEKDAYS]),
        vol.Optional("on"): vol.Match(r"^(?:[01]\d|2[0-3]):[0-5]\d$"),
        vol.Optional("off"): vol.Match(r"^(?:[01]\d|2[0-3]):[0-5]\d$"),
        vol.Optional("effect"): str,
        vol.Optional("color"): vol.All(
            [vol.All(vol.Coerce(int), vol.Range(min=0, max=255))],
            vol.Length(min=3, max=3),
        ),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_set_led_day(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Update one or more settings for one LED weekday."""
    selected = None
    for entry, coordinator in _led_entries(hass):
        if entry.entry_id == msg["entry_id"]:
            selected = coordinator
            break
    if selected is None:
        connection.send_error(msg["id"], "not_found", "LED controller not found")
        return

    day_patch: dict[str, Any] = {}
    for key in ("on", "off", "effect"):
        if key in msg:
            day_patch[key] = msg[key]
    if "color" in msg:
        day_patch["color"] = list(msg["color"])
    if not day_patch:
        connection.send_error(msg["id"], "invalid_format", "No values to update")
        return

    try:
        await async_write_config(selected, {"days": {msg["day"]: day_patch}})
    except Exception as err:
        connection.send_error(msg["id"], "write_failed", str(err))
        return

    connection.send_result(msg["id"], {"day": msg["day"], **day_patch})


POOL_CONFIG_KEYS = (
    "target_temp",
    "diff_on",
    "diff_off",
    "mode",
    "clean_mode",
    "pump_on",
    "pump_off",
)


def _pool_entries(hass: HomeAssistant):
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            continue
        coordinator = runtime.coordinator
        if str(coordinator.info.get("device_type", "")) == "pool_controller":
            yield entry, coordinator


def _pool_config(coordinator) -> dict[str, Any]:
    config = (coordinator.data or {}).get("_config", {})
    if not isinstance(config, dict):
        return {}
    return {key: config.get(key) for key in POOL_CONFIG_KEYS if key in config}


def _validated_pool_value(key: str, value: Any) -> Any:
    if key in {"clean_mode", "manual_pump", "manual_valve"}:
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be boolean")
        return value
    if key == "mode":
        if value not in {"auto", "manual"}:
            raise ValueError("mode must be auto or manual")
        return value
    if key in {"pump_on", "pump_off"}:
        if not isinstance(value, str) or not re.match(
            r"^(?:[01]\d|2[0-3]):[0-5]\d$", value
        ):
            raise ValueError(f"{key} must be HH:MM")
        return value
    if key in {"target_temp", "diff_on", "diff_off"}:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as err:
            raise ValueError(f"{key} must be numeric") from err
        low, high = {
            "target_temp": (5.0, 40.0),
            "diff_on": (0.0, 30.0),
            "diff_off": (0.0, 30.0),
        }[key]
        if not low <= numeric <= high:
            raise ValueError(f"{key} must be between {low:g} and {high:g}")
        return numeric
    raise ValueError("unsupported pool configuration key")


@websocket_api.websocket_command({vol.Required("type"): "pico_rest/pool_state"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_pool_state(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return pool controller state, config and history entity ids."""
    registry = er.async_get(hass)
    devices = []
    for entry, coordinator in _pool_entries(hass):
        data = dict(coordinator.data or {})
        data.pop("_config", None)

        entity_ids: dict[str, str | None] = {
            "t_pool": None,
            "t_collector": None,
            "valve": None,
        }
        for registry_entry in er.async_entries_for_config_entry(
            registry, entry.entry_id
        ):
            unique_id = registry_entry.unique_id
            if registry_entry.domain == "sensor" and unique_id.endswith(":t_pool"):
                entity_ids["t_pool"] = registry_entry.entity_id
            elif (
                registry_entry.domain == "sensor"
                and unique_id.endswith(":t_collector")
            ):
                entity_ids["t_collector"] = registry_entry.entity_id
            elif (
                registry_entry.domain == "binary_sensor"
                and unique_id.endswith(":valve")
            ):
                entity_ids["valve"] = registry_entry.entity_id

        devices.append(
            {
                "entry_id": entry.entry_id,
                "name": str(
                    coordinator.info.get("device_name")
                    or "Pico REST Poolsteuerung"
                ),
                "available": coordinator.last_update_success,
                "status": data,
                "config": _pool_config(coordinator),
                "entity_ids": entity_ids,
            }
        )
    connection.send_result(msg["id"], devices)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "pico_rest/set_pool_value",
        vol.Required("entry_id"): str,
        vol.Required("key"): vol.In(
            [
                "target_temp",
                "diff_on",
                "diff_off",
                "mode",
                "clean_mode",
                "pump_on",
                "pump_off",
                "manual_pump",
                "manual_valve",
            ]
        ),
        vol.Required("value"): object,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_set_pool_value(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Write one pool controller configuration/control value."""
    selected = None
    for entry, coordinator in _pool_entries(hass):
        if entry.entry_id == msg["entry_id"]:
            selected = coordinator
            break
    if selected is None:
        connection.send_error(msg["id"], "not_found", "Pool controller not found")
        return
    key = msg["key"]
    try:
        value = _validated_pool_value(key, msg["value"])
        await async_write_config(selected, {key: value})
    except (ValueError, TypeError) as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    except Exception as err:
        connection.send_error(msg["id"], "write_failed", str(err))
        return
    connection.send_result(msg["id"], {"key": key, "value": value})


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Register Pico REST color panel and websocket commands."""
    websocket_api.async_register_command(hass, ws_led_colors)
    websocket_api.async_register_command(hass, ws_set_led_color)
    websocket_api.async_register_command(hass, ws_set_led_config)
    websocket_api.async_register_command(hass, ws_set_led_day)
    websocket_api.async_register_command(hass, ws_pool_state)
    websocket_api.async_register_command(hass, ws_set_pool_value)

    frontend_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(frontend_dir), False)]
    )
    add_extra_js_url(hass, f"{STATIC_URL}/pico-rest-day-card.js?v=0500")
    add_extra_js_url(hass, f"{STATIC_URL}/pico-rest-pool-card.js?v=0503")

    if not async_panel_exists(hass, PANEL_URL):
        await panel_custom.async_register_panel(
            hass=hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name=PANEL_ELEMENT,
            module_url=f"{STATIC_URL}/pico-rest-color-panel.js?v=042",
            sidebar_title="Pico REST Farben",
            sidebar_icon="mdi:palette",
            require_admin=True,
            config={},
        )
