import typing

import attr

__all__: typing.Sequence[str] = (
    "VelumError",
    "GatewayError",
    "GatewayConnectionError",
    "GatewayConnectionClosedError",
    "HTTPError",
)


@attr.define(auto_exc=True, repr=False, init=False, slots=False)
class VelumError(RuntimeError):
    "idk lol"


@attr.define(auto_exc=True, repr=False, slots=False)
class GatewayError(VelumError):
    reason: str = attr.field()

    def __str__(self) -> str:
        return self.reason


@attr.define(auto_exc=True, repr=False, slots=False)
class GatewayConnectionError(GatewayError):
    def __str__(self) -> str:
        return f"Failed to connect to server: {self.reason}"


@attr.define(auto_exc=True, repr=False, slots=False)
class GatewayConnectionClosedError(GatewayError):
    code: typing.Optional[int | None] = attr.field()

    def __str__(self) -> str:
        return f"Server closed connection with code {self.code} ({self.reason})"


@attr.define(auto_exc=True, repr=False, slots=False)
class HTTPError(VelumError):
    message: str = attr.field()
