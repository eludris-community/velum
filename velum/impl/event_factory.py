from __future__ import annotations

import typing

from velum.events import message_events
from velum.internal import data_binding
from velum.traits import entity_factory_trait
from velum.traits import event_factory_trait
from velum.traits import gateway_trait

__all__: typing.Sequence[str] = ("EventFactory",)


class EventFactory(event_factory_trait.EventFactory):

    __slots__ = ("_entity_factory",)

    def __init__(self, entity_factory: entity_factory_trait.EntityFactory):
        self._entity_factory = entity_factory

    def deserialize_message_create_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> message_events.MessageCreateEvent:
        return message_events.MessageCreateEvent(
            message=self._entity_factory.deserialize_message(payload)
        )
