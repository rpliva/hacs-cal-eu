"""Calendar platform for Cal.eu integration."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CalEuDataUpdateCoordinator
from .const import DOMAIN

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
    async_add_entities([CalEuCalendar(coordinator, entry)])


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
            return None

        now = datetime.now().astimezone()

        # Find the next event (first one that hasn't ended yet)
        for booking in sorted(
            self.coordinator.data,
            key=lambda b: b.get("start", ""),
        ):
            end_str = booking.get("end")
            if end_str:
                end_time = datetime.fromisoformat(end_str)
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
            return []

        events = []
        for booking in self.coordinator.data:
            start_str = booking.get("start")
            end_str = booking.get("end")

            if not start_str or not end_str:
                continue

            event_start = datetime.fromisoformat(start_str)
            event_end = datetime.fromisoformat(end_str)

            # Check if event overlaps with requested range
            if event_end >= start_date and event_start <= end_date:
                events.append(self._booking_to_event(booking))

        return sorted(events, key=lambda e: e.start)

    def _booking_to_event(self, booking: dict) -> CalendarEvent:
        """Convert a booking dict to a CalendarEvent."""
        return CalendarEvent(
            summary=booking.get("title", "Cal.eu Booking"),
            start=datetime.fromisoformat(booking["start"]),
            end=datetime.fromisoformat(booking["end"]),
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

        if booking.get("meetingUrl"):
            parts.append(f"Meeting URL: {booking['meetingUrl']}")

        return "\n".join(parts)
