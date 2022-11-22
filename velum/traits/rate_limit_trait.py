import typing

import typing_extensions


class RateLimiter(typing.Protocol):

    __slots__: typing.Sequence[str] = ()

    def __iter__(self) -> typing_extensions.Self:
        ...

    def __next__(self) -> float:
        ...

    def reset(self) -> None:
        ...
