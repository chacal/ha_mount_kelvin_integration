import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .communicator import MountKelvinCommunicator
from .const import DOMAIN, COMMUNICATOR_KEY
from .domain import MountKelvinScene

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string
            },
        )
    },
    extra=vol.ALLOW_EXTRA
)

PLATFORMS = ["light", "scene"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    _LOGGER.info('Starting Mount Kelvin integration..')

    comms = MountKelvinCommunicator(hass, config[DOMAIN][CONF_API_KEY])

    hass.data[DOMAIN] = {
        COMMUNICATOR_KEY: comms
    }

    for platform in PLATFORMS:
        hass.helpers.discovery.load_platform(platform, DOMAIN, {}, config)

    await comms.connect()

    return True
