"""Sensor entities for the Pelastustoimi integration.

One sensor per configured municipality, each showing the alarm count
and listing alarm details in attributes.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_ALARMS,
    CONF_MUNICIPALITIES,
    COORDINATOR,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pelastustoimi sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    municipalities: list[str] = entry.options.get(CONF_MUNICIPALITIES, [])

    entities = [
        PelastustoimiSensor(coordinator, entry, label)
        for label in municipalities
    ]
    async_add_entities(entities)


class PelastustoimiSensor(SensorEntity):
    """Sensor for a single municipality's alarms."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        municipality_label: str,
    ) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._entry = entry
        self._municipality_label = municipality_label

        # Parse FI name for display
        if "/" in municipality_label:
            self._fi_name = municipality_label.split("/", 1)[0].strip()
        else:
            self._fi_name = municipality_label

        self._attr_name = f"{self._fi_name} Pelastustoimi"
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_{self._fi_name.lower()}"
        )
        self._attr_icon = "mdi:siren"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Pelastustoimi",
            manufacturer="Suomen Pelastustoimi",
            model="Peto-media RSS",
            sw_version="1.0.0",
        )

    async def async_added_to_hass(self) -> None:
        """Register the dispatcher update signal."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self._entry.entry_id}_update",
                self._async_handle_update,
            )
        )
        # Also update on home assistant start if data exists
        await self._async_handle_update()

    @callback
    async def _async_handle_update(self) -> None:
        """Update sensor state from coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        """Return the number of stored alarms for this municipality."""
        alarms = self._coordinator.alarms.get(self._municipality_label, [])
        return len(alarms)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return alarm details as attributes."""
        alarms = self._coordinator.alarms.get(self._municipality_label, [])
        return {
            ATTR_ALARMS: alarms,
        }
