# Home Assistant Integration Patterns (2026.x)

## File Structure
```
custom_components/{domain}/
├── __init__.py      # Setup, coordinator
├── manifest.json    # Metadata, requirements
├── config_flow.py   # UI configuration
├── const.py         # Constants
├── sensor.py        # Sensor platform
├── strings.json     # Translations
```

## Modern Patterns (HA 2026.x)

### Typed Config Entry
```python
from homeassistant.config_entries import ConfigEntry

type MyConfigEntry = ConfigEntry[MyCoordinator]
```

### Runtime Data (NOT hass.data)
```python
# In async_setup_entry
entry.runtime_data = coordinator

# In platform setup (sensor.py, etc.)
coordinator = entry.runtime_data
```

### DataUpdateCoordinator with Generic
```python
class MyCoordinator(DataUpdateCoordinator[list[dict]]):
    async def _async_update_data(self) -> list[dict]:
        # Fetch and return data
        ...
```

### DeviceInfo Class
```python
from homeassistant.helpers.device_registry import DeviceInfo

self._attr_device_info = DeviceInfo(
    identifiers={(DOMAIN, entry.entry_id)},
    name="Device Name",
    manufacturer="Manufacturer",
    model="Model",
)
```

### Timezone-Aware Dates
```python
from datetime import UTC, datetime

# Correct
datetime.now(tz=UTC).date().isoformat()

# Wrong (deprecated)
date.today().isoformat()
```

### Exception Naming
Exceptions must end with `Error` suffix:
```python
class CannotConnectError(Exception):
    """Error to indicate we cannot connect."""

class InvalidAuthError(Exception):
    """Error to indicate there is invalid auth."""
```

### Exception Messages
```python
# Correct - assign to variable first
msg = f"Error fetching data: {response.status}"
raise UpdateFailed(msg)

# Wrong - inline string
raise UpdateFailed(f"Error fetching data: {response.status}")
```

## Ruff Linting Notes
| Issue | Solution |
|-------|----------|
| Unused required arg | `# noqa: ARG001` |
| Runtime import flagged as type-only | `# noqa: TC002` |
| Magic numbers | Define constants in `const.py` |
| Loop with append | Use list comprehension |

## Config Flow Template
```python
class MyConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate(user_input)
            except InvalidAuthError:
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Name",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA,
            errors=errors,
        )
```

## Event Firing
```python
self.hass.bus.async_fire(
    "event_name",
    {
        "key": "value",
        "nested": {"data": "here"},
    },
)
```

## Resources
- Creating integrations: https://developers.home-assistant.io/docs/creating_component_index
- Manifest: https://developers.home-assistant.io/docs/creating_integration_manifest
- Config entries: https://developers.home-assistant.io/docs/config_entries_index
- Config flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler
