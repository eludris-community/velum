from __future__ import annotations

import enum
import importlib
import typing

__all__: typing.Sequence[str] = (
    "JSONish",
    "JSONObject",
    "JSONArray",
    "JSONDecodeError",
    "dump_json",
    "load_json",
    "JSONImpl",
    "set_json_impl",
)

_T = typing.TypeVar("_T")

_JSONishT = str | int | float | bool | None | _T
_JSONObjectT = typing.Mapping[str, _JSONishT[_T]]
_JSONArrayT = typing.Sequence[_JSONishT[_T]]

JSONish = _JSONObjectT["JSONish"] | _JSONArrayT["JSONish"]
JSONObject = _JSONObjectT[JSONish]
JSONArray = _JSONArrayT[JSONish]


# JSON implementation components.


class _JSONLoader(typing.Protocol):
    def __call__(self, __string: typing.AnyStr, /) -> JSONish:
        ...


class _JSONDumper(typing.Protocol):
    def __call__(self, __obj: JSONish, /) -> str:
        ...


# Placeholders.
# These are used to provide typehints for the exported symbols.


def dump_json(_: JSONish, /) -> str:
    """Convert a Python type to a JSON string."""
    raise NotImplementedError


def load_json(_: typing.AnyStr, /) -> JSONish:
    """Convert a JSON string to a Python type."""
    raise NotImplementedError


JSONDecodeError: typing.Type[Exception] = Exception
"""Exception raised when loading an invalid JSON string"""


# JSON implementation setter utility.


class JSONImpl(enum.Enum):
    """Enum used to set the desired JSON implementation with ``velum.set_json_impl``."""

    JSON = enum.auto()
    """The standard-library JSON implementation."""

    ORJSON = enum.auto()
    """A faster JSON implementation that comes installed with ``velum[speedups]``."""


@typing.overload
def set_json_impl(*, impl: JSONImpl) -> None:
    ...


@typing.overload
def set_json_impl(
    loader: _JSONLoader,
    dumper: _JSONDumper,
    error: typing.Type[Exception],
    /,
) -> None:
    ...


def set_json_impl(
    loader: typing.Optional[_JSONLoader] = None,
    dumper: typing.Optional[_JSONDumper] = None,
    error: typing.Optional[typing.Type[Exception]] = None,
    /,
    *,
    impl: typing.Optional[JSONImpl] = None,
) -> None:
    if (not (loader and dumper and error) and not impl) or ((loader or dumper or error) and impl):
        raise ValueError(
            "Please provide either:"
            "\n- All of `loader`, `dumper` and `error`,"
            "\n- only `implementation`."
        )

    global dump_json, load_json, JSONDecodeError

    if loader and dumper and error:
        load_json = loader
        dump_json = dumper
        JSONDecodeError = error
        return

    if impl is JSONImpl.JSON:
        json = importlib.import_module("json")
        load_json = json.loads
        dump_json = json.dumps
        JSONDecodeError = json.JSONDecodeError
        return

    elif impl is JSONImpl.ORJSON:
        try:
            orjson = importlib.import_module("orjson")

        except ImportError as exc:
            raise ImportError(
                "Cannot set 'orjson' as velum's JSON implementation, as you seem to not"
                " have it installed.\nPlease install orjson and try again."
                " Alternatively, orjson comes installed with 'velum[speedups]'."
            ) from exc

        else:
            load_json = orjson.loads
            dump_json = lambda obj: orjson.dumps(obj).decode()  # noqa[E731]
            JSONDecodeError = orjson.JSONDecodeError

        finally:
            return

    raise TypeError(
        "Incorrect values have been passed, and led to an unexpected result."
        " Please double-check your input."
    )


# Set the stdlib `json` module as the default implementation

set_json_impl(impl=JSONImpl.JSON)
