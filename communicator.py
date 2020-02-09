import logging

import aiohttp
import socketio

from .domain import MountKelvinRoom, MountKelvinLight

_LOGGER = logging.getLogger(__name__)
_IO_LOGGER = logging.getLogger(__name__ + "-socketio")
_IO_LOGGER.setLevel(logging.WARNING)

BASE_URL = 'https://api.mountkelvin.com'


class MountKelvinCommunicator:

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

        await sio.connect(BASE_URL)

    async def turn_on(self, light: MountKelvinLight, brightness: int):
        _LOGGER.debug('Turn on: %s Brightness: %s' % (light.name, brightness))
        req = {
            'id': light.unique_id,
            'state': {
                'on': True,
                'bri': brightness
            }
        }
        await self._http_session.post(self._apply_device_url(), json=req)

    async def turn_off(self, light: MountKelvinLight):
        _LOGGER.debug('Turn off: %s' % light.name)
        req = {
            'id': light.unique_id,
            'state': {
                'on': False,
            }
        }
        await self._http_session.post(self._apply_device_url(), json=req)

    def _apply_device_url(self):
        return BASE_URL + '/api/site/' + self._api_key + '/applyDevice'


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
