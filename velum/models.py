import re
import typing

import attr

__all__: typing.Sequence[str] = (
    "Message",
    "InstanceInfo",
)

# FeatureSequence = typing.Sequence[typing.Mapping[int, str]]


@attr.define(kw_only=True, weakref_slot=False)
class Message:
    """Represents a message on Eludris."""

    author: str = attr.field()
    """The author of the message."""

    content: str = attr.field()
    """The content of the message."""


@attr.define(kw_only=True, weakref_slot=False)
class InstanceInfo:
    """Represents info about the connected Eludris instance."""

    instance_name: str = attr.field()
    """The name of the connected Eludris instance."""

    # features: FeatureSequence = attr.field()

    description: typing.Optional[str] = attr.field()
    """The description of the connected Eludris instance."""

    message_limit: int = attr.field()
    """The maximum allowed message content length."""

    oprish_url: str = attr.field()
    """The url to the connected instance's REST api."""

    pandemonium_url: str = attr.field()
    """The url to the connected instance's gateway."""

    effis_url: str = attr.field()
    """The url to the connected instance's CDN."""

    file_size: int = attr.field()
    """The maximum asset file size that can be uploaded to the connected
    instance's CDN.
    """

    attachment_file_size: int = attr.field()
    """The maximum attachment file size that can be uploaded to the connected
    instance's CDN.
    """


@attr.define(kw_only=True, weakref_slot=False)
class RatelimitConfig:
    """Represents a simple ratelimit configuration for an Eludris instance."""

    reset_after: int = attr.field()
    """The number of seconds the client should wait before making new requests."""

    limit: int
    """The number of requests that can be made
    in the timeframe denoted by ``reset_after``.
    """


@attr.define(kw_only=True, weakref_slot=False)
class EffisRatelimitConfig(RatelimitConfig):
    """Represents a ratelimit configuration for an individual Effis (CDN) route.

    Unlike normal ratelimits, these also include a file size limit.
    """

    file_size_limit: str = attr.field()
    """The maximum total filesize that can be requested
    in the timeframe denoted by ``reset_after``, in a human-readable format.
    """

    @property
    def file_size_limit_bytes(self) -> int:
        """The maximum file size limit expressed in bytes as an integer."""

        _UNITS = (None, "K", "M", "G")

        match = re.match(r"(\d+)(K|M)?i?B", self.file_size_limit)
        assert match

        base = int(match.group(1))
        factor = _UNITS.index(match.group(2)) * 10

        return base << factor


@attr.define(kw_only=True, weakref_slot=False)
class OprishRatelimits:
    """Represents the ratelimit configuration for an Oprish (REST-api) instance.

    This denotes the ratelimit specifics on individual routes.
    """

    info: RatelimitConfig = attr.field()
    """The ratelimit information on the info (``GET /``) route."""

    message_create: RatelimitConfig = attr.field()
    """The ratelimit information on the message create (``POST /messages``) route."""

    ratelimits: RatelimitConfig = attr.field()
    """The ratelimit information on the ratelimits (``GET /ratelimits``) route."""


@attr.define(kw_only=True, weakref_slot=False)
class EffisRatelimits:
    """Represents the ratelimit configuration for an Effis (CDN) instance.

    This denotes the ratelimit specifics on individual routes, including
    maximum file size limits.
    """

    assets: EffisRatelimitConfig = attr.field()
    """The ratelimit information for the handling of Assets."""

    attachments: EffisRatelimitConfig = attr.field()
    """The ratelimit information for the handling of Attachments."""


@attr.define(kw_only=True, weakref_slot=False)
class InstanceRatelimits:
    """Represents all ratelimits that apply to the connected Eludris instance.

    This includes individual ratelimit information for Oprish, Pandemonium and
    Effis.
    """

    oprish: OprishRatelimits = attr.field()
    """The ratelimits that apply to the connected Eludris instance's REST api."""

    pandemonium: RatelimitConfig = attr.field()
    """The ratelimits that apply to the connected Eludris instance's gateway."""

    effis: EffisRatelimits = attr.field()
    """The ratelimits that apply to the connected Eludris instance's CDN."""
