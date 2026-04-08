"""Config flow for Powershop integration."""
import logging
from typing import Any, Dict, Mapping, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import AuthError, OTPError, PowershopAPIClient
from .const import (
    CONF_ACCOUNT_NUMBER,
    CONF_EMAIL,
    CONF_PROPERTY_ID,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_STEP_EMAIL_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str})
_STEP_OTP_SCHEMA = vol.Schema({vol.Required("otp"): str})


class PowershopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Powershop (email OTP)."""

    VERSION = 2

    def __init__(self) -> None:
        self._email: Optional[str] = None
        self._journey_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Step 1 – enter email, trigger OTP
    # ------------------------------------------------------------------

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        errors: Dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            client = PowershopAPIClient()
            try:
                journey_id = await client.send_otp(email)
                await client.close()
                self._email = email
                self._journey_id = journey_id
                return await self.async_step_otp()
            except AuthError:
                errors["base"] = "email_not_found"
            except Exception:
                _LOGGER.exception("Unexpected error sending OTP")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="user",
            data_schema=_STEP_EMAIL_SCHEMA,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Step 2 – enter OTP code, complete sign-in
    # ------------------------------------------------------------------

    async def async_step_otp(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        errors: Dict[str, str] = {}

        if user_input is not None:
            otp = user_input["otp"].strip()
            client = PowershopAPIClient()
            try:
                tokens = await client.verify_otp(self._email, otp, self._journey_id)

                # Give the client the fresh tokens so it can call the API
                client.refresh_token = tokens["refresh_token"]
                client._id_token = tokens["id_token"]

                # Discover account number and first property ID
                info = await client.get_account_info()
                accounts = (info.get("viewer") or {}).get("accounts", [])
                if not accounts:
                    errors["base"] = "no_accounts"
                else:
                    account = accounts[0]
                    account_number = account.get("number")
                    properties = account.get("properties", [])
                    property_id = properties[0]["id"] if properties else None

                    await self.async_set_unique_id(account_number)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Powershop ({self._email})",
                        data={
                            CONF_EMAIL: self._email,
                            CONF_REFRESH_TOKEN: tokens["refresh_token"],
                            CONF_ACCOUNT_NUMBER: account_number,
                            CONF_PROPERTY_ID: property_id,
                        },
                    )
            except OTPError:
                errors["base"] = "invalid_otp"
            except AuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error verifying OTP")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="otp",
            data_schema=_STEP_OTP_SCHEMA,
            errors=errors,
            description_placeholders={"email": self._email},
        )

    # ------------------------------------------------------------------
    # Re-authentication flow (triggered when refresh token expires)
    # ------------------------------------------------------------------

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Re-authenticate an existing entry (e.g. refresh token revoked)."""
        self._email = entry_data.get(CONF_EMAIL)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        errors: Dict[str, str] = {}

        if user_input is not None:
            client = PowershopAPIClient()
            try:
                journey_id = await client.send_otp(self._email)
                await client.close()
                self._journey_id = journey_id
                return await self.async_step_reauth_otp()
            except Exception:
                _LOGGER.exception("Re-auth OTP send failed")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"email": self._email},
        )

    async def async_step_reauth_otp(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        errors: Dict[str, str] = {}

        if user_input is not None:
            otp = user_input["otp"].strip()
            client = PowershopAPIClient()
            try:
                tokens = await client.verify_otp(self._email, otp, self._journey_id)
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_REFRESH_TOKEN: tokens["refresh_token"],
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            except OTPError:
                errors["base"] = "invalid_otp"
            except Exception:
                _LOGGER.exception("Re-auth OTP verify failed")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="reauth_otp",
            data_schema=_STEP_OTP_SCHEMA,
            errors=errors,
            description_placeholders={"email": self._email},
        )
