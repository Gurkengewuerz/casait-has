"""Constants for the Smart Home integration."""
import voluptuous as vol

from typing import Final

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv

DOMAIN: Final = "smart_home"

CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_NAME: Final = "name"

DEFAULT_PORT: Final = 5000

# Config flow and options flow
STEP_USER: Final = "user"

DATA_COORDINATOR: Final = "coordinator"
DATA_CONFIG: Final = "config"

SERVICE_SET_ANIMATION_SPEED = "set_animation_speed"
ATTR_SPEED = "speed"

SERVICE_SCHEMA_ANIMATION_SPEED = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_SPEED): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=255)
    ),
})
