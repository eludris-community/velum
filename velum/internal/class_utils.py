import typing

T = typing.TypeVar("T")
ClsT = typing.TypeVar("ClsT")


class classproperty(typing.Generic[ClsT, T]):

    __slots__: typing.Sequence[str] = ("callback",)

    def __init__(self, callback: typing.Callable[[typing.Type[ClsT]], T]):
        self.callback = typing.cast("classmethod[T]", callback)

    def __get__(self, instance: typing.Optional[ClsT], owner: typing.Type[ClsT]) -> T:
        return self.callback.__func__(owner)  # type: ignore
