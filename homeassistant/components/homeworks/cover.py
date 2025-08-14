"""Support for Lutron Homeworks covers."""

from __future__ import annotations

import logging
from typing import Any

from pyhomeworks.pyhomeworks import HW_LIGHT_CHANGED, Homeworks

from homeassistant.components.cover import CoverEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HomeworksConfigEntry
from .const import CONF_ADDR, CONF_CONTROLLER_ID, CONF_COVERS, DOMAIN
from .entity import HomeworksEntity

_LOGGER = logging.getLogger(__name__)

COVER_STOP = 0
COVER_RAISE = 16
COVER_LOWER = 35

async def async_setup_entry(
    hass: HomeAssistant,
    entry: HomeworksConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Homeworks covers."""
    controller = entry.runtime_data.controller
    controller_id = entry.options[CONF_CONTROLLER_ID]
    entities = []
    for cover in entry.options.get(CONF_COVERS, []):
        entity = HomeworksCover(
            controller,
            controller_id,
            cover[CONF_ADDR],
            cover[CONF_NAME],
        )
        entities.append(entity)
    async_add_entities(entities, True)


class HomeworksCover(HomeworksEntity, CoverEntity):
    """Homeworks Cover."""

    def __init__(
        self,
        controller: Homeworks,
        controller_id: str,
        addr: str,
        name: str,
    ) -> None:
        """Create device with Addr and name."""
        super().__init__(controller, controller_id, addr, 0, None)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{controller_id}.{addr}")}, name=name
        )
        self._level: int = COVER_STOP

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        signal = self._signal_name()
        _LOGGER.debug("connecting %s", signal)
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._update_callback)
        )
        self._controller.request_dimmer_level(self._addr)

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._level == COVER_RAISE

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._level == COVER_LOWER

    def open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._set_dim(COVER_RAISE)

    def close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        self._set_dim(COVER_LOWER)

    def stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        self._set_dim(COVER_STOP)

    def _set_dim(self, level: int) -> None:
        """Send the brightness level to the device."""
        #self._controller.set_dim(level, 0, self._addr)
        self._controller.fade_dim(level, 0, 0, self._addr)

    @callback
    def _update_callback(self, msg_type: str, values: list[Any]) -> None:
        """Process device specific messages."""

        if msg_type == HW_LIGHT_CHANGED:
            self._level = values[1]
            self.async_write_ha_state()
