"""Frontend panel and websocket API for Pico REST LED colors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.frontend import async_panel_exists
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, WEEKDAYS
from .control import async_write_config, config_value

PANEL_URL = "pico-rest-colors"
STATIC_URL = "/pico_rest_static"
PANEL_ELEMENT = "pico-rest-color-panel"


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
        for day_key, day_name in WEEKDAYS:
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


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Register Pico REST color panel and websocket commands."""
    websocket_api.async_register_command(hass, ws_led_colors)
    websocket_api.async_register_command(hass, ws_set_led_color)

    if async_panel_exists(hass, PANEL_URL):
        return

    frontend_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(frontend_dir), False)]
    )
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
