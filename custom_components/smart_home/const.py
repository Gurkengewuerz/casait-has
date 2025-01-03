"""Constants for the Smart Home integration."""
from typing import Final

DOMAIN: Final = "smart_home"

CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_NAME: Final = "name"

DEFAULT_PORT: Final = 5000

# Config flow and options flow
STEP_USER: Final = "user"

DATA_COORDINATOR: Final = "coordinator"
DATA_CONFIG: Final = "config"

# Device type mapping
DEVICE_TYPE_MAPPING = {
    "switch": "switch",
    "pushbutton": "button",
    "blind": "cover",
    "sensor": "sensor",
    "binary_sensor": "binary_sensor"
}