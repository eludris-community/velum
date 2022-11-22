import typing

from velum.events import message_events
from velum.impl import event_manager_base
from velum.traits import event_factory_trait
from velum.traits import gateway_trait


class EventManager(event_manager_base.EventManagerBase):

    __slots__ = ("_event_factory",)

    def __init__(self, event_factory: event_factory_trait.EventFactory):
        super().__init__()
        self._event_factory = event_factory

    @event_manager_base.is_consumer_for(message_events.MessageCreateEvent)
    async def on_message_create(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: typing.Dict[str, typing.Any],
    ) -> None:
        await self.dispatch(
            self._event_factory.deserialize_message_create_event(gateway_connection, payload)
        )
