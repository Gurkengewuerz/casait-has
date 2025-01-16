"""The Smart Home integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, CONF_NAME, ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

from .const import (
    DOMAIN,
    DATA_COORDINATOR,
    DATA_CONFIG,
    DEFAULT_PORT, SERVICE_SET_ANIMATION_SPEED, SERVICE_SCHEMA_ANIMATION_SPEED, ATTR_SPEED,
)
from .coordinator import SmartHomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.BUTTON,
    Platform.COVER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Home from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = SmartHomeDataUpdateCoordinator(
        hass,
        config=entry.data,
        entry_id=entry.entry_id,
    )
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_CONFIG: entry.data,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator: SmartHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        await coordinator.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services
        hass.services.async_remove(DOMAIN, SERVICE_SET_ANIMATION_SPEED)

    return unload_ok
