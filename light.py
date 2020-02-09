import logging
from typing import Set, Tuple, List

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry
from homeassistant.helpers.typing import HomeAssistantType, ConfigType

from .domain import MountKelvinLight
from .communicator import MountKelvinCommunicator

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
})

LightT = Tuple[MountKelvinLight, MountKelvinLight]


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info=None):
    _LOGGER.info("Initializing Mount Kelvin integration")

    tracked: Set[str] = set()

    async def lights_updated(lights):
        add_new_entities(lights)
        await update_existing_entities(lights)

    def add_new_entities(lights):
        new_entities = [light for light in lights if not light.unique_id in tracked]
        for light in new_entities:
            tracked.add(light.unique_id)

        async_add_entities(new_entities)

    async def update_existing_entities(lights):
        matched = await match_existing_entities_for(hass, lights)
        for (existing_entity, light) in matched:
            if existing_entity.update_from(light):
                _LOGGER.debug('Updating %s' % existing_entity.name)
                hass.async_create_task(existing_entity.async_update_ha_state())

    mt_kelvin = MountKelvinCommunicator(hass, config[CONF_API_KEY], lights_updated)
    await mt_kelvin.connect()


async def match_existing_entities_for(hass, lights) -> List[LightT]:
    entities = entity_platform.current_platform.get().entities
    registry = await entity_registry.async_get_registry(hass)

    ret = []
    for light in lights:
        entity_id = registry.async_get_entity_id('light', 'mount_kelvin', light.unique_id)
        if entity_id and entity_id in entities:
            ret.append((entities[entity_id], light))

    return ret
