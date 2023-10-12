import typing

__all__: typing.Sequence[str] = ("GatewayHandler",)


@typing.runtime_checkable
class GatewayHandler(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def is_alive(self) -> bool:
        ...

    async def start(self) -> None:
        ...

    async def close(self) -> None:
        ...
