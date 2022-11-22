from __future__ import annotations

import typing

from velum import entity_factory
from velum.events import message_events

if typing.TYPE_CHECKING:
    from velum import gateway


class EventFactory:

    __slots__ = ("_entity_factory",)

    def __init__(self, entity_factory: entity_factory.EntityFactory):
        self._entity_factory = entity_factory

    def deserialize_message_create_event(
        self, gateway_connection: gateway.GatewayHandler, payload: typing.Dict[str, typing.Any]
    ) -> message_events.MessageCreateEvent:
        return message_events.MessageCreateEvent(
            message=self._entity_factory.deserialize_message(payload)
        )
