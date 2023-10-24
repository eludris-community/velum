import typing

__all__: typing.Sequence[str] = ("strip_generic",)


_T = typing.TypeVar("_T")


def strip_generic(type_: type[_T]) -> type[_T]:
    return typing.get_origin(type_) or type_
