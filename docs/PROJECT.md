# Cal.eu Home Assistant Integration - Project Reference

## Project Overview
Custom Home Assistant integration for Cal.com (cal.eu) calendar booking service.
- **Domain**: `cal_eu`
- **HA Version**: 2026.2.0+
- **IoT Class**: `cloud_polling` (5-minute update interval)

## Key Files
| File | Purpose |
|------|---------|
| `custom_components/cal_eu/__init__.py` | Coordinator, fetches bookings + schedules |
| `custom_components/cal_eu/calendar.py` | Four calendar entities (all, confirmed, unconfirmed, availability) |
| `custom_components/cal_eu/sensor.py` | Bookings, Next booking, Unconfirmed sensors |
| `custom_components/cal_eu/config_flow.py` | API key configuration UI |
| `custom_components/cal_eu/const.py` | Constants (API URLs, HTTP codes, booking statuses) |
| `custom_components/cal_eu/strings.json` | UI translations |
| `custom_components/cal_eu/manifest.json` | Integration metadata, requirements |

## Architecture Patterns (HA 2026.x)
- **Type alias**: `type CalEuConfigEntry = ConfigEntry[CalEuDataUpdateCoordinator]`
- **Runtime data**: Use `entry.runtime_data` (not `hass.data[DOMAIN]`)
- **DeviceInfo**: Use `DeviceInfo()` class (not dict)
- **Coordinator**: Generic type `DataUpdateCoordinator[dict]` returning `{"bookings": [...], "schedules": [...]}`

## Calendars

### All Bookings (`calendar.cal_eu_calendar`)
- Displays all upcoming bookings in HA calendar view

### Confirmed Bookings (`calendar.cal_eu_confirmed_calendar`)
- Displays only bookings with status `ACCEPTED`

### Unconfirmed Bookings (`calendar.cal_eu_unconfirmed_calendar`)
- Displays only bookings with status `PENDING`

### Availability (`calendar.cal_eu_availability`)
- Displays availability slots from schedules
- Uses `dateOverrides` from schedules API

## Sensors

### Bookings Sensor (`sensor.cal_eu_bookings`)
- **State**: Count of upcoming bookings (integer)
- **Attributes**: `bookings` array with full booking details

### Next Booking Sensor (`sensor.cal_eu_next_booking`)
- **State**: DateTime of next upcoming booking
- **Device class**: `timestamp` (displays as relative time)
- **Attributes**: `title`, `end`, `location`

### Unconfirmed Bookings Sensor (`sensor.cal_eu_unconfirmed_bookings`)
- **State**: Count of pending/unconfirmed bookings
- **Attributes**: `bookings` array with unconfirmed booking details

## Events

### `cal_eu_new_booking`
Fired when a new booking is detected (compares UIDs between refreshes).

**Event Data:**
```yaml
uid: "booking-uid-123"
title: "Meeting Title"
start: "2026-02-16T10:00:00Z"
end: "2026-02-16T11:00:00Z"
status: "ACCEPTED"
attendees:
  - name: "John Doe"
    email: "john@example.com"
location: "https://zoom.us/..."
```

## API Field Mapping

API fields use different names than displayed in attributes:
- `startTime` → `start`
- `endTime` → `end`
- Status values are uppercase: `ACCEPTED`, `PENDING`

## GitHub Workflows
| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `lint.yml` | Push/PR to main | Ruff linting and formatting |
| `validate.yml` | Push/PR/Daily | Hassfest + HACS validation |
| `release.yml` | Manual dispatch | Version bump + GitHub release |

## Dependencies
- `homeassistant>=2026.2.0`
- `aiohttp>=3.8.0`
- `ruff==0.11.5` (dev)
- `pytest-homeassistant-custom-component==0.13.315` (dev)
