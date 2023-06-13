import typing

import attr

from velum import models
from velum.events import base_events

__all__: typing.Sequence[str] = ("MessageEvent", "MessageCreateEvent")


class MessageEvent(base_events.Event):
    """Any event concerning messages."""

    __slots__ = ()


@attr.define(kw_only=True, weakref_slot=False)
class MessageCreateEvent(MessageEvent):
    """An event that is fired when a message is created."""

    message: models.Message = attr.field()

    @property
    def author(self) -> models.User:
        return self.message.author

    @property
    def content(self) -> str:
        return self.message.content
