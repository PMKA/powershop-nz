"""Powershop integration for Home Assistant."""
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import PowershopAPIClient, normalise_hourly_usage
from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DATE,
    CONF_ACCOUNT_NUMBER,
    CONF_PROPERTY_ID,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    SERVICE_GET_HOURLY_USAGE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

_SERVICE_GET_HOURLY_USAGE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_DATE): cv.date,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Powershop service actions."""
    hass.data.setdefault(DOMAIN, {})

    async def async_get_hourly_usage(call: ServiceCall) -> ServiceResponse:
        """Return hourly usage rows for a selected date."""
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        requested_date = call.data[ATTR_DATE]

        if entry_id is None:
            loaded_entries = [
                entry
                for entry in hass.config_entries.async_entries(DOMAIN)
                if entry.state is ConfigEntryState.LOADED
            ]
            if not loaded_entries:
                raise ServiceValidationError("No loaded Powershop NZ config entry found")
            if len(loaded_entries) > 1:
                raise ServiceValidationError(
                    "Multiple loaded Powershop NZ config entries found; "
                    "specify config_entry_id in YAML mode"
                )
            entry = loaded_entries[0]
            entry_id = entry.entry_id
        else:
            entry = hass.config_entries.async_get_entry(entry_id)

        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError("Powershop NZ config entry not found")
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError("Powershop NZ config entry is not loaded")

        coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
        if coordinator is None:
            raise ServiceValidationError("Powershop NZ coordinator is not available")

        account_number = entry.data.get(CONF_ACCOUNT_NUMBER)
        property_id = entry.data.get(CONF_PROPERTY_ID)
        if not account_number or not property_id:
            raise ServiceValidationError(
                "Powershop NZ account or property is not configured"
            )

        nodes = await coordinator.client.get_measurements(
            account_number,
            property_id,
            24,
            requested_date.isoformat(),
            "HOUR_INTERVAL",
        )
        hourly_usage = normalise_hourly_usage(nodes)

        return {
            "date": requested_date.isoformat(),
            "hourly_usage_count": len(hourly_usage),
            "total_kwh": round(sum(row["kwh"] for row in hourly_usage), 3),
            "total_cost_incl_tax_estimated_nzd": round(
                sum(row["cost_incl_tax_estimated_nzd"] for row in hourly_usage),
                2,
            ),
            "hourly_usage": hourly_usage,
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_HOURLY_USAGE,
        async_get_hourly_usage,
        schema=_SERVICE_GET_HOURLY_USAGE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
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
