"""DataUpdateCoordinator for Smart Home integration."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import websocket
import threading

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SmartHomeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        config: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize."""
        self.config = config
        self.api_url = f"http://{config[CONF_HOST]}:{config[CONF_PORT]}"
        self.ws_url = f"ws://{config[CONF_HOST]}:{config[CONF_PORT]}/ws"
        self.ws = None
        self.ws_thread = None
        self.entry_id = entry_id
        self._devices = {}
        self._device_states = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),  # Fallback update interval
        )

        self._start_ws_client()

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/devices") as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error communicating with API: {response.status}")
                    devices = await response.json()
                    
                    # Update internal device cache
                    new_devices = {}
                    for device in devices:
                        if not device["enabled"]:
                            continue
                        new_devices[str(device["id"])] = device
                    self._devices = new_devices
                    return self._devices
                    
        except aiohttp.ClientError as error:
            raise UpdateFailed(f"Error communicating with API: {error}")

    @callback
    def async_device_state_update(self, msg: dict[str, Any]) -> None:
        """Process device state update from WebSocket."""
        if msg["type"] == "device_update":
            device_id = str(msg["device_id"])
            if device_id in self._devices:
                self._device_states[device_id] = msg["state"]
                self.async_set_updated_data(self._devices)
        elif msg["type"] == "initial_states":
            for state in msg["states"]:
                device_id = str(state["device_id"])
                self._device_states[device_id] = state["state"]
            self.async_set_updated_data(self._devices)

    def _ws_connect(self) -> None:
        """Connect to WebSocket in a separate thread."""
        _LOGGER.info("Connecting to WebSocket")
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self._ws_message,
            on_error=self._ws_error,
            on_close=self._ws_close,
        )
        self.ws.run_forever()

    def _ws_message(self, _, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            msg = json.loads(message)
            self.hass.add_job(self.async_device_state_update, msg)
        except json.JSONDecodeError:
            _LOGGER.error("Failed to parse WebSocket message")

    def _ws_error(self, _, error: Any) -> None:
        """Handle WebSocket error."""
        _LOGGER.error("WebSocket error: %s", error)

    def _ws_close(self, *args: Any) -> None:
        """Handle WebSocket close."""
        _LOGGER.warning("WebSocket connection closed")
        # Attempt to reconnect after a delay
        self.hass.loop.call_later(30, self._start_ws_client)

    def _start_ws_client(self) -> None:
        """Start WebSocket client in a separate thread."""
        if self.ws_thread is not None and self.ws_thread.is_alive():
            _LOGGER.warning("WebSocket client already running")
            return

        _LOGGER.info("Starting WebSocket client")
        self.ws_thread = threading.Thread(target=self._ws_connect, daemon=True)
        self.ws_thread.start()

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.ws:
            self.ws.close()
