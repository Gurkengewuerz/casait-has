"""Base entity for Smart Home integration."""
from __future__ import annotations

import logging

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartHomeDataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)


class SmartHomeEntity(CoordinatorEntity):
    """Base class for Smart Home entities."""

    def __init__(
        self,
        coordinator: SmartHomeDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": self.device_data["name"],
            "manufacturer": "casaIT",
            "model": self.device_data["device_type"],
            "via_device": (DOMAIN, coordinator.entry_id),
        }

    @property
    def device_data(self) -> dict:
        """Get device data."""
        return self.coordinator._devices[self._device_id]

    @property
    def device_state(self) -> dict:
        """Get device state."""
        return self.coordinator._device_states.get(self._device_id, {})

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._device_id in self.coordinator._devices

    @property
    def name(self):
        """Name of the sensor"""
        return self.device_data["name"]

    @property
    def unique_id(self):
        """ID of the sensor"""
        return f'casait_{self.device_data["id"]}_{self.device_data["uuid"]}'

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
