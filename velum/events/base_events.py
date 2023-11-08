from __future__ import annotations

import abc
import typing

import attr

__all__: typing.Sequence[str] = ("Event", "ExceptionEvent")


EventT = typing.TypeVar("EventT", bound="Event")
EventCallbackT = typing.Callable[[EventT], typing.Coroutine[typing.Any, typing.Any, None]]


_id_counter = 1


class Event(abc.ABC):
    """Base type for all events"""

    __slots__ = ()

    bitmask: typing.ClassVar[int]
    dispatches: typing.ClassVar[typing.Sequence[type[Event]]]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # NOTE: cls.dispatches contains the event `cls` itself.
        # This needs to be run every time __init_subclass__ is run for two reasons:
        #    1. We need to make sure that this is set when attrs.define
        #       finalises the class to ensure that the event itself in the tuple
        #       is actually finalised.
        #    2. As not all event classes are decorated with attrs.define, we
        #       must also set it in the original run, as otherwise cls.dispatches
        #       would not be set at all.
        cls.dispatches = tuple(sub_cls for sub_cls in cls.mro() if issubclass(sub_cls, Event))

        if "__attrs_attrs__" in cls.__dict__:
            # attrs runs __new__ a second time on class creation, and we don't
            # need to increment the bitmask again.
            return

        global _id_counter  # noqa: PLW0603

        cls.bitmask = 1 << _id_counter
        _id_counter += 1


# Set event parameters on the actual event class.
Event.dispatches = (Event,)
Event.bitmask = 1


@attr.define(kw_only=True, weakref_slot=False)
class ExceptionEvent(Event, typing.Generic[EventT]):
    exception: Exception = attr.field()

    failed_event: EventT = attr.field()

    failed_callback: EventCallbackT[EventT] = attr.field()

    async def retry(self) -> None:
        await self.failed_callback(self.failed_event)
