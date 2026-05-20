"""Powershop integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import AuthError, PowershopAPIClient
from .const import CONF_ACCOUNT_NUMBER, CONF_PROPERTY_ID, CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Powershop from a config entry."""
    from .sensor import PowershopDataUpdateCoordinator

    hass.data.setdefault(DOMAIN, {})

    client = PowershopAPIClient(refresh_token=entry.data[CONF_REFRESH_TOKEN])
    coordinator = PowershopDataUpdateCoordinator(hass, client, entry)

    # Raises ConfigEntryNotReady here (before platform forwarding) as HA requires
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            await coordinator.client.close()
    return unload_ok