import typing

import attr

from velum import models
from velum.events import base_events

__all__: typing.Sequence[str] = (
    "ConnectionEvent",
    "DisconnectEvent",
    "HelloEvent",
    "RatelimitEvent",
)


class ConnectionEvent(base_events.Event):
    """Event fired when the client establishes a connection with the gateway."""

    __slots__: typing.Sequence[str] = ()


class DisconnectEvent(base_events.Event):
    """Event fired when the client loses connection with the gateway"""

    __slots__: typing.Sequence[str] = ()


@attr.define(kw_only=True, weakref_slot=False)
class HelloEvent(base_events.Event):
    """Event fired when the gateway first connects."""

    data: models.Hello = attr.field()

    @property
    def heartbeat_interval(self) -> int:
        """The number of milliseconds to wait between pings."""

        return self.data.heartbeat_interval

    @property
    def instance_info(self) -> models.InstanceInfo:
        """The :class:`InstanceInfo` object for the connected instance."""

        return self.data.instance_info

    @property
    def pandemonium_info(self) -> models.PandemoniumConf:
        """Information regarding the connected Eludris instance's gateway.

        This contains the gateway url and rate-limit info.
        """
        return self.data.pandemonium_info


@attr.define(kw_only=True, weakref_slot=False)
class RatelimitEvent(base_events.Event):
    """Event fired when the gateway ratelimits the client."""

    data: models.RatelimitData = attr.field()

    @property
    def wait(self) -> int:
        """The number of milliseconds to wait for the rate-limit to wear off."""

        return self.data.wait
