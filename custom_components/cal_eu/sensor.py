"""Sensor platform for Cal.eu integration."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CalEuDataUpdateCoordinator
from .const import BOOKING_STATUS_PENDING, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import CalEuConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CalEuConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cal.eu sensor based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CalEuBookingsSensor(coordinator, entry),
            CalEuNextBookingSensor(coordinator, entry),
            CalEuUnconfirmedBookingsSensor(coordinator, entry),
        ]
    )


def _get_bookings(coordinator: CalEuDataUpdateCoordinator) -> list[dict]:
    """Get bookings from coordinator data."""
    if not coordinator.data:
        return []
    return coordinator.data.get("bookings", [])


class CalEuBookingsSensor(CoordinatorEntity[CalEuDataUpdateCoordinator], SensorEntity):
    """Sensor representing Cal.eu bookings count."""

    _attr_has_entity_name = True
    _attr_name = "Bookings"
    _attr_icon = "mdi:calendar"

    def __init__(
        self,
        coordinator: CalEuDataUpdateCoordinator,
        entry: CalEuConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_bookings"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Cal.eu",
            manufacturer="Cal.com",
            model="Calendar",
        )

    @property
    def native_value(self) -> int:
        """Return the number of upcoming bookings."""
        return len(_get_bookings(self.coordinator))

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes with booking details."""
        bookings = _get_bookings(self.coordinator)
        return {
            "bookings": [
                {
                    "id": booking.get("id"),
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
                }
                for booking in bookings
            ]
        }


class CalEuNextBookingSensor(
    CoordinatorEntity[CalEuDataUpdateCoordinator], SensorEntity
):
    """Sensor representing the next upcoming Cal.eu booking date."""

    _attr_has_entity_name = True
    _attr_name = "Next booking"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: CalEuDataUpdateCoordinator,
        entry: CalEuConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_next_booking"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Cal.eu",
            manufacturer="Cal.com",
            model="Calendar",
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the start time of the next upcoming booking."""
        bookings = _get_bookings(self.coordinator)
        if not bookings:
            return None

        next_booking = min(
            bookings,
            key=lambda b: b.get("startTime", ""),
            default=None,
        )

        if next_booking and next_booking.get("startTime"):
            return datetime.fromisoformat(next_booking["startTime"])

        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return details of the next booking."""
        bookings = _get_bookings(self.coordinator)
        if not bookings:
            return {}

        next_booking = min(
            bookings,
            key=lambda b: b.get("startTime", ""),
            default=None,
        )

        if not next_booking:
            return {}

        return {
            "title": next_booking.get("title"),
            "end": next_booking.get("endTime"),
            "location": next_booking.get("location"),
        }


class CalEuUnconfirmedBookingsSensor(
    CoordinatorEntity[CalEuDataUpdateCoordinator], SensorEntity
):
    """Sensor representing the count of unconfirmed Cal.eu bookings."""

    _attr_has_entity_name = True
    _attr_name = "Unconfirmed bookings"
    _attr_icon = "mdi:calendar-question"

    def __init__(
        self,
        coordinator: CalEuDataUpdateCoordinator,
        entry: CalEuConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_unconfirmed_bookings"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Cal.eu",
            manufacturer="Cal.com",
            model="Calendar",
        )

    def _get_unconfirmed_bookings(self) -> list[dict]:
        """Return list of unconfirmed bookings."""
        bookings = _get_bookings(self.coordinator)
        return [
            booking
            for booking in bookings
            if booking.get("status") == BOOKING_STATUS_PENDING
        ]

    @property
    def native_value(self) -> int:
        """Return the number of unconfirmed bookings."""
        return len(self._get_unconfirmed_bookings())

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes with unconfirmed booking details."""
        unconfirmed = self._get_unconfirmed_bookings()
        return {
            "bookings": [
                {
                    "id": booking.get("id"),
                    "uid": booking.get("uid"),
                    "title": booking.get("title"),
                    "start": booking.get("startTime"),
                    "end": booking.get("endTime"),
                    "attendees": [
                        {
                            "name": attendee.get("name"),
                            "email": attendee.get("email"),
                        }
                        for attendee in booking.get("attendees", [])
                    ],
                    "location": booking.get("location"),
                }
                for booking in unconfirmed
            ]
        }
