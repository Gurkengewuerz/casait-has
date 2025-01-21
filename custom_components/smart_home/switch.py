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
        if device["device_type"] in ["switch", "pushbutton"]:
            if device["module_type"] == "digital":
                # Create two switches for port A and B
                entities.append(SmartHomeDigitalSwitch(coordinator, device_id, "port_a"))
                entities.append(SmartHomeDigitalSwitch(coordinator, device_id, "port_b"))
            else:
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


class SmartHomeDigitalSwitch(SmartHomeEntity, SwitchEntity):
    """Representation of a Smart Home digital switch."""

    def __init__(self, coordinator, device_id, port_name):
        super().__init__(coordinator, device_id)
        self._port_name = port_name
        self._attr_name = port_name.replace("_", " ").title()
        _LOGGER.debug("Initialized switch digital switch %s port %s", self.device_data["name"], self.name)

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return self.device_data["uuid"] + "_" + self._port_name

    @property
    def is_on(self) -> bool | None:
        """Return if the switch is on."""
        if not self.device_state or "multistate" not in self.device_state:
            return None

        if self._port_name == "port_a":
            return self.device_state["multistate"]["port_a"]
        return self.device_state["multistate"]["port_b"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        state = {}

        if self._port_name == "port_a":
            state["port_a"] = True
        else:
            state["port_b"] = True

        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json=state) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn on switch: %s", response.status)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        state = {}

        if self._port_name == "port_a":
            state["port_a"] = False
        else:
            state["port_b"] = False

        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json=state) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn off switch: %s", response.status)
