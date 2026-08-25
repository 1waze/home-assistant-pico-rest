# Pico REST API v1

The Home Assistant integration expects every supported device to expose:

- `GET /api/info`
- `GET /api/status`

Optional capabilities are announced by `/api/info` and may include `config`, `reboot`, `ota`, `rollback`, and `factory_reset`.

## `/api/info`

Required fields used by integration v0.3.0 and later:

```json
{
  "api": "pico-rest",
  "api_version": 1,
  "device_id": "e6614103e75b6a2d",
  "device_type": "pool_controller",
  "device_name": "HSZ Pool Pumpensteuerung",
  "manufacturer": "HSZ-IT",
  "hardware": "Raspberry Pi Pico W",
  "firmware": "3.3.1",
  "capabilities": ["status", "config", "reboot", "ota"]
}
```

Supported `device_type` values:

- `pool_controller`
- `led_controller`
- `elevator_monitor`
- `sun_wind_monitor`
- `pool_sensor_monitor`

## Stable device ID

`device_id` is the stable identity of the physical Pico. It is derived from MicroPython's `machine.unique_id()` and encoded as a lowercase hexadecimal string. The value must not depend on the IP address, hostname, configuration, or firmware version.

Home Assistant uses `device_id` for the config entry, device registry identifier, and entity unique IDs. This allows a Pico to keep the same Home Assistant device and entities when its IP address or hostname changes.

Example MicroPython implementation:

```python
import machine
import ubinascii

DEVICE_ID = ubinascii.hexlify(machine.unique_id()).decode().lower()
```

## `/api/status`

Returns the current runtime values of the device. The exact payload depends on `device_type`. Home Assistant polls this endpoint through one coordinator per Pico.

## `/api/config`

Devices announcing the `config` capability provide a typed JSON object through `GET /api/config` and accept partial configuration patches through `POST /api/config`.

## Maintenance endpoints

Depending on the announced capabilities, devices may implement:

- `POST /api/reboot`
- `POST /api/ota`
- `POST /api/rollback`
- `POST /api/factory_reset`

Maintenance actions should return a JSON object containing at least an `ok` boolean and a human-readable `message` when applicable.
