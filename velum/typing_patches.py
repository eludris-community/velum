import typing
import aiohttp


class WSMessage(typing.Protocol):
    type: aiohttp.WSMsgType
    data: typing.Optional[str | bytes]
    extra: typing.Optional[str]

    def json(self, loads: typing.Callable[[typing.Any], typing.Any] = ...) -> typing.Any:
        ...
