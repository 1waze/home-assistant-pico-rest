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


def _normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    host = (
        data[CONF_HOST]
        .strip()
        .removeprefix("http://")
        .removeprefix("https://")
        .rstrip("/")
    )
    return {
        CONF_HOST: host,
        CONF_PORT: data.get(CONF_PORT, DEFAULT_PORT),
    }


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


def _schema(host: str | None = None, port: int = DEFAULT_PORT) -> vol.Schema:
    host_field = vol.Required(CONF_HOST, default=host) if host else vol.Required(CONF_HOST)
    return vol.Schema(
        {
            host_field: str,
            vol.Optional(CONF_PORT, default=port): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
        }
    )


class PicoRestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pico REST."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Set up a Pico REST device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = _normalize_input(user_input)
            try:
                info = await _validate_input(self.hass, user_input)
            except PicoRestConnectionError:
                errors["base"] = "cannot_connect"
            except PicoRestInvalidResponse:
                errors["base"] = "unsupported_device"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                device_id = str(info["device_id"])
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    }
                )
                title = str(
                    info.get("device_name") or info.get("device_type") or device_id
                )
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Allow changing the network address without recreating the device."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = _normalize_input(user_input)
            try:
                info = await _validate_input(self.hass, user_input)
            except PicoRestConnectionError:
                errors["base"] = "cannot_connect"
            except PicoRestInvalidResponse:
                errors["base"] = "unsupported_device"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(info["device_id"]))
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(
                str(entry.data[CONF_HOST]),
                int(entry.data.get(CONF_PORT, DEFAULT_PORT)),
            ),
            errors=errors,
        )
