"""Calendar platform for Cal.eu integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CalEuDataUpdateCoordinator
from .const import BOOKING_STATUS_PENDING, DOMAIN

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import CalEuConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CalEuConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cal.eu calendar based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CalEuCalendar(coordinator, entry),
            CalEuUnconfirmedCalendar(coordinator, entry),
        ]
    )


def _parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string and ensure timezone awareness."""
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class CalEuCalendar(CoordinatorEntity[CalEuDataUpdateCoordinator], CalendarEntity):
    """Calendar entity for Cal.eu bookings."""

    _attr_has_entity_name = True
    _attr_name = "Calendar"

    def __init__(
        self,
        coordinator: CalEuDataUpdateCoordinator,
        entry: CalEuConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Cal.eu",
            manufacturer="Cal.com",
            model="Calendar",
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        if not self.coordinator.data:
            _LOGGER.debug("No coordinator data available")
            return None

        now = datetime.now(tz=UTC)
        _LOGGER.debug(
            "Looking for next event, now=%s, bookings=%d",
            now,
            len(self.coordinator.data),
        )

        # Find the next event (first one that hasn't ended yet)
        for booking in sorted(
            self.coordinator.data,
            key=lambda b: b.get("startTime", ""),
        ):
            end_str = booking.get("endTime")
            if end_str:
                end_time = _parse_datetime(end_str)
                _LOGGER.debug(
                    "Checking booking: %s, end=%s", booking.get("title"), end_time
                )
                if end_time > now:
                    return self._booking_to_event(booking)

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,  # noqa: ARG002
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        if not self.coordinator.data:
            _LOGGER.debug("async_get_events: No coordinator data")
            return []

        _LOGGER.debug(
            "async_get_events: range=%s to %s, bookings=%d",
            start_date,
            end_date,
            len(self.coordinator.data),
        )

        events = []
        for booking in self.coordinator.data:
            start_str = booking.get("startTime")
            end_str = booking.get("endTime")

            if not start_str or not end_str:
                _LOGGER.debug("Skipping booking without startTime/endTime: %s", booking)
                continue

            event_start = _parse_datetime(start_str)
            event_end = _parse_datetime(end_str)

            _LOGGER.debug(
                "Booking: %s, start=%s, end=%s",
                booking.get("title"),
                event_start,
                event_end,
            )

            # Check if event overlaps with requested range
            if event_end >= start_date and event_start <= end_date:
                events.append(self._booking_to_event(booking))
                _LOGGER.debug("Added event: %s", booking.get("title"))

        return sorted(events, key=lambda e: e.start)

    def _booking_to_event(self, booking: dict) -> CalendarEvent:
        """Convert a booking dict to a CalendarEvent."""
        return CalendarEvent(
            summary=booking.get("title", "Cal.eu Booking"),
            start=_parse_datetime(booking["startTime"]),
            end=_parse_datetime(booking["endTime"]),
            location=booking.get("location"),
            description=self._build_description(booking),
            uid=booking.get("uid"),
        )

    def _build_description(self, booking: dict) -> str:
        """Build event description from booking details."""
        parts = []

        if booking.get("status"):
            parts.append(f"Status: {booking['status']}")

        attendees = booking.get("attendees", [])
        if attendees:
            attendee_strs = [
                f"{a.get('name', 'Unknown')} ({a.get('email', '')})" for a in attendees
            ]
            parts.append(f"Attendees: {', '.join(attendee_strs)}")

        return "\n".join(parts)


class CalEuUnconfirmedCalendar(
    CoordinatorEntity[CalEuDataUpdateCoordinator], CalendarEntity
):
    """Calendar entity for unconfirmed Cal.eu bookings."""

    _attr_has_entity_name = True
    _attr_name = "Unconfirmed calendar"

    def __init__(
        self,
        coordinator: CalEuDataUpdateCoordinator,
        entry: CalEuConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_unconfirmed_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Cal.eu",
            manufacturer="Cal.com",
            model="Calendar",
        )

    def _get_unconfirmed_bookings(self) -> list[dict]:
        """Return list of unconfirmed bookings."""
        if not self.coordinator.data:
            return []
        return [
            booking
            for booking in self.coordinator.data
            if booking.get("status") == BOOKING_STATUS_PENDING
        ]

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming unconfirmed event."""
        bookings = self._get_unconfirmed_bookings()
        if not bookings:
            return None

        now = datetime.now(tz=UTC)

        for booking in sorted(bookings, key=lambda b: b.get("startTime", "")):
            end_str = booking.get("endTime")
            if end_str:
                end_time = _parse_datetime(end_str)
                if end_time > now:
                    return self._booking_to_event(booking)

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,  # noqa: ARG002
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return unconfirmed calendar events within a datetime range."""
        bookings = self._get_unconfirmed_bookings()
        if not bookings:
            return []

        events = []
        for booking in bookings:
            start_str = booking.get("startTime")
            end_str = booking.get("endTime")

            if not start_str or not end_str:
                continue

            event_start = _parse_datetime(start_str)
            event_end = _parse_datetime(end_str)

            if event_end >= start_date and event_start <= end_date:
                events.append(self._booking_to_event(booking))

        return sorted(events, key=lambda e: e.start)

    def _booking_to_event(self, booking: dict) -> CalendarEvent:
        """Convert a booking dict to a CalendarEvent."""
        return CalendarEvent(
            summary=booking.get("title", "Cal.eu Booking"),
            start=_parse_datetime(booking["startTime"]),
            end=_parse_datetime(booking["endTime"]),
            location=booking.get("location"),
            description=self._build_description(booking),
            uid=booking.get("uid"),
        )

    def _build_description(self, booking: dict) -> str:
        """Build event description from booking details."""
        parts = []

        attendees = booking.get("attendees", [])
        if attendees:
            attendee_strs = [
                f"{a.get('name', 'Unknown')} ({a.get('email', '')})" for a in attendees
            ]
            parts.append(f"Attendees: {', '.join(attendee_strs)}")

        return "\n".join(parts)
