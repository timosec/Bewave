"""Binary sensor platform for BeWave."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import BeWaveBaseEntity
from .tcp import BeWaveHub

BeWaveConfigEntry = ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BeWaveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BeWave zone status entities."""
    hub: BeWaveHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BeWaveZoneStatusBinarySensor(hub, hub.get_device(device.id))
        for device in hub.devices
        if device.has_feedback
    )


class BeWaveZoneStatusBinarySensor(BeWaveBaseEntity, BinarySensorEntity):
    """Read-only zone status driven by BeWave feedback messages."""

    _attr_name = "Status"

    def __init__(self, hub: BeWaveHub, device) -> None:
        super().__init__(hub, device)
        self._attr_unique_id = f"bewave_{hub.host}_{self._device.unique_id}_status"
        self._attr_is_on = hub.get_state(device.id)
        self._unsubscribe: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""

        @callback
        def _handle_state(new_state: bool) -> None:
            self._attr_is_on = new_state
            self.async_write_ha_state()

        self._unsubscribe = self._hub.subscribe(self._device.id, _handle_state)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def icon(self) -> str:
        """Return an icon based on the current state."""
        return "mdi:toggle-switch" if self.is_on else "mdi:toggle-switch-off-outline"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose BeWave feedback mapping for debugging."""
        return {
            "bewave_feedback_on": self._device.on_message,
            "bewave_feedback_off": self._device.off_message,
            "bewave_listen_port": self._device.listen_port,
        }
