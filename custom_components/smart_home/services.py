"""Service for adjusting animation speed of RGB lights."""
from __future__ import annotations

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_ANIMATION_SPEED = "set_animation_speed"
ATTR_SPEED = "speed"

SERVICE_SCHEMA_ANIMATION_SPEED = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_SPEED): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=255)
    ),
})

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Light Animation services."""

    # Register services
    async def service_handler(call: ServiceCall) -> None:
        """Handle the services."""
        # coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        if call.service == SERVICE_SET_ANIMATION_SPEED:
            # Get all light entities from the call
            target_entities = call.data.get(ATTR_ENTITY_ID)
            speed = call.data.get(ATTR_SPEED)

            for entity_id in target_entities:
                # Find the light entity
                entity = hass.data[LIGHT_DOMAIN].get_entity(entity_id)
                if entity and hasattr(entity, "set_animation_speed"):
                    await entity.set_animation_speed(speed)
                else:
                    _LOGGER.warning(
                        "Entity %s doesn't support animation speed adjustment",
                        entity_id
                    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ANIMATION_SPEED,
        service_handler,
        schema=SERVICE_SCHEMA_ANIMATION_SPEED,
    )

async def async_unload_services(hass: HomeAssistant) -> None:
    # Unregister services
    hass.services.async_remove(DOMAIN, SERVICE_SET_ANIMATION_SPEED)
