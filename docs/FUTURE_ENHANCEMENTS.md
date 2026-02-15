# Future Enhancement Ideas

## Potential New Sensors

### Today's Bookings
- Count of bookings for current day only
- Filter coordinator data by date

### Booking Duration
- Total scheduled time for today/week
- Sum of all booking durations

### Free Slots
- Available booking slots for today
- Requires `GET /v2/slots` endpoint

### Per-Event-Type Sensors
- Separate sensor for each event type
- Requires `GET /v2/event-types` endpoint

## Calendar Entity
Create a proper HA calendar entity (`calendar.cal_eu`) instead of just sensors.

**Benefits:**
- Integrates with HA calendar card
- Shows bookings on calendar view
- Supports `get_events` service

**Implementation:**
- Extend `CalendarEntity` from `homeassistant.components.calendar`
- Implement `async_get_events()` method

## Services

### `cal_eu.create_booking`
Create new booking via service call.
```yaml
service: cal_eu.create_booking
data:
  event_type_id: 123
  start: "2026-02-20T10:00:00"
  attendee_name: "John Doe"
  attendee_email: "john@example.com"
```

### `cal_eu.cancel_booking`
Cancel existing booking.
```yaml
service: cal_eu.cancel_booking
data:
  booking_uid: "abc-123"
  reason: "Schedule conflict"
```

### `cal_eu.reschedule_booking`
Reschedule booking to new time.
```yaml
service: cal_eu.reschedule_booking
data:
  booking_uid: "abc-123"
  new_start: "2026-02-21T14:00:00"
```

## Configuration Options

### Options Flow
Add runtime configuration via options flow:
- Update interval (currently hardcoded 5 min)
- Filter by event type
- Filter by date range
- Show/hide past bookings

### Multiple Accounts
Support multiple API keys / Cal.com accounts:
- Each as separate config entry
- Unique device per account

## Additional Events

### `cal_eu_booking_cancelled`
When a booking is cancelled (detected by UID removal).

### `cal_eu_booking_reminder`
Fire X minutes before booking starts (configurable).

### `cal_eu_booking_started`
When booking time starts.

### `cal_eu_booking_ended`
When booking time ends.

## Technical Improvements

### Unit Tests
Add comprehensive tests using `pytest-homeassistant-custom-component`:
- Config flow tests
- Coordinator tests
- Sensor tests
- Mock API responses

### Options Flow
Allow changing settings after setup without reconfiguring.

### Diagnostics
Add diagnostics for debugging:
- Redacted API key
- Last successful fetch
- Booking count
- Error history

### Repair Issues
Surface common problems to user:
- Invalid/expired API key
- Rate limit exceeded
- API connection issues

### Reauthentication Flow
Handle expired API keys gracefully:
- Detect 401 responses
- Prompt user to re-enter API key
- Don't require full reconfiguration

## API Endpoints to Explore

| Endpoint | Potential Use |
|----------|---------------|
| `GET /v2/event-types` | Per-event-type sensors |
| `GET /v2/slots` | Available slots sensor |
| `GET /v2/calendars/busy-times` | Busy time display |
| `POST /v2/bookings` | Create booking service |
| `DELETE /v2/bookings/:uid/cancel` | Cancel service |
| `PATCH /v2/bookings/:uid` | Reschedule service |
| Webhooks | Real-time updates instead of polling |
