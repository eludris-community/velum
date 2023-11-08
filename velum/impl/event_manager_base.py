from __future__ import annotations

import asyncio
import inspect
import logging
import types
import typing

import attr

from velum.api import event_manager_trait
from velum.api import gateway_trait
from velum.events import base_events
from velum.internal import async_utils
from velum.internal import class_utils
from velum.internal import data_binding

if typing.TYPE_CHECKING:
    import typing_extensions

__all__: typing.Sequence[str] = (
    "UnboundConsumerCallback",
    "Consumer",
    "is_consumer_for",
    "EventManagerBase",
)


if typing.TYPE_CHECKING:
    _ListenerMapT = dict[
        type[base_events.EventT],
        list[base_events.EventCallbackT[base_events.EventT]],
    ]
    _WaiterPairT = tuple[
        event_manager_trait.EventPredicateT[base_events.EventT] | None,
        asyncio.Future[base_events.EventT],
    ]
    _WaiterMapT = dict[
        type[base_events.EventT],
        set[_WaiterPairT[base_events.EventT]],
    ]
    ConsumerCallback = typing.Callable[
        [gateway_trait.GatewayHandler, data_binding.JSONObject],
        typing.Coroutine[typing.Any, typing.Any, None],
    ]

_EventManagerT = typing.TypeVar("_EventManagerT", bound=event_manager_trait.EventManager)
UnboundConsumerCallback = typing.Callable[
    [_EventManagerT, gateway_trait.GatewayHandler, data_binding.JSONObject],
    typing.Coroutine[typing.Any, typing.Any, None],
]


_LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)
_UNIONS = frozenset((typing.Union, types.UnionType))


def _is_exception_event(
    event: base_events.EventT,
) -> typing.TypeGuard[base_events.ExceptionEvent[base_events.EventT]]:
    if isinstance(event, base_events.ExceptionEvent):
        return True

    return False


@attr.define(weakref_slot=False)
class Consumer(typing.Generic[_EventManagerT]):
    callback: UnboundConsumerCallback[_EventManagerT] = attr.field(hash=True)
    """The callback function for this consumer."""

    events_bitmask: int = attr.field()
    """The registered events bitmask."""

    listener_group_count: int = attr.field(init=False, default=0)
    """The number of listener groups registered to this consumer."""

    waiter_group_count: int = attr.field(init=False, default=0)
    """The number of waiters groups registered to this consumer."""

    @property
    def is_enabled(self) -> bool:
        return self.listener_group_count > 0 or self.waiter_group_count > 0

    @typing.overload
    def __get__(self, instance: None, owner: type[typing.Any]) -> typing_extensions.Self:
        ...

    @typing.overload
    def __get__(
        self,
        instance: _BoundConsumer[_EventManagerT],
        owner: type,
    ) -> Consumer[_EventManagerT]:
        ...

    @typing.overload
    def __get__(
        self,
        instance: object,
        owner: type,
    ) -> _BoundConsumer[_EventManagerT]:
        ...

    def __get__(
        self,
        instance: typing.Any | None,
        owner: type,
    ) -> _BoundConsumer[_EventManagerT] | Consumer[_EventManagerT]:
        if instance is None or isinstance(instance, _BoundConsumer):
            return self

        return _BoundConsumer(instance, self)


def is_consumer_for(
    *event_types: type[base_events.Event],
) -> typing.Callable[[UnboundConsumerCallback[_EventManagerT]], Consumer[_EventManagerT]]:
    # Get all event subtypes dispatched by the provided events and eliminate
    # duplicates...
    bitmask = 0
    for event_type in event_types:
        for dispatched_event in event_type.dispatches:
            bitmask |= dispatched_event.bitmask

    def wrapper(
        callback: UnboundConsumerCallback[_EventManagerT],
    ) -> Consumer[_EventManagerT]:
        return Consumer(callback, bitmask)

    return wrapper


@attr.define(weakref_slot=False)
class _BoundConsumer(typing.Generic[_EventManagerT]):
    event_manager: event_manager_trait.EventManager = attr.field()

    consumer: Consumer[_EventManagerT] = attr.field()

    @property
    def callback(self) -> UnboundConsumerCallback[_EventManagerT]:
        return self.consumer.callback

    @property
    def events_bitmask(self) -> int:
        return self.consumer.events_bitmask

    @property
    def listener_group_count(self) -> int:
        return self.consumer.listener_group_count

    @listener_group_count.setter
    def listener_group_count(self, value: int) -> None:
        self.consumer.listener_group_count = value

    @property
    def waiter_group_count(self) -> int:
        return self.consumer.waiter_group_count

    @waiter_group_count.setter
    def waiter_group_count(self, value: int) -> None:
        self.consumer.waiter_group_count = value

    @property
    def is_enabled(self) -> bool:
        return self.consumer.is_enabled

    async def __call__(
        self,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        await self.callback(self.event_manager, gateway_connection, payload)


class EventManagerBase(event_manager_trait.EventManager):
    __slots__ = ("_consumers", "_listeners", "_waiters")

    _consumers: dict[str, _BoundConsumer[typing_extensions.Self]]
    _waiters: _WaiterMapT[base_events.Event]
    _listeners: _ListenerMapT[base_events.Event]

    def __init__(self) -> None:
        self._consumers = {}
        self._listeners = {}
        self._waiters = {}

        for name, member in inspect.getmembers(self):
            if not name.startswith("on_"):
                continue

            event_name = name[3:]
            if not isinstance(member, _BoundConsumer):
                continue

            self._consumers[event_name] = member  # pyright: ignore

    async def _invoke_callback(
        self,
        callback: base_events.EventCallbackT[base_events.EventT],
        event: base_events.EventT,
    ) -> None:
        try:
            await callback(event)
        except Exception as exc:  # noqa: BLE001
            exc_info = type(exc), exc, exc.__traceback__.tb_next if exc.__traceback__ else None
            if _is_exception_event(event):
                _LOGGER.exception(
                    "An exception occurred while handling event '%s', and was ignored.",
                    type(event).__name__,
                    exc_info=exc_info,
                )

            else:
                exception_event = base_events.ExceptionEvent(
                    exception=exc,
                    failed_event=event,
                    failed_callback=callback,
                )

                _LOGGER.debug(
                    "An exception occurred while handling event '%s'.",
                    type(event).__name__,
                )
                await self.dispatch(exception_event)

    async def _handle_consumption(
        self,
        consumer: _BoundConsumer[typing_extensions.Self],
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        if not consumer.is_enabled:
            _LOGGER.debug(
                "Skipping raw dispatch for event '%s' because it has no registered listeners.",
                consumer.callback.__name__,
            )
            return

        try:
            _LOGGER.debug(
                "Dispatching event '%s'.",
                consumer.callback.__name__,
            )
            await consumer(gateway_connection, payload)
        except asyncio.CancelledError:
            # Can be safely skipped, most likely caused by shutting down event loop.
            return
        # TODO: Figure out if this can be Exception
        except BaseException as exc:  # noqa: BLE001
            asyncio.get_running_loop().call_exception_handler(
                {
                    "message": "An exception occurred while dispatching raw event.",
                    "exception": exc,
                    "task": asyncio.current_task(),
                },
            )

    def _increment_listener_group_count(
        self,
        event_type: type[base_events.Event],
        count: typing.Literal[-1, 1],
    ) -> None:
        event_bitmask = event_type.bitmask
        for consumer in self._consumers.values():
            if (consumer.events_bitmask & event_bitmask) == event_bitmask:
                consumer.listener_group_count += count

    def _increment_waiter_group_count(
        self,
        event_type: type[base_events.Event],
        count: typing.Literal[-1, 1],
    ) -> None:
        event_bitmask = event_type.bitmask
        for consumer in self._consumers.values():
            if (consumer.events_bitmask & event_bitmask) == event_bitmask:
                consumer.waiter_group_count += count

    def consume_raw_event(
        self,
        event_name: str,
        gateway_connection: gateway_trait.GatewayHandler,
        payload: data_binding.JSONObject,
    ) -> None:
        consumer = self._consumers.get(event_name.lower())

        if not consumer:
            _LOGGER.warning("Unhandled event: %r", event_name.lower())
            return

        async_utils.safe_task(
            self._handle_consumption(consumer, gateway_connection, payload),
            name=f"dispatch {event_name}",
        )

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        tasks: list[typing.Coroutine[None, typing.Any, None]] = []

        for cls in event.dispatches:
            for callback in self._listeners.get(cls, ()):
                tasks.append(self._invoke_callback(callback, event))  # noqa: PERF401

            if cls not in self._waiters:
                continue

            waiter_set = self._waiters[cls]
            for waiter in tuple(waiter_set):
                predicate, future = waiter
                if not future.done():
                    try:
                        if predicate and not predicate(event):
                            continue
                    except Exception as ex:  # noqa: BLE001
                        future.set_exception(ex)
                    else:
                        future.set_result(event)

                waiter_set.remove(waiter)

            if not waiter_set:
                del self._waiters[cls]
                self._increment_waiter_group_count(cls, -1)

        return asyncio.gather(*tasks) if tasks else async_utils.create_completed_future()

    def subscribe(
        self,
        event_type: type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        if not asyncio.iscoroutinefunction(callback):
            msg = f"Cannot subscribe to non-coroutine function '{callback.__name__}'."
            raise TypeError(msg)

        _LOGGER.debug(
            "Subscribing callback '%s%s' to event-type '%s.%s'.",
            callback.__name__,
            inspect.signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )

        try:
            self._listeners[event_type].append(callback)  # type: ignore
        except KeyError:
            self._listeners[event_type] = [callback]  # type: ignore
            self._increment_listener_group_count(event_type, 1)

    def unsubscribe(
        self,
        event_type: type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        listeners = self._listeners.get(event_type)
        if not listeners:
            return

        _LOGGER.debug(
            "Unsubscribing callback '%s%s' from event-type '%s.%s'.",
            callback.__name__,
            inspect.signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )

        listeners.remove(callback)  # type: ignore

        if not listeners:
            # Last listener for this event type was removed
            del self._listeners[event_type]
            self._increment_listener_group_count(event_type, -1)

    def get_listeners(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event_type: type[base_events.EventT],
        /,
        *,
        polymorphic: bool = True,
    ) -> typing.Collection[base_events.EventCallbackT[base_events.EventT]]:
        if polymorphic:
            listeners: list[base_events.EventCallbackT[base_events.EventT]] = []
            for event in event_type.dispatches:
                if subscribed_listeners := self._listeners.get(event):
                    listeners.extend(subscribed_listeners)

            return listeners

        if items := self._listeners.get(event_type):
            return items.copy()

        return ()

    def listen(
        self,
        *event_types: type[base_events.EventT],
    ) -> typing.Callable[
        [base_events.EventCallbackT[base_events.EventT]],
        base_events.EventCallbackT[base_events.EventT],
    ]:
        def wrapper(
            callback: base_events.EventCallbackT[base_events.EventT],
        ) -> base_events.EventCallbackT[base_events.EventT]:
            signature = inspect.signature(callback)
            parameters = signature.parameters.values()
            event_param = next(iter(parameters))
            annotation = event_param.annotation

            if annotation is inspect.Parameter.empty:
                if event_types:
                    resolved_types = event_types

                else:
                    msg = (
                        "Please provide the event type either as an argument to"
                        " the decorator or as a type hint."
                    )
                    raise TypeError(msg)

            else:
                if typing.get_origin(annotation) in _UNIONS:
                    resolved_types = {
                        class_utils.strip_generic(ann) for ann in typing.get_args(annotation)
                    }
                else:
                    resolved_types = {class_utils.strip_generic(annotation)}

                if event_types and resolved_types != set(event_types):
                    msg = (
                        "Please make sure the event types provided to the"
                        " decorator match those provided as a typehint."
                    )
                    raise TypeError(msg)

            for event_type in resolved_types:
                self.subscribe(event_type, callback)

            return callback

        return wrapper

    async def wait_for(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event_type: type[base_events.EventT],
        /,
        *,
        timeout: float | None = None,
        predicate: event_manager_trait.EventPredicateT[base_events.EventT] | None = None,
    ) -> base_events.EventT:
        future: asyncio.Future[base_events.EventT] = asyncio.get_running_loop().create_future()

        assert issubclass(event_type, base_events.Event)

        try:
            waiter_set = self._waiters[event_type]
        except KeyError:
            waiter_set = self._waiters[event_type] = set[_WaiterPairT[base_events.Event]]()
            self._increment_waiter_group_count(event_type, 1)

        pair = (predicate, future)

        waiter_set.add(pair)  # pyright: ignore[reportGeneralTypeIssues]
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            waiter_set.remove(pair)  # pyright: ignore[reportGeneralTypeIssues]
            if not waiter_set:
                del self._waiters[event_type]
                self._increment_waiter_group_count(event_type, -1)

            raise
