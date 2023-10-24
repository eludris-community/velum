from __future__ import annotations

import concurrent.futures
import contextlib
import enum
import importlib
import typing

import aiohttp
import typing_extensions

from velum import files

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


JSONDecodeError: type[Exception] = Exception
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
    error: type[Exception],
    /,
) -> None:
    ...


def set_json_impl(
    loader: _JSONLoader | None = None,
    dumper: _JSONDumper | None = None,
    error: type[Exception] | None = None,
    /,
    *,
    impl: JSONImpl | None = None,
) -> None:
    if (not (loader and dumper and error) and not impl) or ((loader or dumper or error) and impl):
        msg = "Please provide either:\n- All of `loader`, `dumper` and `error`,\n- only `implementation`."
        raise ValueError(
            msg,
        )

    global dump_json, load_json, JSONDecodeError  # noqa: PLW0603

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
            msg = "Cannot set 'orjson' as velum's JSON implementation, as you seem to not have it installed.\nPlease install orjson and try again. Alternatively, orjson comes installed with 'velum[speedups]'."
            raise ImportError(
                msg,
            ) from exc

        else:
            load_json = orjson.loads
            dump_json = lambda obj: orjson.dumps(obj).decode()  # noqa: E731
            JSONDecodeError = orjson.JSONDecodeError
            return

    msg = "Incorrect values have been passed, and led to an unexpected result. Please double-check your input."
    raise TypeError(
        msg,
    )


# Set the stdlib `json` module as the default implementation

set_json_impl(impl=JSONImpl.JSON)


# Builders


class FormBuilder:
    """Helper class to generate `aiohttp.FormData`."""

    __slots__: typing.Sequence[str] = ("_executor", "_fields", "_resources")

    def __init__(self, executor: concurrent.futures.Executor | None = None) -> None:
        self._executor = executor
        self._fields: list[tuple[str, str, str | None]] = []
        self._resources: list[tuple[str, files.Resource[files.AsyncReader]]] = []

    def add_field(
        self,
        name: str,
        data: str,
        *,
        content_type: str | None = None,
    ) -> typing_extensions.Self:
        self._fields.append((name, data, content_type))
        return self

    def add_resource(
        self,
        name: str,
        resource: files.Resource[files.AsyncReader],
    ) -> typing_extensions.Self:
        self._resources.append((name, resource))
        return self

    async def build(self, stack: contextlib.AsyncExitStack) -> aiohttp.FormData:
        form = aiohttp.FormData()

        for field in self._fields:
            form.add_field(field[0], field[1], content_type=field[2])

        for name, resource in self._resources:
            stream = await stack.enter_async_context(resource.stream(executor=self._executor))
            form.add_field(name, stream, filename=stream.filename)

        return form
