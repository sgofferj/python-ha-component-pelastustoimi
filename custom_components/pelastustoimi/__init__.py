"""Entry lifecycle for the Pelastustoimi integration.

Polls the Pelastustoimi RSS feed and creates sensor entities per municipality.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import feedparser
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_DESCRIPTION,
    ATTR_INCIDENT_TYPE,
    ATTR_MUNICIPALITY,
    ATTR_MUNICIPALITY_FI,
    ATTR_MUNICIPALITY_SE,
    ATTR_PUB_DATE,
    ATTR_TITLE,
    CONF_INTERVAL,
    CONF_MAX_ALARMS,
    CONF_MUNICIPALITIES,
    COORDINATOR,
    DEFAULT_INTERVAL,
    DEFAULT_MAX_ALARMS,
    DOMAIN,
    EVENT_NEW_ALARM,
    RSS_URL,
)
_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 2
STORAGE_KEY = f"{DOMAIN}.alarm_store"

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({})},
    extra=vol.ALLOW_EXTRA,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pelastustoimi from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PelastustoimiCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    await coordinator.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN][entry.entry_id].get(COORDINATOR)
        if coordinator:
            coordinator.async_unload()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


class PelastustoimiCoordinator:
    """Polls the Pelastustoimi RSS feed and manages alarm data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry

        interval_min = entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL)
        self._interval = timedelta(minutes=max(interval_min, 1))

        self._max_alarms = max(
            entry.options.get(CONF_MAX_ALARMS, DEFAULT_MAX_ALARMS),
            1,
        )
        self._municipalities: list[str] = entry.options.get(
            CONF_MUNICIPALITIES, []
        )

        # Parsed municipality cache: label -> (fi_name, se_name)
        self._municipality_names: dict[str, tuple[str, str]] = {}
        for label in self._municipalities:
            if "/" in label:
                fi, se = label.split("/", 1)
                self._municipality_names[label] = (fi.strip(), se.strip())

        # Seen alarm keys per municipality: {municipality_label: set(alarm_key)}
        self._seen_alarms: dict[str, set[str]] = {}

        # Current alarms per municipality: {municipality_label: list[dict]}
        self.alarms: dict[str, list[dict[str, Any]]] = {}

        # Persistent store for seen alarm keys and alarm data (survives restarts)
        self._store = Store[dict[str, Any]](
            self.hass, STORAGE_VERSION, f"{STORAGE_KEY}.{self.entry.entry_id}"
        )
        self._remove_interval: callable | None = None

    async def async_setup(self) -> None:
        """Set up polling. Loads persisted seen-alarms and alarm data before first poll."""
        # Restore seen alarm keys and alarm data from store
        stored = await self._store.async_load()
        if stored:
            for label, value in stored.items():
                if isinstance(value, list):
                    # v1 format: just seen alarm keys, no alarm data.
                    # Don't load — let the first poll re-process everything.
                    self._seen_alarms.clear()
                    self.alarms.clear()
                    _LOGGER.warning(
                        "Migrating from v1 store format: alarm data will be "
                        "re-fetched on next poll"
                    )
                    break
                # v2 format: both seen keys and alarm data
                self._seen_alarms[label] = set(value.get("seen", []))
                self.alarms[label] = value.get("alarms", [])[: self._max_alarms]
            else:
                _LOGGER.debug(
                    "Loaded %d municipality alarm records from store",
                    len(stored),
                )

        async def _initial_poll(_: Event | None = None) -> None:
            await self._async_update()
            self._remove_interval = async_track_time_interval(
                self.hass, self._async_update, self._interval
            )

        if self.hass.is_running:
            await _initial_poll(None)
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, _initial_poll
            )

    @callback
    def async_unload(self) -> None:
        """Remove the interval timer."""
        if self._remove_interval:
            self._remove_interval()
            self._remove_interval = None

    async def _async_update(self, now: datetime | None = None) -> None:
        """Fetch RSS feed and process alarms."""
        _LOGGER.debug("Polling Pelastustoimi RSS feed")

        try:
            feed = await self.hass.async_add_executor_job(
                feedparser.parse, RSS_URL
            )
        except Exception as err:
            _LOGGER.warning("Failed to fetch RSS feed: %s", err)
            return

        if not feed or not feed.get("entries"):
            _LOGGER.warning("RSS feed returned no entries")
            return

        _alarms_added = 0

        for item in feed.entries:
            title = item.get("title", "")
            description = item.get("description", "")
            pub_date_str = item.get("published", "")

            # Parse municipality from title: "{FI}/{SE}, {incident_type}"
            municipality = self._parse_municipality(title)
            if not municipality:
                continue

            label = municipality  # e.g. "Espoo/Esbo"
            if label not in self._municipality_names:
                continue

            fi_name, se_name = self._municipality_names[label]

            # Parse incident type
            incident_type = self._parse_incident_type(title)

            alarm_key = f"{title}|{pub_date_str}"

            alarm_data: dict[str, Any] = {
                ATTR_TITLE: title,
                ATTR_DESCRIPTION: description,
                ATTR_PUB_DATE: pub_date_str,
                ATTR_MUNICIPALITY: label,
                ATTR_MUNICIPALITY_FI: fi_name,
                ATTR_MUNICIPALITY_SE: se_name,
                ATTR_INCIDENT_TYPE: incident_type,
            }

            # Track seen alarms per municipality
            if label not in self._seen_alarms:
                self._seen_alarms[label] = set()
                self.alarms[label] = []

            # Check if this is a new alarm
            is_new = alarm_key not in self._seen_alarms[label]

            if is_new:
                _alarms_added += 1
                self._seen_alarms[label].add(alarm_key)
                self.alarms[label].insert(0, alarm_data)

                # Enforce maximum kept alarms per municipality
                while len(self.alarms[label]) > self._max_alarms:
                    self.alarms[label].pop()

                _LOGGER.debug(
                    "New alarm in %s: %s (%s)", label, title, incident_type
                )

                # Fire event for new alarm
                self.hass.bus.async_fire(
                    EVENT_NEW_ALARM,
                    {
                        ATTR_MUNICIPALITY: label,
                        ATTR_MUNICIPALITY_FI: fi_name,
                        ATTR_MUNICIPALITY_SE: se_name,
                        ATTR_TITLE: title,
                        ATTR_DESCRIPTION: description,
                        ATTR_PUB_DATE: pub_date_str,
                        ATTR_INCIDENT_TYPE: incident_type,
                    },
                )

        if _alarms_added > 0:
            # Persist seen alarm keys and alarm data to survive restarts
            store_data: dict[str, dict[str, Any]] = {}
            for label, seen_set in self._seen_alarms.items():
                store_data[label] = {
                    "seen": sorted(seen_set),
                    "alarms": self.alarms.get(label, []),
                }
            await self._store.async_save(store_data)
            _LOGGER.debug(
                "Saved %d municipality alarm records to store",
                len(store_data),
            )

        # Notify sensor entities to update
        async_dispatcher_send(
            self.hass, f"{DOMAIN}_{self.entry.entry_id}_update"
        )

        _LOGGER.debug(
            "RSS poll complete: %d municipalities tracked",
            len(self.alarms),
        )

    def _parse_municipality(self, title: str) -> str | None:
        """Extract the municipality portion from an RSS title.

        Title format: "{NAMEFIN}/{NAMESWE}, {incident_type}"
        Returns the "{NAMEFIN}/{NAMESWE}" label or None.
        """
        if not title or ", " not in title:
            return None
        municipality_part = title.split(", ", 1)[0]
        if "/" not in municipality_part:
            return None
        return municipality_part.strip()

    def _parse_incident_type(self, title: str) -> str:
        """Extract the incident type from an RSS title."""
        if not title or ", " not in title:
            return title or ""
        return title.split(", ", 1)[1].strip()
