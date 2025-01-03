"""Support for Smart Home switches."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.components.switch import SwitchEntity
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
    """Set up Smart Home switches."""
    coordinator: SmartHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    for device_id, device in coordinator._devices.items():
        if device["device_type"] == "switch" or device["device_type"] == "pushbutton":
            entities.append(SmartHomeSwitch(coordinator, device_id))

    async_add_entities(entities)

class SmartHomeSwitch(SmartHomeEntity, SwitchEntity):
    """Representation of a Smart Home switch."""

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json={"state": True}) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn on switch: %s", response.status)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json={"state": False}) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn off switch: %s", response.status)

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        return self.device_state.get("state", False)
