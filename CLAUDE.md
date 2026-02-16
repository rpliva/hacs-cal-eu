# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom integration for [Cal.eu/Cal.com](https://cal.eu) calendar booking service. Distributed via HACS (Home Assistant Community Store).

- **Domain**: `cal_eu`
- **Python**: 3.13
- **Home Assistant**: 2026.2.0+

## Development Commands

```bash
# Lint
ruff check .

# Format check
ruff format . --check

# Format
ruff format .

# Install dev dependencies
pip install -r requirements.txt
```

## Architecture

### Data Flow
The integration uses a `DataUpdateCoordinator` pattern for polling the Cal.com API every 5 minutes. The coordinator is stored in `entry.runtime_data` (HA 2026.x pattern, not `hass.data`).

```
Cal.com API (bookings + schedules) → CalEuDataUpdateCoordinator → Calendars + Sensors
                                              ↓
                                     Event bus (new booking events)
```

### Coordinator Data Structure
```python
{
    "bookings": [...],   # From GET /v2/bookings?status=upcoming
    "schedules": [...]   # From GET /v2/schedules
}
```

### Key Components

| File | Purpose |
|------|---------|
| `__init__.py` | `CalEuDataUpdateCoordinator` - fetches bookings + schedules, fires events |
| `calendar.py` | Four calendars: all, confirmed, unconfirmed, availability |
| `sensor.py` | Three sensors: bookings count, next booking, unconfirmed count |
| `config_flow.py` | API key configuration with validation |
| `const.py` | API URLs, HTTP codes, booking statuses (`ACCEPTED`, `PENDING`) |

### Calendars
- **Calendar** (`calendar.cal_eu_calendar`): All bookings
- **Confirmed calendar** (`calendar.cal_eu_confirmed_calendar`): Status = ACCEPTED
- **Unconfirmed calendar** (`calendar.cal_eu_unconfirmed_calendar`): Status = PENDING
- **Availability** (`calendar.cal_eu_availability`): Schedule availability slots

### Sensors
- **Bookings** (`sensor.cal_eu_bookings`): Count as state, full booking array in attributes
- **Next Booking** (`sensor.cal_eu_next_booking`): DateTime with `timestamp` device class
- **Unconfirmed Bookings** (`sensor.cal_eu_unconfirmed_bookings`): Count of pending bookings

### Events
`cal_eu_new_booking` is fired when a new booking UID appears (compares UIDs between refreshes, skips first load).

## API Field Mapping

The Cal.com API uses different field names:
- `startTime` / `endTime` (not `start` / `end`)
- Status values are uppercase: `ACCEPTED`, `PENDING`

## HA 2026.x Patterns Used

- Typed config entry: `type CalEuConfigEntry = ConfigEntry[CalEuDataUpdateCoordinator]`
- Runtime data: `entry.runtime_data` instead of `hass.data[DOMAIN]`
- `DeviceInfo` class import from `homeassistant.helpers.device_registry`
- Timezone-aware: `datetime.now(tz=UTC)` instead of `date.today()`
- Exception messages: assign to variable before raising (`msg = "..."; raise Error(msg)`)
- Exception naming: must end with `Error` suffix

## CI/CD

- **lint.yml**: Ruff check + format on push/PR to main
- **validate.yml**: Hassfest + HACS validation on push/PR/daily
- **release.yml**: Manual version bump + GitHub release

## Cal.com API

Base URL: `https://api.cal.eu/v2`

Headers required:
```
Authorization: Bearer {API_KEY}
Content-Type: application/json
cal-api-version: {YYYY-MM-DD}
```

Endpoints used:
- `GET /v2/bookings?status=upcoming` - Fetch upcoming bookings
- `GET /v2/schedules` - Fetch availability schedules

See `docs/CAL_EU_API.md` for full API reference.
