import typing

from velum.events import base_events

__all__: typing.Sequence[str] = ("ConnectionEvent", "DisconnectEvent")


class ConnectionEvent(base_events.Event):
    """Event fired when the client establishes a connection with the gateway."""

    __slots__: typing.Sequence[str] = ()


class DisconnectEvent(base_events.Event):
    """Event fired when the client loses connection with the gateway"""

    __slots__: typing.Sequence[str] = ()
