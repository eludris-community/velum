import asyncio
import typing

from velum.api import gateway_trait
from velum.events import base_events
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("EventManager",)


EventPredicateT = typing.Callable[[base_events.EventT], bool]


@typing.runtime_checkable
class EventManager(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    def consume_raw_event(
        self,
        event_name: str,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        ...

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        ...

    def subscribe(
        self,
        event_type: typing.Type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        ...

    def unsubscribe(
        self,
        event_type: typing.Type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        ...

    def get_listeners(
        self, event_type: typing.Type[base_events.EventT], /, *, polymorphic: bool = True
    ) -> typing.Collection[base_events.EventCallbackT[base_events.EventT]]:
        ...

    def listen(
        self,
        *event_types: typing.Type[base_events.EventT],
    ) -> typing.Callable[
        [base_events.EventCallbackT[base_events.EventT]],
        base_events.EventCallbackT[base_events.EventT],
    ]:
        ...

    async def wait_for(
        self,
        event_type: typing.Type[base_events.EventT],
        /,
        *,
        timeout: typing.Optional[float | int] = None,
        predicate: typing.Optional[EventPredicateT[base_events.EventT]] = None,
    ) -> base_events.EventT:
        ...
