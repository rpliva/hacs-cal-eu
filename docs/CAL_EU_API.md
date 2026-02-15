# Cal.com API v2 Reference

## Base URL
```
https://api.cal.eu/v2
```

## Authentication
```http
Authorization: Bearer {API_KEY}
Content-Type: application/json
cal-api-version: {YYYY-MM-DD}
```

- API keys found in Cal.com Settings > Security
- Test keys: `cal_` prefix
- Production keys: `cal_live_` prefix
- **Rate limit**: 120 requests/minute (expandable to 200-800/min)

## Endpoints Used in Integration

### GET /v2/bookings
Fetch bookings list.

**Query Parameters:**
| Parameter | Description |
|-----------|-------------|
| `status` | `upcoming`, `past`, `cancelled`, `all` |
| `timeZone` | UTC or IANA format |
| `start` | Start date filter |
| `end` | End date filter |

**Response Structure:**
```json
{
  "data": {
    "bookings": [
      {
        "id": 123,
        "uid": "booking-uid-abc",
        "title": "Meeting Title",
        "start": "2026-02-16T10:00:00Z",
        "end": "2026-02-16T11:00:00Z",
        "status": "accepted",
        "attendees": [
          {"name": "John Doe", "email": "john@example.com"}
        ],
        "location": "Conference Room",
        "meetingUrl": "https://cal.eu/video/xyz"
      }
    ]
  }
}
```

## Other Available Endpoints (Not Yet Implemented)

### Bookings
- `POST /v2/bookings` - Create booking
- `PATCH /v2/bookings/:uid` - Reschedule/update
- `DELETE /v2/bookings/:uid/cancel` - Cancel booking
- `POST /v2/bookings-guests/add-guests` - Add guests (max 10)

### Event Types
- `GET /v2/event-types` - List event types
- `POST /v2/event-types` - Create event type
- `PATCH /v2/event-types/:id` - Update event type
- `DELETE /v2/event-types/:id` - Delete event type

### Schedules
- `GET /v2/schedules` - List availability schedules
- `POST /v2/schedules` - Create schedule
- `PATCH /v2/schedules/:id` - Update schedule

### Availability
- `GET /v2/slots` - Query available booking times
- `GET /v2/calendars/busy-times` - Get busy times

### Users & Teams
- Full CRUD for users, teams, memberships
- Out-of-office management

### Webhooks
- Organization, team, event-type, and user-level webhooks

## HTTP Status Codes
| Code | Meaning |
|------|---------|
| `200` | Success |
| `401` | Invalid API key |
| `429` | Rate limit exceeded |

## Documentation Links
- Full docs: https://cal.com/docs/api-reference/v2/introduction
- LLM-friendly: https://cal.com/docs/llms.txt
