"""Config flow for Cal.eu integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE_URL,
    API_BOOKINGS_ENDPOINT,
    CONF_API_KEY,
    DOMAIN,
    HTTP_OK,
    HTTP_UNAUTHORIZED,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class CalEuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cal.eu."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]

            try:
                await self._test_api_key(api_key)
            except InvalidAuthError:
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(api_key[:16])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Cal.eu",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_api_key(self, api_key: str) -> bool:
        """Test if the API key is valid."""
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "cal-api-version": datetime.now(tz=UTC).date().isoformat(),
        }

        url = f"{API_BASE_URL}{API_BOOKINGS_ENDPOINT}"
        params = {"status": "upcoming"}

        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == HTTP_UNAUTHORIZED:
                    raise InvalidAuthError
                if response.status != HTTP_OK:
                    raise CannotConnectError
                return True
        except aiohttp.ClientError as err:
            raise CannotConnectError from err


class CannotConnectError(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuthError(Exception):
    """Error to indicate there is invalid auth."""
