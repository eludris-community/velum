import typing

from velum.events import message_events
from velum.traits import gateway_trait as gateway_trait


class EventFactory(typing.Protocol):

    __slots__: typing.Sequence[str] = ()

    def deserialize_message_create_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: typing.Dict[str, typing.Any],
    ) -> message_events.MessageCreateEvent:
        ...
