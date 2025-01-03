"""Support for Smart Home blinds."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
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
    """Set up Smart Home covers."""
    coordinator: SmartHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    for device_id, device in coordinator._devices.items():
        if device["device_type"] == "blind":
            entities.append(SmartHomeCover(coordinator, device_id))

    async_add_entities(entities)

class SmartHomeCover(SmartHomeEntity, CoverEntity):
    """Representation of a Smart Home cover."""

    def __init__(
        self,
        coordinator: SmartHomeDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator, device_id)
        
        # Set supported features based on position control capability
        if self.device_data.get("can_use_positions", False):
            self._attr_supported_features = CoverEntityFeature.SET_POSITION
        else:
            self._attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if self.device_data.get("can_use_positions", False):
            await self._async_set_cover_position(100)
        else:
            async with aiohttp.ClientSession() as session:
                url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
                async with session.put(url, json={"position": 100}) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to open cover: %s", response.status)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        if self.device_data.get("can_use_positions", False):
            await self._async_set_cover_position(0)
        else:
            async with aiohttp.ClientSession() as session:
                url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
                async with session.put(url, json={"position": 0}) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to close cover: %s", response.status)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json={"position": -1}) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to stop cover: %s", response.status)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if not self.device_data.get("can_use_positions", False):
            _LOGGER.warning("Trying to set position for a blind that doesn't support position control")
            return
            
        position = kwargs.get("position", 0)
        await self._async_set_cover_position(position)

    async def _async_set_cover_position(self, position: int) -> None:
        """Helper to set cover position."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json={"position": position}) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set cover position: %s", response.status)

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover."""
        position = self.device_state.get("position")
        if position is None or position == -1:
            return None
        return position

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        position = self.current_cover_position
        if position is None:
            return None
        return position == 0

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        if self.device_data.get("moving", False):
            if self.device_data.get("can_use_positions", False):
                return self.device_state.get("position", 0) > self.device_data.get("current_position", 0)
            else:
                # For non-position blinds, check if moving up
                return self.device_state.get("position", 0) == 100
        return False

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        if self.device_data.get("moving", False):
            if self.device_data.get("can_use_positions", False):
                return self.device_state.get("position", 0) < self.device_data.get("current_position", 0)
            else:
                # For non-position blinds, check if moving down
                return self.device_state.get("position", 0) == 0
        return False