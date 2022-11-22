import typing

from velum.events import message_events
from velum.internal import data_binding
from velum.traits import gateway_trait as gateway_trait


class EventFactory(typing.Protocol):

    __slots__: typing.Sequence[str] = ()

    def deserialize_message_create_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> message_events.MessageCreateEvent:
        ...
