"""Models for the BeWave integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_COMMAND_ON,
    CONF_LISTEN_PORT,
    CONF_MOMENTARY_RESET_MS,
    CONF_OFF_MESSAGE,
    CONF_ON_MESSAGE,
    DEFAULT_LISTEN_PORT,
    DEFAULT_MOMENTARY_RESET_MS,
)


@dataclass(slots=True)
class BeWaveDevice:
    """Normalized device config."""

    id: str
    name: str
    command_on: str
    on_message: str | None = None
    off_message: str | None = None
    listen_port: int = DEFAULT_LISTEN_PORT
    momentary_reset_ms: int = DEFAULT_MOMENTARY_RESET_MS

    @property
    def has_feedback(self) -> bool:
        return bool(self.on_message and self.off_message)

    @property
    def unique_id(self) -> str:
        return self.id


def _pick(source: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in source:
            return source[name]
    return default


def normalize_device(raw: dict[str, Any], index: int) -> BeWaveDevice:
    """Normalize a raw device dict.

    Accept both Home Assistant style snake_case and legacy Homebridge style camelCase keys.
    """
    name = _pick(raw, "name")
    command_on = _pick(raw, CONF_COMMAND_ON, "commandOn")
    on_message = _pick(raw, CONF_ON_MESSAGE, "onMessage")
    off_message = _pick(raw, CONF_OFF_MESSAGE, "offMessage")
    listen_port = int(_pick(raw, CONF_LISTEN_PORT, "listenPort", default=DEFAULT_LISTEN_PORT))
    momentary_reset_ms = int(
        _pick(raw, CONF_MOMENTARY_RESET_MS, "momentaryResetMs", default=DEFAULT_MOMENTARY_RESET_MS)
    )
    raw_id = _pick(raw, "id", default=f"device_{index}")

    if isinstance(name, str):
        name = name.strip()
    if isinstance(command_on, str):
        command_on = command_on.strip()
    if isinstance(on_message, str):
        on_message = on_message.strip()
    if isinstance(off_message, str):
        off_message = off_message.strip()

    if not name or not isinstance(name, str):
        raise ValueError(f"Device {index}: 'name' is verplicht")
    if not command_on or not isinstance(command_on, str):
        raise ValueError(f"Device {index}: 'command_on' / 'commandOn' is verplicht")
    if (on_message and not off_message) or (off_message and not on_message):
        raise ValueError(
            f"Device {index}: gebruik zowel 'on_message' als 'off_message', of geen van beide"
        )

    return BeWaveDevice(
        id=str(raw_id),
        name=name,
        command_on=command_on,
        on_message=on_message,
        off_message=off_message,
        listen_port=listen_port,
        momentary_reset_ms=momentary_reset_ms,
    )


def devices_to_storage_dicts(devices: list[BeWaveDevice]) -> list[dict[str, Any]]:
    """Convert normalized devices to config entry storage."""
    return [
        {
            "id": device.id,
            "name": device.name,
            CONF_COMMAND_ON: device.command_on,
            CONF_ON_MESSAGE: device.on_message,
            CONF_OFF_MESSAGE: device.off_message,
            CONF_LISTEN_PORT: device.listen_port,
            CONF_MOMENTARY_RESET_MS: device.momentary_reset_ms,
        }
        for device in devices
    ]
