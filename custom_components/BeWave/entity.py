"""Shared entity helpers for BeWave."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .models import BeWaveDevice
from .tcp import BeWaveHub


class BeWaveBaseEntity(Entity):
    """Base BeWave entity bound to a single configured zone."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: BeWaveHub, device: BeWaveDevice) -> None:
        self._hub = hub
        self._device = device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{hub.host}_{device.unique_id}")},
            manufacturer="BeWave",
            model="Zone",
            name=device.name,
        )
