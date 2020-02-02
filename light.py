import logging
from dataclasses import dataclass
from typing import Set, Optional

import aiohttp
import socketio
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    PLATFORM_SCHEMA, Light, SUPPORT_BRIGHTNESS)
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry
from homeassistant.helpers.typing import HomeAssistantType, ConfigType

_LOGGER = logging.getLogger(__name__)
_IO_LOGGER = logging.getLogger(__name__ + "-socketio")
_IO_LOGGER.setLevel(logging.WARNING)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
})


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
        entities = entity_platform.current_platform.get().entities
        registry = await entity_registry.async_get_registry(hass)
        for light in lights:
            entity_id = registry.async_get_entity_id('light', 'mount_kelvin', light.unique_id)
            if entity_id and entity_id in entities:
                entity = entities[entity_id]
                if entity.update_from(light):
                    _LOGGER.debug('Updating %s' % entity.name)
                    hass.async_create_task(entity.async_update_ha_state())
            else:
                _LOGGER.debug('Not found %s' % light.unique_id)

    mt_kelvin = MountKelvinCommunicator(hass, config[CONF_API_KEY], lights_updated)
    await mt_kelvin.connect()


class MountKelvinCommunicator:
    BASE_URL = 'https://api.mountkelvin.com'

    def __init__(self, hass, api_key, lights_updated):
        self._hass = hass
        self._api_key = api_key
        self._lights_updated = lights_updated
        self._http_session = aiohttp.ClientSession()

    async def connect(self):
        sio = socketio.AsyncClient(logger=_IO_LOGGER, engineio_logger=_IO_LOGGER)

        @sio.event
        def connect():
            _LOGGER.info("Connected to Mount Kelvin API")
            self._hass.async_create_task(sio.emit('subscribe', {'siteKey': self._api_key}))

        @sio.event
        def disconnect():
            _LOGGER.info("Disconnected from Mount Kelvin")

        @sio.on('site')
        async def site(event):
            lights = parse_site(event['data'], self)
            await self._lights_updated(lights)

        await sio.connect(self.BASE_URL)

    async def turn_on(self, light: 'MountKelvinLight', brightness: int):
        _LOGGER.debug('Turn on: %s Brightness: %s' % (light.name, brightness))
        req = {
            'id': light.unique_id,
            'state': {
                'on': True,
                'bri': brightness
            }
        }
        await self._http_session.post(self._apply_device_url(), json=req)

    async def turn_off(self, light: 'MountKelvinLight'):
        _LOGGER.debug('Turn off: %s' % light.name)
        req = {
            'id': light.unique_id,
            'state': {
                'on': False,
            }
        }
        await self._http_session.post(self._apply_device_url(), json=req)

    def _apply_device_url(self):
        return self.BASE_URL + '/api/site/' + self._api_key + '/applyDevice'


class MountKelvinLight(Light):
    def __init__(self, light_id, light_type, name, state, brightness, room_name, communicator: MountKelvinCommunicator):
        self._id = light_id
        self._type = light_type
        self._name = name
        self._state = state
        self._brightness = brightness
        self._room_name = room_name
        self._communicator = communicator

    @property
    def name(self):
        return self._name + ' (' + self._room_name + ')' if self._room_name else self._name

    @property
    def unique_id(self) -> Optional[str]:
        return self._id

    @property
    def is_on(self) -> bool:
        return self._state

    @property
    def brightness(self) -> Optional[int]:
        return self._brightness

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def supported_features(self):
        if self._type == 'dimmable':
            return SUPPORT_BRIGHTNESS
        return 0

    async def async_turn_on(self, **kwargs):
        await self._communicator.turn_on(self, kwargs.get('brightness', 255))

    async def async_turn_off(self, **kwargs):
        await self._communicator.turn_off(self)

    def update_from(self, other: 'MountKelvinLight') -> bool:
        if not self.equals(other):
            assert self._id == other._id, 'Only same light can be updated!'
            self._type = other._type
            self._name = other._name
            self._state = other._state
            self._brightness = other._brightness
            return True
        else:
            return False

    def equals(self, other: 'MountKelvinLight') -> bool:
        return self._id == other._id and self._type == other._type and \
               self._name == other._name and self._state == other._state and \
               self._brightness == other._brightness


@dataclass
class MountKelvinRoom:
    id: str
    name: str


def parse_site(site, communicator: MountKelvinCommunicator):
    rooms = parse_rooms(site['locations']['rooms'])
    return parse_lights(site['devices'], rooms, communicator)


def parse_lights(devices, rooms: [MountKelvinRoom], communicator: MountKelvinCommunicator):
    return [MountKelvinLight(
        device['id'],
        device['type'],
        device['name'],
        device['state']['on'],
        device['state'].get('bri', None),
        next((room.name for room in rooms if room.id == device['roomId']), None),
        communicator
    ) for device in devices]


def parse_rooms(rooms):
    return [MountKelvinRoom(
        room['id'],
        room['name']
    ) for room in rooms]
