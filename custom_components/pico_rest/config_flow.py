"""Config flow for Pico REST."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PicoRestClient, PicoRestConnectionError, PicoRestInvalidResponse
from .const import DEFAULT_PORT, DOMAIN, SUPPORTED_DEVICE_TYPES


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    client = PicoRestClient(
        async_get_clientsession(hass),
        data[CONF_HOST],
        data.get(CONF_PORT, DEFAULT_PORT),
    )
    info = await client.async_get_info()
    device_type = info.get("device_type")
    if device_type not in SUPPORTED_DEVICE_TYPES:
        raise PicoRestInvalidResponse(f"Unsupported device type: {device_type}")
    return info


class PicoRestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pico REST."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip().removeprefix("http://").removeprefix("https://").rstrip("/")
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            user_input = {CONF_HOST: host, CONF_PORT: port}

            # Pico REST API v1 currently has no hardware UID. Prevent duplicate
            # entries by host until the protocol exposes a stable device ID.
            for entry in self._async_current_entries():
                if (
                    entry.data.get(CONF_HOST) == host
                    and entry.data.get(CONF_PORT, DEFAULT_PORT) == port
                ):
                    return self.async_abort(reason="already_configured")

            try:
                info = await _validate_input(self.hass, user_input)
            except PicoRestConnectionError:
                errors["base"] = "cannot_connect"
            except PicoRestInvalidResponse:
                errors["base"] = "unsupported_device"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                title = str(info.get("device_name") or info.get("device_type") or host)
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
