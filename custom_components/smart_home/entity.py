"""Base entity for Smart Home integration."""
from __future__ import annotations

import logging

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo

from .const import DOMAIN
from .coordinator import SmartHomeDataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)


class SmartHomeEntity(CoordinatorEntity):
    """Base class for Smart Home entities."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: SmartHomeDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        _LOGGER.debug("Initialized entity %s", self.device_data["name"])

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return self.device_data["uuid"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this WLED device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.device_data["name"],
            manufacturer="casaIT",
            model=self.device_data["device_type"].replace("_", " ").title(),
            via_device=(DOMAIN, self.coordinator.entry_id),
        )
