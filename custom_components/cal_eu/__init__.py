"""The Cal.eu integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant  # noqa: TC002
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
    API_BOOKINGS_ENDPOINT,
    API_SCHEDULES_ENDPOINT,
    CONF_API_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_NEW_BOOKING,
    HTTP_OK,
    HTTP_UNAUTHORIZED,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR]

type CalEuConfigEntry = ConfigEntry[CalEuDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CalEuConfigEntry) -> bool:
    """Set up Cal.eu from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    session = async_get_clientsession(hass)

    coordinator = CalEuDataUpdateCoordinator(hass, session, api_key)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: CalEuConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class CalEuDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching Cal.eu data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._session = session
        self._api_key = api_key
        self._known_booking_uids: set[str] = set()

    def _get_headers(self) -> dict[str, str]:
        """Return API headers."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "cal-api-version": datetime.now(tz=UTC).date().isoformat(),
        }

    async def _async_update_data(self) -> dict:
        """Fetch data from Cal.eu API."""
        try:
            bookings = await self._fetch_bookings()
            schedules = await self._fetch_schedules()
        except aiohttp.ClientError as err:
            msg = f"Error communicating with API: {err}"
            raise UpdateFailed(msg) from err

        self._fire_new_booking_events(bookings)

        return {"bookings": bookings, "schedules": schedules}

    async def _fetch_bookings(self) -> list[dict]:
        """Fetch bookings from API."""
        url = f"{API_BASE_URL}{API_BOOKINGS_ENDPOINT}"
        params = {"status": "upcoming"}

        async with self._session.get(
            url, headers=self._get_headers(), params=params
        ) as response:
            if response.status == HTTP_UNAUTHORIZED:
                msg = "Invalid API key"
                raise UpdateFailed(msg)
            if response.status != HTTP_OK:
                msg = f"Error fetching bookings: {response.status}"
                raise UpdateFailed(msg)

            data = await response.json()
            return data.get("data", {}).get("bookings", [])

    async def _fetch_schedules(self) -> list[dict]:
        """Fetch schedules from API."""
        url = f"{API_BASE_URL}{API_SCHEDULES_ENDPOINT}"

        async with self._session.get(url, headers=self._get_headers()) as response:
            if response.status == HTTP_UNAUTHORIZED:
                msg = "Invalid API key"
                raise UpdateFailed(msg)
            if response.status != HTTP_OK:
                _LOGGER.warning("Error fetching schedules: %s", response.status)
                return []

            data = await response.json()
            return data.get("data", [])

    def _fire_new_booking_events(self, bookings: list[dict]) -> None:
        """Fire events for newly detected bookings."""
        current_uids = {b.get("uid") for b in bookings if b.get("uid")}

        # Skip firing events on first load
        if not self._known_booking_uids:
            self._known_booking_uids = current_uids
            return

        new_uids = current_uids - self._known_booking_uids

        for booking in bookings:
            if booking.get("uid") in new_uids:
                self.hass.bus.async_fire(
                    EVENT_NEW_BOOKING,
                    {
                        "uid": booking.get("uid"),
                        "title": booking.get("title"),
                        "start": booking.get("startTime"),
                        "end": booking.get("endTime"),
                        "status": booking.get("status"),
                        "attendees": [
                            {
                                "name": attendee.get("name"),
                                "email": attendee.get("email"),
                            }
                            for attendee in booking.get("attendees", [])
                        ],
                        "location": booking.get("location"),
                    },
                )
                _LOGGER.debug("Fired new booking event for: %s", booking.get("title"))

        self._known_booking_uids = current_uids
