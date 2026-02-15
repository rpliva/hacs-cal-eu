# Cal.eu Integration for Home Assistant

[![Validate](https://github.com/rpliva/hacs-cal-eu/actions/workflows/validate.yml/badge.svg)](https://github.com/rpliva/hacs-cal-eu/actions/workflows/validate.yml)
[![Lint](https://github.com/rpliva/hacs-cal-eu/actions/workflows/lint.yml/badge.svg)](https://github.com/rpliva/hacs-cal-eu/actions/workflows/lint.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for [Cal.com](https://cal.eu) calendar booking service.

## Features

- **Bookings Sensor**: Shows the count of upcoming bookings with full booking details in attributes
- **Next Booking Sensor**: Displays the date/time of your next upcoming booking
- **New Booking Event**: Fires `cal_eu_new_booking` event when a new booking is detected

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Add"
6. Search for "Cal.eu" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the `cal_eu` folder from `custom_components`
2. Copy it to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Cal.eu"
4. Enter your Cal.com API key (found in Settings > Security on cal.com)

## Sensors

### Bookings (`sensor.cal_eu_bookings`)

- **State**: Number of upcoming bookings
- **Attributes**:
  - `bookings`: Array of booking objects containing:
    - `id`, `uid`, `title`, `start`, `end`, `status`
    - `attendees`: List of attendee names and emails
    - `location`, `meeting_url`

### Next Booking (`sensor.cal_eu_next_booking`)

- **State**: DateTime of the next upcoming booking
- **Device Class**: `timestamp` (displays as relative time)
- **Attributes**: `title`, `end`, `location`, `meeting_url`

## Events

### `cal_eu_new_booking`

Fired when a new booking is detected. Event data includes:

```yaml
uid: "booking-uid-123"
title: "Meeting with John"
start: "2024-02-16T10:00:00Z"
end: "2024-02-16T11:00:00Z"
status: "accepted"
attendees:
  - name: "John Doe"
    email: "john@example.com"
location: "Conference Room A"
meeting_url: "https://cal.eu/video/abc123"
```

## Automation Example

```yaml
automation:
  - alias: "Notify on new Cal.eu booking"
    trigger:
      - platform: event
        event_type: cal_eu_new_booking
    action:
      - service: notify.mobile_app
        data:
          title: "New booking: {{ trigger.event.data.title }}"
          message: "Scheduled for {{ trigger.event.data.start }}"
```

## License

MIT License
