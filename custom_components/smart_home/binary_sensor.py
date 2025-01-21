"""Support for Smart Home binary sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up Smart Home binary sensors."""
    coordinator: SmartHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    for device_id, device in coordinator._devices.items():
        if device["device_type"] == "binary_sensor":
            if device["module_type"] == "digital":
                # Create two binary sensors for port A and B
                entities.append(SmartHomeDigitalBinarySensor(coordinator, device_id, "port_a"))
                entities.append(SmartHomeDigitalBinarySensor(coordinator, device_id, "port_b"))
            else:
                entities.append(SmartHomeBinarySensor(coordinator, device_id))

    async_add_entities(entities)

class SmartHomeBinarySensor(SmartHomeEntity, BinarySensorEntity):
    """Representation of a Smart Home binary sensor."""

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.device_state.get("state", False)


class SmartHomeDigitalBinarySensor(SmartHomeEntity, BinarySensorEntity):
    """Representation of a Smart Home digital binary sensor."""

    def __init__(self, coordinator, device_id, port_name):
        super().__init__(coordinator, device_id)
        self._port_name = port_name
        self._attr_name = port_name.replace("_", " ").title()
        _LOGGER.debug("Initialized digital sensor %s port %s", self.device_data["name"], self.name)

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return self.device_data["uuid"] + "_" + self._port_name

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.device_state or "multistate" not in self.device_state:
            return None

        # Check relevant port state
        if self._port_name == "port_a":
            return self.device_state["multistate"]["port_a"]
        return self.device_state["multistate"]["port_b"]
