from __future__ import annotations

import typing

import attr

from velum.events import base_events

if typing.TYPE_CHECKING:
    from velum import models

__all__: typing.Sequence[str] = (
    "UserUpdateEvent",
    "PresenceUpdateEvent",
)


class UserEvent(base_events.Event):
    """Any event concerning users."""

    __slots__ = ()


@attr.define(kw_only=True, weakref_slot=False)
class UserUpdateEvent(UserEvent):
    """Event fired when a user's information is updated."""

    user: models.User = attr.field()


@attr.define(kw_only=True, weakref_slot=False)
class PresenceUpdateEvent(UserEvent):
    """Event fired when a user's presence is updated."""

    data: models.PresenceUpdate = attr.field()

    @property
    def user_id(self) -> int:
        """The id of the user."""

        return self.data.user_id

    @property
    def status(self) -> models.Status:
        """The status of the user."""

        return self.data.status
