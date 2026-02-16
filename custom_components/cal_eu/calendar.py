"""Calendar platform for Cal.eu integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CalEuDataUpdateCoordinator
from .const import BOOKING_STATUS_ACCEPTED, BOOKING_STATUS_PENDING, DOMAIN

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
            CalEuConfirmedCalendar(coordinator, entry),
            CalEuUnconfirmedCalendar(coordinator, entry),
            CalEuSchedulesCalendar(coordinator, entry),
        ]
    )


def _get_bookings(coordinator: CalEuDataUpdateCoordinator) -> list[dict]:
    """Get bookings from coordinator data."""
    if not coordinator.data:
        return []
    return coordinator.data.get("bookings", [])


def _get_schedules(coordinator: CalEuDataUpdateCoordinator) -> list[dict]:
    """Get schedules from coordinator data."""
    if not coordinator.data:
        return []
    return coordinator.data.get("schedules", [])


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
        bookings = _get_bookings(self.coordinator)
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
        """Return calendar events within a datetime range."""
        bookings = _get_bookings(self.coordinator)
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

        if booking.get("status"):
            parts.append(f"Status: {booking['status']}")

        attendees = booking.get("attendees", [])
        if attendees:
            attendee_strs = [
                f"{a.get('name', 'Unknown')} ({a.get('email', '')})" for a in attendees
            ]
            parts.append(f"Attendees: {', '.join(attendee_strs)}")

        return "\n".join(parts)


class CalEuConfirmedCalendar(
    CoordinatorEntity[CalEuDataUpdateCoordinator], CalendarEntity
):
    """Calendar entity for confirmed Cal.eu bookings."""

    _attr_has_entity_name = True
    _attr_name = "Confirmed calendar"

    def __init__(
        self,
        coordinator: CalEuDataUpdateCoordinator,
        entry: CalEuConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_confirmed_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Cal.eu",
            manufacturer="Cal.com",
            model="Calendar",
        )

    def _get_confirmed_bookings(self) -> list[dict]:
        """Return list of confirmed bookings."""
        bookings = _get_bookings(self.coordinator)
        return [
            booking
            for booking in bookings
            if booking.get("status") == BOOKING_STATUS_ACCEPTED
        ]

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming confirmed event."""
        bookings = self._get_confirmed_bookings()
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
        """Return confirmed calendar events within a datetime range."""
        bookings = self._get_confirmed_bookings()
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
        bookings = _get_bookings(self.coordinator)
        return [
            booking
            for booking in bookings
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


class CalEuSchedulesCalendar(
    CoordinatorEntity[CalEuDataUpdateCoordinator], CalendarEntity
):
    """Calendar entity for Cal.eu availability schedules."""

    _attr_has_entity_name = True
    _attr_name = "Availability"

    def __init__(
        self,
        coordinator: CalEuDataUpdateCoordinator,
        entry: CalEuConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_schedules_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Cal.eu",
            manufacturer="Cal.com",
            model="Calendar",
        )

    def _get_availability_slots(self) -> list[dict]:
        """Extract availability slots from all schedules."""
        schedules = _get_schedules(self.coordinator)
        slots = []

        for schedule in schedules:
            schedule_name = schedule.get("name", "Availability")

            # Use dateOverrides which has full datetime ranges
            for override in schedule.get("dateOverrides", []):
                for slot_range in override.get("ranges", []):
                    start_str = slot_range.get("start")
                    end_str = slot_range.get("end")
                    if start_str and end_str:
                        slots.append(
                            {
                                "name": schedule_name,
                                "start": start_str,
                                "end": end_str,
                                "schedule_id": schedule.get("id"),
                            }
                        )

        return slots

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming availability slot."""
        slots = self._get_availability_slots()
        if not slots:
            return None

        now = datetime.now(tz=UTC)

        for slot in sorted(slots, key=lambda s: s.get("start", "")):
            end_time = _parse_datetime(slot["end"])
            if end_time > now:
                return self._slot_to_event(slot)

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,  # noqa: ARG002
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return availability slots within a datetime range."""
        slots = self._get_availability_slots()
        if not slots:
            return []

        events = []
        for slot in slots:
            event_start = _parse_datetime(slot["start"])
            event_end = _parse_datetime(slot["end"])

            if event_end >= start_date and event_start <= end_date:
                events.append(self._slot_to_event(slot))

        return sorted(events, key=lambda e: e.start)

    def _slot_to_event(self, slot: dict) -> CalendarEvent:
        """Convert an availability slot to a CalendarEvent."""
        return CalendarEvent(
            summary=f"Available: {slot['name']}",
            start=_parse_datetime(slot["start"]),
            end=_parse_datetime(slot["end"]),
            uid=f"schedule_{slot.get('schedule_id')}_{slot['start']}",
        )
