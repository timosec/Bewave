"""The BeWave integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICES, DOMAIN, PLATFORMS

BeWaveConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: BeWaveConfigEntry) -> bool:
    """Set up BeWave from a config entry."""
    from .models import normalize_device
    from .tcp import BeWaveHub

    hass.data.setdefault(DOMAIN, {})

    raw_devices = entry.options.get(CONF_DEVICES, entry.data.get(CONF_DEVICES, []))
    devices = [normalize_device(device, idx + 1) for idx, device in enumerate(raw_devices)]

    hub = BeWaveHub(hass, entry.data[CONF_HOST], devices)
    await hub.async_start()

    hass.data[DOMAIN][entry.entry_id] = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BeWaveConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_stop()
    return unload_ok
