"""Support for Smart Home sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
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
    """Set up Smart Home sensors."""
    coordinator: SmartHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    for device_id, device in coordinator._devices.items():
        if device["device_type"] == "sensor":
            if device.get("onewire_conversion_type") == "DS2438TEMP":
                entities.append(SmartHomeTemperatureSensor(coordinator, device_id))
            elif device.get("onewire_type") == "DS18XB20":
                entities.append(SmartHomeTemperatureSensor(coordinator, device_id))
            elif device.get("onewire_conversion_type") in ["HIH4030", "HIH5030"]:
                entities.append(SmartHomeHumiditySensor(coordinator, device_id))
            elif device.get("onewire_conversion_type") == "TEPT5600":
                entities.append(SmartHomeLightSensor(coordinator, device_id))
            else:
                entities.append(SmartHomeGenericSensor(coordinator, device_id))

    async_add_entities(entities)

class SmartHomeTemperatureSensor(SmartHomeEntity, SensorEntity):
    """Representation of a Smart Home temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        return self.device_state.get("value")

class SmartHomeHumiditySensor(SmartHomeEntity, SensorEntity):
    """Representation of a Smart Home humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        return self.device_state.get("value")

class SmartHomeLightSensor(SmartHomeEntity, SensorEntity):
    """Representation of a Smart Home light sensor."""

    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "lx"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        return self.device_state.get("value")

class SmartHomeGenericSensor(SmartHomeEntity, SensorEntity):
    """Representation of a Smart Home generic sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        return self.device_state.get("value")

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.device_state.get("unit")
