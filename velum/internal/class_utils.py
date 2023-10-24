import typing

__all__: typing.Sequence[str] = ("classproperty", "strip_generic")


_T = typing.TypeVar("_T")
_ClsT = typing.TypeVar("_ClsT")


class classproperty(typing.Generic[_ClsT, _T]):  # noqa: N801
    __slots__: typing.Sequence[str] = ("callback",)

    callback: "classmethod[_ClsT, ..., _T]"

    def __init__(self, callback: typing.Callable[[type[_ClsT]], _T]) -> None:
        self.callback = typing.cast("classmethod[_ClsT, ..., _T]", callback)

    def __get__(self, instance: _ClsT | None, owner: type[_ClsT]) -> _T:
        return self.callback.__func__(owner)  # type: ignore


def strip_generic(type_: type[_T]) -> type[_T]:
    return typing.get_origin(type_) or type_
