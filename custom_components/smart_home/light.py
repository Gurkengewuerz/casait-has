"""Support for Smart Home RGB lights."""
from __future__ import annotations

import logging
import async_timeout
import aiohttp
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DATA_COORDINATOR
from .coordinator import SmartHomeDataUpdateCoordinator
from .entity import SmartHomeEntity

_LOGGER = logging.getLogger(__name__)


async def async_fetch_effects(api_url: str) -> dict:
    """Fetch available effects from API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                async with session.get(f"{api_url}/api/effects") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise HomeAssistantError(f"Failed to fetch effects: {response.status}")
    except Exception as e:
        raise HomeAssistantError(f"Error fetching effects: {e}")
    return {}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Home RGB lights."""
    coordinator: SmartHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    try:
        # Fetch available effects from API
        effect_map = await async_fetch_effects(coordinator.api_url)
        _LOGGER.debug("Fetched effects: %s", effect_map)

        entities = []
        for device_id, device in coordinator._devices.items():
            if device["device_type"] == "rgb_led":
                entities.append(SmartHomeLight(coordinator, device_id, effect_map))
            elif device["device_type"] == "dimmer":
                entities.append(SmartHomeDimmerLight(coordinator, device_id))

        async_add_entities(entities)
    except HomeAssistantError as e:
        _LOGGER.error("Failed to set up RGB lights: %s", e)


class SmartHomeLight(SmartHomeEntity, LightEntity):
    """Representation of a Smart Home RGB light."""

    def __init__(
        self,
        coordinator: SmartHomeDataUpdateCoordinator,
        device_id: str,
        effect_map: dict[str, str],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, device_id)
        self._effect_map = effect_map
        self._attr_supported_features |= LightEntityFeature.EFFECT

        # Set up supported features
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_color_mode = ColorMode.RGB

        # No color temperature support
        self._attr_min_mireds = 0
        self._attr_max_mireds = 0

        _LOGGER.debug("Initializing RGB light: %s id %s", device_id, self.unique_id)

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        if not self.device_state:
            return None
        return self.device_state.get("state", False)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if not self.device_state:
            return None
        brightness = self.device_state.get("brightness", 0)
        return int(brightness)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        if not self.device_state or "colors" not in self.device_state:
            return None
        # Use first color from the array
        if not self.device_state["colors"]:
            return None
        color_hex = self.device_state["colors"][0]
        # Convert hex string to RGB tuple, stripping any leading '0x'
        color_hex = color_hex.replace('0x', '')
        return (
            int(color_hex[0:2], 16),
            int(color_hex[2:4], 16),
            int(color_hex[4:6], 16),
        )

    @property
    def effect_list(self) -> list[str] | None:
        """Return the list of supported effects."""
        return list(self._effect_map.values())

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        if not self.device_state:
            return None
        animation = self.device_state.get("animation")
        # Handle mapping from API animation name to display name
        if animation in self._effect_map:
            return self._effect_map[animation]
        _LOGGER.debug("Unknown animation mode: %s", animation)
        return None

    async def set_animation_speed(self, speed: int) -> None:
        """Set the animation speed."""
        data = {
            "animation_speed": speed
        }
        _LOGGER.debug("Setting animation speed to %s", speed)
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json=data) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to update LED configuration: %s", response.status)
                    return

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        data = {
            "state": True
        }
        _LOGGER.debug("Data given in async_turn_on: %s", kwargs)
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            data["brightness"] = int(brightness)

        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            # Convert RGB values to hex string
            color_hex = f"{r:02x}{g:02x}{b:02x}"
            # Always maintain 5 colors array, set first color and pad with black
            data["colors"] = [color_hex] + ['000000'] * 4

        # Handle multiple color update from set_colors service
        elif "colors" in kwargs:
            colors = ['000000'] * 5  # Default to all black
            # Update each color at its specified index
            for color_data in kwargs["colors"]:
                r, g, b = color_data["rgb_color"]
                color_hex = f"{r:02x}{g:02x}{b:02x}"
                colors[color_data["colors_index"]] = color_hex

            data["colors"] = colors

        if ATTR_EFFECT in kwargs:
            # Convert HA effect name back to API animation mode
            effect_name = kwargs[ATTR_EFFECT]
            effect_key = list(self._effect_map.keys())[list(self._effect_map.values()).index(effect_name)]
            if effect_key is not None:
                # get effect key from value
                data["animation"] = effect_key
            else:
                _LOGGER.warning("Unknown effect name: %s (%s). Valid effects are: %s", effect_name, effect_key,
                                list(self._effect_map.keys()))

        _LOGGER.debug("Sending data to API: %s", data)
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json=data) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn on light: %s", response.status)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json={"state": False}) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn off light: %s", response.status)


class SmartHomeDimmerLight(SmartHomeEntity, LightEntity):
    """Representation of a Smart Home dimmer light."""

    def __init__(
        self,
        coordinator: SmartHomeDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, device_id)

        # Set color modes
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS

    @property
    def is_on(self) -> bool | None:
        """Return if the light is on."""
        if not self.device_state:
            return None

        if "value" in self.device_state:
            return self.device_state["value"] > 0

        return False

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        if not self.device_state or "value" not in self.device_state:
            return None

        # Convert 0-100 to 0-255 range
        return int(self.device_state["value"] * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        data = {}

        if ATTR_BRIGHTNESS in kwargs:
            # Convert brightness to percentage
            brightness = kwargs[ATTR_BRIGHTNESS]
            data["value"] = round((brightness * 100) / 255)
        else:
            data["value"] = 100

        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json=data) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn on light: %s", response.status)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.coordinator.api_url}/api/devices/{self._device_id}/state"
            async with session.put(url, json={"value": 0}) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to turn off light: %s", response.status)
