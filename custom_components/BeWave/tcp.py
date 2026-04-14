"""TCP runtime for BeWave."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections import defaultdict
from collections.abc import Callable

from homeassistant.core import HomeAssistant

from .const import DEFAULT_TARGET_PORT
from .models import BeWaveDevice

_LOGGER = logging.getLogger(__name__)


class BeWaveHub:
    """Runtime coordinator for BeWave."""

    def __init__(self, hass: HomeAssistant, host: str, devices: list[BeWaveDevice]) -> None:
        self.hass = hass
        self.host = host
        self.devices = devices
        self._servers: dict[int, asyncio.base_events.Server] = {}
        self._listeners: dict[str, list[Callable[[bool], None]]] = defaultdict(list)
        self._device_by_message_port: dict[tuple[int, str], BeWaveDevice] = {}
        self._device_by_id: dict[str, BeWaveDevice] = {device.id: device for device in devices}

        for device in devices:
            if device.has_feedback:
                assert device.on_message is not None
                assert device.off_message is not None
                self._device_by_message_port[(device.listen_port, device.on_message)] = device
                self._device_by_message_port[(device.listen_port, device.off_message)] = device

    async def async_start(self) -> None:
        """Start TCP listeners for feedback devices."""
        for port in {device.listen_port for device in self.devices if device.has_feedback}:
            if port in self._servers:
                continue
            server = await asyncio.start_server(self._handle_client, host="0.0.0.0", port=port)
            self._servers[port] = server
            _LOGGER.info("BeWave luistert op TCP poort %s voor feedback", port)

    async def async_stop(self) -> None:
        """Stop listeners."""
        for server in self._servers.values():
            server.close()
            await server.wait_closed()
        self._servers.clear()

    def subscribe(self, device_id: str, callback: Callable[[bool], None]) -> Callable[[], None]:
        """Subscribe to state changes for a specific device."""
        self._listeners[device_id].append(callback)

        def unsubscribe() -> None:
            with contextlib.suppress(ValueError):
                self._listeners[device_id].remove(callback)

        return unsubscribe

    async def async_send_command(self, command: str) -> None:
        """Send a trigger command to BeWave.

        Match the original Homebridge plugin behavior: CRLF line ending and
        keep the socket open briefly after the write.
        """
        payload = f"{command}\r\n"
        _LOGGER.info("BeWave verzendt naar %s:%s -> %s", self.host, DEFAULT_TARGET_PORT, command)
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, DEFAULT_TARGET_PORT), timeout=3
        )
        try:
            writer.write(payload.encode("utf-8"))
            await asyncio.wait_for(writer.drain(), timeout=3)
            _LOGGER.debug("BeWave payload bytes: %r", payload.encode("utf-8"))
            await asyncio.sleep(0.4)
        except Exception:
            _LOGGER.exception(
                "BeWave verzenden mislukt naar %s:%s", self.host, DEFAULT_TARGET_PORT
            )
            raise
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle feedback TCP connection."""
        port = writer.get_extra_info("sockname")[1]
        peer = writer.get_extra_info("peername")
        _LOGGER.debug("BeWave feedback connectie op poort %s vanaf %s", port, peer)
        try:
            while not reader.at_eof():
                data = await reader.readline()
                if not data:
                    break
                message = data.decode("utf-8").strip()
                if message:
                    _LOGGER.info("BeWave feedback op poort %s -> %s", port, message)
                    self._dispatch_feedback(port, message)
        finally:
            writer.close()
            await writer.wait_closed()

    def _dispatch_feedback(self, port: int, message: str) -> None:
        """Dispatch feedback message to subscribers."""
        device = self._device_by_message_port.get((port, message))
        if device is None:
            _LOGGER.warning("Geen BeWave device match voor bericht %s op poort %s", message, port)
            return

        new_state = message == device.on_message
        _LOGGER.info("BeWave statusupdate %s -> %s", device.name, "AAN" if new_state else "UIT")
        for callback in list(self._listeners[device.id]):
            callback(new_state)

    def get_device(self, device_id: str) -> BeWaveDevice:
        """Return a device by id."""
        return self._device_by_id[device_id]
