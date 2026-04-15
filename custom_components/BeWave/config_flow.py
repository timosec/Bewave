"""Config flow for BeWave."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import (
    CONF_COMMAND_ON,
    CONF_DEVICES,
    CONF_LISTEN_PORT,
    CONF_OFF_MESSAGE,
    CONF_ON_MESSAGE,
    DEFAULT_LISTEN_PORT,
    DOMAIN,
)
from .models import devices_to_storage_dicts, normalize_device

ACTION_ADD = "add"
ACTION_EDIT = "edit"
ACTION_DELETE = "delete"
ACTION_FINISH = "finish"


def _menu_choices(*, allow_finish: bool, allow_edit: bool, allow_delete: bool) -> dict[str, str]:
    choices: dict[str, str] = {
        ACTION_ADD: "Zone toevoegen",
    }
    if allow_edit:
        choices[ACTION_EDIT] = "Zone wijzigen"
    if allow_delete:
        choices[ACTION_DELETE] = "Zone verwijderen"
    if allow_finish:
        choices[ACTION_FINISH] = "Opslaan en afronden"
    return choices


def _menu_schema(*, allow_finish: bool, allow_edit: bool, allow_delete: bool) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("action", default=ACTION_ADD): vol.In(
                _menu_choices(
                    allow_finish=allow_finish,
                    allow_edit=allow_edit,
                    allow_delete=allow_delete,
                )
            )
        }
    )


def _select_device_schema(devices: list[dict[str, Any]]) -> vol.Schema:
    options = {str(device["id"]): f"{device['name']} ({device['id']})" for device in devices}
    return vol.Schema({vol.Required("device_id"): vol.In(options)})


def _device_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    suggested_id = str(defaults.get("id", "") or "1")
    return vol.Schema(
        {
            vol.Required("id", default=suggested_id): str,
            vol.Required("name", default=defaults.get("name", "")): str,
            vol.Required(
                CONF_COMMAND_ON,
                default=defaults.get(CONF_COMMAND_ON, defaults.get("commandOn", "")),
            ): str,
            vol.Optional(
                CONF_ON_MESSAGE,
                default=defaults.get(CONF_ON_MESSAGE, defaults.get("onMessage", "")),
            ): str,
            vol.Optional(
                CONF_OFF_MESSAGE,
                default=defaults.get(CONF_OFF_MESSAGE, defaults.get("offMessage", "")),
            ): str,
            vol.Required(
                CONF_LISTEN_PORT,
                default=int(
                    defaults.get(
                        CONF_LISTEN_PORT,
                        defaults.get("listenPort", DEFAULT_LISTEN_PORT),
                    )
                ),
            ): vol.Coerce(int),
        }
    )


class BeWaveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BeWave."""

    VERSION = 3

    def __init__(self) -> None:
        self._host = ""
        self._devices: list[dict[str, Any]] = []
        self._edit_device_id: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST].strip()
            if not self._host:
                errors["base"] = "invalid_host"
            else:
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()
                return await self.async_step_device_menu()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST, default=self._host): str}),
            errors=errors,
        )

    async def async_step_device_menu(self, user_input: dict[str, Any] | None = None):
        """Choose what to do with zones during setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input["action"]
            if action == ACTION_ADD:
                return await self.async_step_add_device()
            if action == ACTION_FINISH:
                if not self._devices:
                    errors["base"] = "at_least_one_device"
                else:
                    return self.async_create_entry(
                        title=f"BeWave ({self._host})",
                        data={CONF_HOST: self._host, CONF_DEVICES: self._devices},
                    )

        return self.async_show_form(
            step_id="device_menu",
            data_schema=_menu_schema(
                allow_finish=bool(self._devices),
                allow_edit=False,
                allow_delete=False,
            ),
            errors=errors,
            description_placeholders={"zone_count": str(len(self._devices))},
        )

    async def async_step_add_device(self, user_input: dict[str, Any] | None = None):
        """Add a zone during initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                device = normalize_device(user_input, len(self._devices) + 1)
                if any(str(existing["id"]) == device.id for existing in self._devices):
                    raise ValueError("Device id bestaat al")
                self._devices.append(devices_to_storage_dicts([device])[0])
                return await self.async_step_device_menu()
            except ValueError:
                errors["base"] = "invalid_device"

        suggested_id = str(len(self._devices) + 1)
        return self.async_show_form(
            step_id="add_device",
            data_schema=_device_schema(
                {
                    "id": suggested_id,
                    CONF_LISTEN_PORT: DEFAULT_LISTEN_PORT,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return BeWaveOptionsFlow()


class BeWaveOptionsFlow(config_entries.OptionsFlowWithReload):
    """BeWave options flow."""

    def __init__(self) -> None:
        self._devices: list[dict[str, Any]] = []
        self._edit_device_id: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage BeWave zones."""
        if not self._devices:
            self._devices = list(
                self.config_entry.options.get(
                    CONF_DEVICES, self.config_entry.data.get(CONF_DEVICES, [])
                )
            )

        if user_input is not None:
            action = user_input["action"]
            if action == ACTION_ADD:
                return await self.async_step_add_device()
            if action == ACTION_EDIT:
                return await self.async_step_select_edit_device()
            if action == ACTION_DELETE:
                return await self.async_step_select_delete_device()
            if action == ACTION_FINISH:
                return self.async_create_entry(title="", data={CONF_DEVICES: self._devices})

        return self.async_show_form(
            step_id="init",
            data_schema=_menu_schema(
                allow_finish=True,
                allow_edit=bool(self._devices),
                allow_delete=bool(self._devices),
            ),
            description_placeholders={"zone_count": str(len(self._devices))},
        )

    async def async_step_add_device(self, user_input: dict[str, Any] | None = None):
        """Add a zone from options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                device = normalize_device(user_input, len(self._devices) + 1)
                if any(str(existing["id"]) == device.id for existing in self._devices):
                    raise ValueError("Device id bestaat al")
                self._devices.append(devices_to_storage_dicts([device])[0])
                return await self.async_step_init()
            except ValueError:
                errors["base"] = "invalid_device"

        suggested_id = str(len(self._devices) + 1)
        return self.async_show_form(
            step_id="add_device",
            data_schema=_device_schema(
                {
                    "id": suggested_id,
                    CONF_LISTEN_PORT: DEFAULT_LISTEN_PORT,
                }
            ),
            errors=errors,
        )

    async def async_step_select_edit_device(self, user_input: dict[str, Any] | None = None):
        """Choose a zone to edit."""
        if user_input is not None:
            self._edit_device_id = user_input["device_id"]
            return await self.async_step_edit_device()

        return self.async_show_form(
            step_id="select_edit_device",
            data_schema=_select_device_schema(self._devices),
        )

    async def async_step_edit_device(self, user_input: dict[str, Any] | None = None):
        """Edit a selected zone."""
        errors: dict[str, str] = {}
        selected = next((item for item in self._devices if str(item["id"]) == self._edit_device_id), None)
        if selected is None:
            return await self.async_step_init()

        if user_input is not None:
            try:
                device = normalize_device(user_input, 1)
                if device.id != self._edit_device_id and any(
                    str(existing["id"]) == device.id for existing in self._devices
                ):
                    raise ValueError("Device id bestaat al")
                replacement = devices_to_storage_dicts([device])[0]
                self._devices = [
                    replacement if str(item["id"]) == self._edit_device_id else item
                    for item in self._devices
                ]
                self._edit_device_id = None
                return await self.async_step_init()
            except ValueError:
                errors["base"] = "invalid_device"

        return self.async_show_form(
            step_id="edit_device",
            data_schema=_device_schema(selected),
            errors=errors,
        )

    async def async_step_select_delete_device(self, user_input: dict[str, Any] | None = None):
        """Choose a zone to delete."""
        if user_input is not None:
            device_id = user_input["device_id"]
            self._devices = [item for item in self._devices if str(item["id"]) != device_id]
            return await self.async_step_init()

        return self.async_show_form(
            step_id="select_delete_device",
            data_schema=_select_device_schema(self._devices),
        )
