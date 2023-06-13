from __future__ import annotations

import typing

from velum.events import base_events

__all__: typing.Sequence[str] = ()


class UserEvent(base_events.Event):
    """Any event concerning users."""

    __slots__ = ()
