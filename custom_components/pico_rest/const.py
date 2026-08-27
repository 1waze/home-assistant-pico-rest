"""Constants for the Pico REST integration."""

from datetime import timedelta

DOMAIN = "pico_rest"
CONF_HOST = "host"
CONF_PORT = "port"
DEFAULT_PORT = 80
API_VERSION = 1

PLATFORMS = [
    "sensor",
    "binary_sensor",
    "switch",
    "number",
    "select",
    "time",
    "button",
]

DEFAULT_SCAN_INTERVALS = {
    "elevator_monitor": timedelta(seconds=2),
    "pool_controller": timedelta(seconds=10),
    "led_controller": timedelta(seconds=10),
    "sun_wind_monitor": timedelta(seconds=10),
    "pool_sensor_monitor": timedelta(seconds=10),
}
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

SUPPORTED_DEVICE_TYPES = {
    "pool_controller",
    "led_controller",
    "elevator_monitor",
    "sun_wind_monitor",
    "pool_sensor_monitor",
}

WEEKDAYS = (
    ("0", "Montag"),
    ("1", "Dienstag"),
    ("2", "Mittwoch"),
    ("3", "Donnerstag"),
    ("4", "Freitag"),
    ("5", "Samstag"),
    ("6", "Sonntag"),
)

LED_EFFECTS = (
    "solid",
    "two_color",
    "rainbow",
    "pulse",
    "theater",
    "scanner",
    "sparkle",
    "matrix",
    "chevrons",
)
LED_ELEVATOR_EFFECTS = ("chevrons", "scanner", "theater")
