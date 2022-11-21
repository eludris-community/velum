import typing

from velum import event_factory
from velum import event_manager_base
from velum import gateway
from velum.events import message_events


class EventManager(event_manager_base.EventManagerBase):
    def __init__(self, event_factory: event_factory.EventFactory):
        super().__init__()
        self.event_factory = event_factory

    @event_manager_base.is_consumer_for(message_events.MessageCreateEvent)
    async def on_message_create(
        self,
        gateway_connection: gateway.GatewayHandler,
        payload: typing.Dict[str, typing.Any],
    ) -> None:
        await self.dispatch(
            self.event_factory.deserialize_message_create_event(gateway_connection, payload)
        )
