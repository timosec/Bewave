"""Button platform for BeWave."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import BeWaveBaseEntity
from .tcp import BeWaveHub

_LOGGER = logging.getLogger(__name__)

BeWaveConfigEntry = ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BeWaveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BeWave button entities."""
    hub: BeWaveHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(BeWaveTriggerButton(hub, hub.get_device(device.id)) for device in hub.devices)


class BeWaveTriggerButton(BeWaveBaseEntity, ButtonEntity):
    """Button that sends the configured BeWave command."""

    _attr_name = "Trigger"
    _attr_icon = "mdi:gesture-tap-button"

    def __init__(self, hub: BeWaveHub, device) -> None:
        super().__init__(hub, device)
        self._attr_unique_id = f"bewave_{hub.host}_{self._device.unique_id}_trigger"

    async def async_press(self) -> None:
        """Send the configured trigger command to BeWave."""
        _LOGGER.info(
            "BeWave knop %s sending command: %s",
            self._device.name,
            self._device.command_on,
        )
        await self._hub.async_send_command(self._device.command_on)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose BeWave config for debugging."""
        return {
            "bewave_command_on": self._device.command_on,
            "bewave_has_feedback": self._device.has_feedback,
            "bewave_listen_port": self._device.listen_port,
        }
