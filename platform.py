import logging
from typing import List, Tuple, Set

from custom_components.mount_kelvin import DOMAIN
from homeassistant.helpers import entity_platform, entity_registry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType

_LOGGER = logging.getLogger(__name__)


class MountKelvinPlatform:
    def __init__(self, platform_type: str, hass: HomeAssistantType, async_add_entities: AddEntitiesCallback):
        self._platform_type = platform_type
        self._hass = hass
        self._async_add_entities = async_add_entities
        self._tracked: Set[str] = set()

    async def entities_updated(self, entities):
        self._add_new_entities(entities)
        await self._update_existing_entities(entities)

    def _add_new_entities(self, entities):
        new_entities = [entity for entity in entities if not entity.unique_id in self._tracked]
        for entity in new_entities:
            self._tracked.add(entity.unique_id)

        self._async_add_entities(new_entities)

    async def _update_existing_entities(self, entities):
        matched = await self._match_existing_entities_for(self._hass, entities)
        for (existing_entity, new_entity) in matched:
            if existing_entity.update_from(new_entity):
                _LOGGER.debug('Updating %s' % existing_entity.name)
                self._hass.async_create_task(existing_entity.async_update_ha_state())

    async def _match_existing_entities_for(self, hass, new_entities) -> List[Tuple[Entity, Entity]]:
        platforms = entity_platform.async_get_platforms(hass, DOMAIN)
        platform = next(plat for plat in platforms if self._platform_type in plat.platform.__name__)
        old_entities = platform.entities
        registry = await entity_registry.async_get_registry(hass)

        ret = []
        for entity in new_entities:
            entity_id = registry.async_get_entity_id(self._platform_type, DOMAIN, entity.unique_id)
            if entity_id and entity_id in old_entities:
                ret.append((old_entities[entity_id], entity))

        return ret
