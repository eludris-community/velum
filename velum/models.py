from __future__ import annotations

import ipaddress
import typing
from enum import Enum

import attr

__all__: typing.Sequence[str] = (
    "Message",
    "InstanceInfo",
    "Session",
    "StatusType",
    "Status",
    "User",
)


# Gateway event models...


@attr.define(kw_only=True, weakref_slot=False)
class RatelimitData:
    """Represents a rate-limit by the connected Eludris instance's gateway."""

    wait: int
    """The number of milliseconds to wait for the rate-limit to wear off."""


@attr.define(kw_only=True, weakref_slot=False)
class Hello:
    """Represents the payload sent by the gateway upon connection."""

    heartbeat_interval: int
    """The number of milliseconds to wait between pings."""

    instance_info: InstanceInfo
    """The :class:`InstanceInfo` object for the connected instance."""

    pandemonium_info: PandemoniumConf
    """Information regarding the connected Eludris instance's gateway.

    This contains the gateway url and rate-limit info.
    """


@attr.define(kw_only=True, weakref_slot=False)
class Authenticated:
    """Represents the payload sent by the gateway upon authentication."""

    user: User
    """The currently authenticated user."""

    users: typing.Sequence[User]
    """The online users relevant to the authenticated user."""


@attr.define(kw_only=True, weakref_slot=False)
class Message:
    """Represents a message on Eludris."""

    author: User = attr.field()
    """The author of the message."""

    content: str = attr.field()
    """The content of the message."""


# REST-api models...


@attr.define(kw_only=True, weakref_slot=False)
class RatelimitConf:
    """Represents a simple rate-limit configuration for an Eludris instance."""

    reset_after: int = attr.field()
    """The number of seconds the client should wait before making new requests."""

    limit: int
    """The number of requests that can be made
    in the timeframe denoted by ``reset_after``.
    """


@attr.define(kw_only=True, weakref_slot=False)
class EffisRatelimitConf(RatelimitConf):
    """Represents a rate-limit configuration for an individual Effis (CDN) route.

    Unlike normal ratelimits, these also include a file size limit.
    """

    file_size_limit: int = attr.field()
    """The maximum total filesize in bytes that can be requested in the
    timeframe denoted by ``reset_after``.
    """


@attr.define(kw_only=True, weakref_slot=False)
class InstanceRatelimits:
    """Represents all ratelimits that apply to the connected Eludris instance.

    This includes individual rate-limit information for Oprish, Pandemonium and
    Effis.
    """

    oprish: OprishRatelimits = attr.field()
    """The ratelimits that apply to the connected Eludris instance's REST api."""

    pandemonium: RatelimitConf = attr.field()
    """The ratelimits that apply to the connected Eludris instance's gateway."""

    effis: EffisRatelimits = attr.field()
    """The ratelimits that apply to the connected Eludris instance's CDN."""


@attr.define(kw_only=True, weakref_slot=False)
class OprishRatelimits:
    """Represents the rate-limit configuration for an Oprish (REST-api) instance.

    This denotes the rate-limit specifics on individual routes.
    """

    info: RatelimitConf = attr.field()
    """The rate-limit information on the info (``GET /``) route."""

    message_create: RatelimitConf = attr.field()
    """The rate-limit information on the message create (``POST /messages``) route."""

    ratelimits: RatelimitConf = attr.field()
    """The rate-limit information on the ratelimits (``GET /ratelimits``) route."""


@attr.define(kw_only=True, weakref_slot=False)
class EffisRatelimits:
    """Represents the rate-limit configuration for an Effis (CDN) instance.

    This denotes the rate-limit specifics on individual routes, including
    maximum file size limits.
    """

    assets: EffisRatelimitConf = attr.field()
    """The rate-limit information for the handling of Assets."""

    attachments: EffisRatelimitConf = attr.field()
    """The rate-limit information for the handling of Attachments."""

    fetch_file: RatelimitConf = attr.field()
    """The rate-limit information for file-fetching endpoints."""


@attr.define(kw_only=True, weakref_slot=False)
class FileMetadata:
    """Represents metadata for a file stored on the connected Eludris instance's CDN."""

    type: str = attr.field()
    """The type of file. Can be any of "text", "image", "video", or "other"."""

    width: typing.Optional[int] = attr.field(default=None)
    """The width of the file. Only available for files of types "image" or "video"."""

    height: typing.Optional[int] = attr.field(default=None)
    """The height of the file. Only available for files of types "image" or "video"."""


@attr.define(kw_only=True, weakref_slot=False)
class FileData:
    """Represents a file stored on the connected Eludris instance's CDN."""

    id: int
    """The id of the file."""

    name: str
    """The name of the file."""

    bucket: str
    """The bucket to which the file belongs."""

    spoiler: bool
    """Whether or not the file is tagged as a spoiler."""

    metadata: FileMetadata
    """Extra information pertaining the file. This is dependent on the filetype.

    See the documentation on ``FileMetadata`` for more accurate information.
    """


@attr.define(kw_only=True, weakref_slot=False)
class PandemoniumConf:
    """Represents configuration settings for the connected Eludris instance's gateway.

    This contains the gateway URL and the rate-limit information.
    """

    url: str
    """The URL for the connected Eludris instance's gateway."""

    rate_limit: RatelimitConf
    """The rate-limit config for the connected Eludris instance's gateway."""


@attr.define(kw_only=True, weakref_slot=False)
class InstanceInfo:
    """Represents info about the connected Eludris instance."""

    instance_name: str = attr.field()
    """The name of the connected Eludris instance."""

    description: typing.Optional[str] = attr.field()
    """The description of the connected Eludris instance."""

    version: str = attr.field()
    """The Eludris version the connected Eludris instance is running."""

    message_limit: int = attr.field()
    """The maximum allowed message content length."""

    oprish_url: str = attr.field()
    """The url to the connected instance's REST api."""

    pandemonium_url: str = attr.field()
    """The url to the connected instance's gateway."""

    effis_url: str = attr.field()
    """The url to the connected instance's CDN."""

    file_size: int = attr.field()
    """The maximum asset file size that can be uploaded to the connected instance's CDN."""

    attachment_file_size: int = attr.field()
    """The maximum attachment file size that can be uploaded to the connected instance's CDN."""

    rate_limits: typing.Optional[InstanceRatelimits] = attr.field()
    """The ratelimits that apply to the connected Eludris instance."""


@attr.define(kw_only=True, weakref_slot=False)
class Session:
    """Represents an authenticated session with an Eludris instance."""

    id: int
    """The id of the session."""

    user_id: int
    """The id of the user that owns the session."""

    platform: str
    """The platform the session was created on."""

    client: str
    """The client the session was created by."""

    ip: typing.Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
    """The IP address the session was created from."""


class StatusType(Enum):
    """Represents the type of a status."""

    ONLINE = "ONLINE"
    """The user is online."""

    OFFLINE = "OFFLINE"
    """The user is offline."""

    IDLE = "IDLE"
    """The user is idle."""

    BUSY = "BUSY"
    """The user is busy."""


@attr.define(kw_only=True, weakref_slot=False)
class Status:
    """Represents the status of a user."""

    type: StatusType = attr.field()
    """The type of the status."""

    text: typing.Optional[str] = attr.field()
    """The text of the status."""


@attr.define(kw_only=True, weakref_slot=False)
class User:
    """Represents a user on an Eludris instance."""

    id: int
    """The id of the user."""

    username: str
    """The username of the user."""

    display_name: typing.Optional[str] = attr.field(default=None)
    """The display name of the user."""

    social_credit: int
    """The social credit of the user."""

    status: Status
    """The status of the user."""

    bio: typing.Optional[str] = attr.field(default=None)
    """The bio of the user."""

    avatar: typing.Optional[int] = attr.field(default=None)
    """The avatar of the user."""

    banner: typing.Optional[int] = attr.field(default=None)
    """The banner of the user."""

    badges: int
    """The badges of the user."""

    permissions: int
    """The permissions of the user."""

    email: typing.Optional[str] = attr.field(default=None)
    """The email of the user.

    This is only available when getting the data of the currently authenticated user.
    """

    verified: typing.Optional[bool] = attr.field(default=None)
    """Whether or not the user is verified.

    This is only available when getting the data of the currently authenticated user.
    """


@attr.define(kw_only=True, weakref_slot=False)
class PresenceUpdate:
    """Represents a presence update."""

    user_id: int
    """The id of the user."""

    status: Status
    """The status of the user."""
