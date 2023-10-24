import typing

from velum.api import gateway_trait
from velum.events import connection_events
from velum.events import message_events
from velum.events import user_events
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("EventFactory",)


@typing.runtime_checkable
class EventFactory(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    def deserialize_message_create_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> message_events.MessageCreateEvent:
        ...

    def deserialize_hello_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> connection_events.HelloEvent:
        ...

    def deserialize_ratelimit_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> connection_events.RatelimitEvent:
        ...

    def deserialize_authenticated_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> connection_events.AuthenticatedEvent:
        ...

    def deserialize_user_update_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> user_events.UserUpdateEvent:
        ...

    def deserialize_presence_update_event(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> user_events.PresenceUpdateEvent:
        ...
