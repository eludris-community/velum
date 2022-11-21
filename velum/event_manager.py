import typing

from velum import event_manager_base
from velum import gateway
from velum import models
from velum.events import message_events


# TODO: replace with standalone event factory
def _message_factory(payload: typing.Dict[str, typing.Any]) -> message_events.MessageCreateEvent:
    message = models.Message(
        content=payload["content"],
        author=payload["author"],
    )
    return message_events.MessageCreateEvent(message=message)


class EventManager(event_manager_base.EventManagerBase):
    @event_manager_base.is_consumer_for(message_events.MessageCreateEvent)
    async def on_message_create(
        self,
        gateway_connection: gateway.GatewayHandler,
        payload: typing.Dict[str, typing.Any],
    ) -> None:
        await self.dispatch(_message_factory(payload))
