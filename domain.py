from dataclasses import dataclass
from typing import Optional

from homeassistant.components.light import (LightEntity, SUPPORT_BRIGHTNESS)


class MountKelvinLight(LightEntity):
    def __init__(self, light_id, light_type, name, state, brightness, room_name, communicator):
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
        bri = kwargs.get('brightness', self._brightness)
        await self._communicator.turn_on(self, bri if bri else 255)

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
