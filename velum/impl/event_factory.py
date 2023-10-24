from __future__ import annotations

import typing

from velum.api import entity_factory_trait
from velum.api import event_factory_trait
from velum.api import gateway_trait
from velum.events import connection_events
from velum.events import message_events
from velum.events import user_events
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("EventFactory",)


class EventFactory(event_factory_trait.EventFactory):
    __slots__ = ("_entity_factory",)

    def __init__(self, entity_factory: entity_factory_trait.EntityFactory) -> None:
        self._entity_factory = entity_factory

    def deserialize_ratelimit_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> connection_events.RatelimitEvent:
        return connection_events.RatelimitEvent(
            data=self._entity_factory.deserialize_ratelimit(payload),
        )

    def deserialize_hello_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> connection_events.HelloEvent:
        return connection_events.HelloEvent(data=self._entity_factory.deserialize_hello(payload))

    def deserialize_message_create_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> message_events.MessageCreateEvent:
        return message_events.MessageCreateEvent(
            message=self._entity_factory.deserialize_message(payload),
        )

    def deserialize_authenticated_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> connection_events.AuthenticatedEvent:
        return connection_events.AuthenticatedEvent(
            data=self._entity_factory.deserialize_authenticated(payload),
        )

    def deserialize_user_update_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> user_events.UserUpdateEvent:
        return user_events.UserUpdateEvent(user=self._entity_factory.deserialize_user(payload))

    def deserialize_presence_update_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> user_events.PresenceUpdateEvent:
        return user_events.PresenceUpdateEvent(
            data=self._entity_factory.deserialize_presence_update(payload),
        )
