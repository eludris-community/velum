import typing

from velum.api import event_factory_trait
from velum.api import gateway_trait
from velum.events import connection_events
from velum.events import message_events
from velum.impl import event_manager_base
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("EventManager",)


class EventManager(event_manager_base.EventManagerBase):
    __slots__ = ("_event_factory",)

    def __init__(self, event_factory: event_factory_trait.EventFactory):
        super().__init__()
        self._event_factory = event_factory

    @event_manager_base.is_consumer_for(message_events.MessageCreateEvent)
    async def on_message_create(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        await self.dispatch(
            self._event_factory.deserialize_message_create_event(gateway_connection, payload)
        )

    @event_manager_base.is_consumer_for(connection_events.HelloEvent)
    async def on_hello(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        await self.dispatch(
            self._event_factory.deserialize_hello_event(gateway_connection, payload)
        )

    @event_manager_base.is_consumer_for(connection_events.RatelimitEvent)
    async def on_ratelimit(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        await self.dispatch(
            self._event_factory.deserialize_ratelimit_event(gateway_connection, payload)
        )

    @event_manager_base.is_consumer_for(connection_events.AuthenticatedEvent)
    async def on_authenticated(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        await self.dispatch(
            self._event_factory.deserialize_authenticated_event(gateway_connection, payload)
        )
