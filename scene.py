import logging

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from . import DOMAIN, COMMUNICATOR_KEY
from .platform import MountKelvinPlatform

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType, async_add_entities: AddEntitiesCallback,
                               discovery_info=None):
    _LOGGER.info("Starting Mount Kelvin scene platform..")

    scene_platformm = MountKelvinPlatform('scene', hass, async_add_entities)
    hass.data[DOMAIN][COMMUNICATOR_KEY].set_scenes_update_callback(scene_platformm.entities_updated)
