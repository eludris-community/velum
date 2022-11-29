import typing

from velum.events import base_events

__all__: typing.Sequence[str] = ("ConnectionEvent", "DisconnectEvent")


class ConnectionEvent(base_events.Event):
    """Event fired when the bot establishes a connection with the gateway."""


class DisconnectEvent(base_events.Event):
    """Event fired when the bot loses connection with the gateway"""
