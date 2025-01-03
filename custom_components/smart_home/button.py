"""Support for Smart Home pushbuttons."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DATA_COORDINATOR
from .coordinator import SmartHomeDataUpdateCoordinator
from .entity import SmartHomeEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Home buttons."""
    coordinator: SmartHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    #for device_id, device in coordinator._devices.items():
    #    if device["device_type"] == "pushbutton":
    #        entities.append(SmartHomeButton(coordinator, device_id))

    async_add_entities(entities)

class SmartHomeButton(SmartHomeEntity, ButtonEntity):
    """Representation of a Smart Home button."""

    async def async_press(self) -> None:
        """Press the button."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json={"state": True}) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to press button: %s", response.status)
