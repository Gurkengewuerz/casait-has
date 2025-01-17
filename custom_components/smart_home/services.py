"""Service for adjusting animation speed and colors of RGB lights."""
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
SERVICE_SET_COLORS = "set_colors"
ATTR_SPEED = "speed"
ATTR_COLOR1 = "color1"
ATTR_COLOR2 = "color2"
ATTR_COLOR3 = "color3"
ATTR_COLOR4 = "color4"
ATTR_COLOR5 = "color5"

SERVICE_SCHEMA_ANIMATION_SPEED = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_SPEED): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=255)
    ),
})

SERVICE_SCHEMA_SET_COLORS = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_COLOR1): vol.All(list, vol.Length(min=3, max=3)),
    vol.Optional(ATTR_COLOR2): vol.All(list, vol.Length(min=3, max=3)),
    vol.Optional(ATTR_COLOR3): vol.All(list, vol.Length(min=3, max=3)),
    vol.Optional(ATTR_COLOR4): vol.All(list, vol.Length(min=3, max=3)),
    vol.Optional(ATTR_COLOR5): vol.All(list, vol.Length(min=3, max=3)),
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Light Animation services."""

    # Register services
    async def service_handler(call: ServiceCall) -> None:
        """Handle the services."""
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

        elif call.service == SERVICE_SET_COLORS:
            # Get all light entities from the call
            target_entities = call.data.get(ATTR_ENTITY_ID)
            # Build list of colors and their indices
            colors = []
            for i, color_attr in enumerate([ATTR_COLOR1, ATTR_COLOR2, ATTR_COLOR3, ATTR_COLOR4, ATTR_COLOR5]):
                if color_attr in call.data:
                    colors.append({
                        'rgb_color': call.data[color_attr],
                        'colors_index': i
                    })

            for entity_id in target_entities:
                entity = hass.data[LIGHT_DOMAIN].get_entity(entity_id)
                if entity and hasattr(entity, "async_turn_on"):
                    # Handle color updates
                    if colors:
                        await entity.async_turn_on(colors=colors)
                else:
                    _LOGGER.warning(
                        "Entity %s doesn't support color adjustment",
                        entity_id
                    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ANIMATION_SPEED,
        service_handler,
        schema=SERVICE_SCHEMA_ANIMATION_SPEED,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COLORS,
        service_handler,
        schema=SERVICE_SCHEMA_SET_COLORS,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    # Unregister services
    hass.services.async_remove(DOMAIN, SERVICE_SET_ANIMATION_SPEED)
    hass.services.async_remove(DOMAIN, SERVICE_SET_COLORS)
