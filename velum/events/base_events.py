from __future__ import annotations

import abc
import typing

import attr

from velum.internal import class_utils

__all__: typing.Sequence[str] = ("Event", "ExceptionEvent")


EventT = typing.TypeVar("EventT", bound="Event")
EventCallbackT = typing.Callable[[EventT], typing.Coroutine[typing.Any, typing.Any, None]]


_id_counter = 0


class Event(abc.ABC):
    """Base type for all events"""

    __slots__ = ()

    __bitmask: int
    __dispatches: tuple[type[Event], ...]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        mro = cls.mro()
        cls.__dispatches = tuple(sub_cls for sub_cls in mro if issubclass(sub_cls, Event))

        if "__attrs_attrs__" in cls.__dict__:
            # attrs runs __new__ a second time on class creation, and we don't
            # need to increment the bitmask again.
            return

        global _id_counter  # noqa: PLW0603  # NOTE: maybe make this a private attr? hmm...

        # We don't have to explicitly include Event here as issubclass(Event, Event) returns True.
        # Non-event classes should be ignored.
        cls.__bitmask = 1 << _id_counter
        _id_counter += 1

    @class_utils.classproperty
    @classmethod
    def bitmask(cls) -> int:
        return cls.__bitmask

    @class_utils.classproperty
    @classmethod
    def dispatches(cls) -> tuple[type[Event], ...]:
        return cls.__dispatches


# Set event parameters on the actual event class.
Event.__init_subclass__()


@attr.define(kw_only=True, weakref_slot=False)
class ExceptionEvent(Event, typing.Generic[EventT]):
    exception: Exception = attr.field()

    failed_event: EventT = attr.field()

    failed_callback: EventCallbackT[EventT] = attr.field()

    async def retry(self) -> None:
        await self.failed_callback(self.failed_event)
