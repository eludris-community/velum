import typing

import typing_extensions

from velum.api import rate_limit_trait

__all__: typing.Sequence[str] = ("ExponentialBackoff",)


class ExponentialBackoff(rate_limit_trait.RateLimiter):

    __slots__ = ("base", "maximum", "increment", "_initial_increment")

    base: float
    maximum: float
    increment: int

    def __init__(
        self,
        base: float = 2.0,
        maximum: float = 60.0,
        initial_increment: int = 0,
    ):
        self.base = base
        self.maximum = maximum
        self.increment = self._initial_increment = initial_increment

    @property
    def initial_increment(self) -> int:
        return self._initial_increment

    def __next__(self) -> float:
        value = self.base**self.increment

        if value >= self.maximum:
            value = self.maximum
        else:
            # No point incrementing if we're already at the maximum value.
            self.increment += 1

        return value

    def __iter__(self) -> typing_extensions.Self:
        return self

    def reset(self) -> None:
        self.increment = self._initial_increment
