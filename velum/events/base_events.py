from __future__ import annotations

import abc
import typing

import attr

__all__: typing.Sequence[str] = ("Event", "ExceptionEvent")


EventT = typing.TypeVar("EventT", bound="Event")
EventCallbackT = typing.Callable[[EventT], typing.Coroutine[typing.Any, typing.Any, None]]


class Event(abc.ABC):
    """Base type for all events"""

    __slots__ = ()

    __id_counter: int = 0

    bitmask: int
    dispatches: tuple[type[Event], ...]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if "__attrs_attrs__" in cls.__dict__:
            # attrs runs __new__ a second time on class creation, and we don't
            # need to increment the bitmask again.
            return

        # We don't have to explicitly include Event here as issubclass(Event, Event) returns True.
        # Non-event classes should be ignored.
        cls.dispatches = tuple(sub_cls for sub_cls in cls.mro() if issubclass(sub_cls, Event))
        cls.bitmask = 1 << cls.__id_counter

        cls.__id_counter += 1


# Set event parameters on the actual event class.
Event.__init_subclass__()


@attr.define(kw_only=True, weakref_slot=False)
class ExceptionEvent(Event, typing.Generic[EventT]):
    exception: Exception = attr.field()

    failed_event: EventT = attr.field()

    failed_callback: EventCallbackT[EventT] = attr.field()

    async def retry(self) -> None:
        await self.failed_callback(self.failed_event)
