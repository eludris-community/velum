import typing

import typing_extensions

__all__: typing.Sequence[str] = ("RateLimiter",)


@typing.runtime_checkable
class RateLimiter(typing.Protocol):

    __slots__: typing.Sequence[str] = ()

    def __iter__(self) -> typing_extensions.Self:
        ...

    def __next__(self) -> float:
        ...

    def reset(self) -> None:
        ...
