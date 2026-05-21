"""Powershop integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .api import AuthError, PowershopAPIClient
from .const import CONF_ACCOUNT_NUMBER, CONF_PROPERTY_ID, CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entry to the current version."""
    if config_entry.version == 2 and config_entry.minor_version < 2:
        # v2.1 → v2.2: rename entity IDs to sensor.powershop_nz_{key}
        registry = er.async_get(hass)
        account_number = config_entry.data.get(CONF_ACCOUNT_NUMBER, "")
        unique_id_prefix = f"{DOMAIN}_{account_number}_"

        for entity_entry in er.async_entries_for_config_entry(registry, config_entry.entry_id):
            if not entity_entry.unique_id.startswith(unique_id_prefix):
                continue
            key = entity_entry.unique_id[len(unique_id_prefix):]
            new_entity_id = f"sensor.{DOMAIN}_{key}"
            if entity_entry.entity_id != new_entity_id:
                _LOGGER.info("Migrating entity ID %s → %s", entity_entry.entity_id, new_entity_id)
                registry.async_update_entity(entity_entry.entity_id, new_entity_id=new_entity_id)

        hass.config_entries.async_update_entry(config_entry, minor_version=2)

    return True


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