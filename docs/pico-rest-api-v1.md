# Pico REST API v1

The Home Assistant integration expects every supported device to expose:

- `GET /api/info`
- `GET /api/status`

Optional capabilities are announced by `/api/info` and may include `config`, `reboot`, `ota`, `rollback`, and `factory_reset`.

## `/api/info`

Required fields used by the integration:

```json
{
  "api": "pico-rest",
  "api_version": 1,
  "device_type": "pool_controller",
  "device_name": "HSZ Pool Pumpensteuerung",
  "manufacturer": "HSZ-IT",
  "hardware": "Raspberry Pi Pico W",
  "firmware": "3.3.0",
  "capabilities": ["status", "config", "reboot", "ota"]
}
```

Supported `device_type` values in integration v0.1.0:

- `pool_controller`
- `led_controller`
- `elevator_monitor`
- `sun_wind_monitor`
- `pool_sensor_monitor`

## Stable device ID – planned protocol extension

Pico REST API v1 currently does not expose a hardware-stable identifier. Integration v0.1.0 therefore de-duplicates and identifies devices by host plus `device_type`. This works well with fixed IP addresses but is not suitable for DHCP address changes.

A future protocol update should add a stable field such as:

```json
"device_id": "e6614103e75b6a2d"
```

preferably based on `machine.unique_id()`.
