# Massive props and thanks to
# https://github.com/hikari-py/hikari/blob/master/hikari/files.py

from __future__ import annotations

import abc
import asyncio
import concurrent.futures
import contextlib
import inspect
import io
import mimetypes
import os
import pathlib
import types
import typing
import urllib.parse
import uuid

import aiohttp
import attr
import typing_extensions

from velum.internal import async_utils

ReaderT = typing.TypeVar("ReaderT", bound="AsyncReader")
ReaderT_co = typing_extensions.TypeVar(
    "ReaderT_co", bound="AsyncReader", covariant=True, default="AsyncReader"
)

PathLike = os.PathLike[str] | str
RawData = bytes | bytearray | memoryview | io.BytesIO | io.StringIO
ResourceLike = typing.Union["Resource[typing.Any]", PathLike, RawData]

LazyByteIterator = typing.Union[
    typing.AsyncIterator[bytes],
    typing.AsyncIterable[bytes],
    typing.Iterator[bytes],
    typing.Iterable[bytes],
    typing.AsyncIterator[str],
    typing.AsyncIterable[str],
    typing.Iterator[str],
    typing.Iterable[str],
    typing.AsyncGenerator[bytes, typing.Any],
    typing.Generator[bytes, typing.Any, typing.Any],
    typing.AsyncGenerator[str, typing.Any],
    typing.Generator[str, typing.Any, typing.Any],
    asyncio.StreamReader,
    aiohttp.StreamReader,
]

_BUFFER_SIZE: typing.Final[int] = 50 << 10


def ensure_path(pathish: PathLike) -> pathlib.Path:
    """Convert a path-like object to a `pathlib.Path` instance."""
    return pathlib.Path(pathish)


def unwrap_bytes(data: RawData) -> bytes:
    """Convert a byte-like object to bytes."""

    if isinstance(data, bytearray):
        data = bytes(data)
    elif isinstance(data, memoryview):
        data = data.tobytes()
    elif isinstance(data, io.StringIO):
        data = bytes(data.read(), "utf-8")
    elif isinstance(data, io.BytesIO):
        data = data.read()

    return data


def ensure_resource(
    data: ResourceLike, /, *, filename: typing.Optional[str] = None
) -> "Resource[AsyncReader]":
    if isinstance(data, Resource):
        return data

    elif isinstance(data, RawData):
        if not filename:
            filename = uuid.uuid4().hex

        return Bytes(data, filename)

    # Probably a URL or filepath at this point.
    data = str(data)

    if data.startswith(("http://", "https://")):
        return URL(data)

    return File(data)


@attr.define(weakref_slot=False)
class AsyncReader(typing.AsyncIterable[bytes], abc.ABC):
    """Protocol for reading a resource asynchronously using bit inception.
    This supports being used as an async iterable, although the implementation
    detail is left to each implementation of this class to define.
    """

    filename: str = attr.field(repr=True)
    """The filename of the resource."""

    mimetype: typing.Optional[str] = attr.field(repr=True)
    """The mimetype of the resource. May be `None` if not known."""

    async def read(self) -> bytes:
        """Read the rest of the resource and return it in a `bytes` object."""
        buff = bytearray()
        async for chunk in self:
            buff.extend(chunk)
        return buff


class AsyncReaderContextManager(abc.ABC, typing.Generic[ReaderT]):
    """Context manager that returns a reader."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def __aenter__(self) -> ReaderT:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...


class Resource(typing.Generic[ReaderT_co], abc.ABC):
    """Base for any uploadable or downloadable representation of information.
    These representations can be streamed using bit inception for performance,
    which may result in significant decrease in memory usage for larger
    resources.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def filename(self) -> str:
        """Filename of the resource."""

    @property
    def extension(self) -> typing.Optional[str]:
        """File extension, if there is one."""
        _, _, ext = self.filename.rpartition(".")
        return ext if ext != self.filename else None

    async def read(
        self,
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
    ) -> bytes:
        async with self.stream(executor=executor) as reader:
            return await reader.read()

    @abc.abstractmethod
    def stream(
        self,
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        head_only: bool = False,
    ) -> AsyncReaderContextManager[ReaderT_co]:
        ...

    def __str__(self) -> str:
        return self.filename

    def __repr__(self) -> str:
        return f"{type(self).__name__}(filename={self.filename!r})"

    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, Resource):
            return self.filename == other.filename
        return False

    def __hash__(self) -> int:
        return hash((self.__class__, self.filename))


# Local files


@attr.define(weakref_slot=False)
class ThreadedFileReader(AsyncReader):
    """Asynchronous file reader that reads a resource from local storage.
    This implementation works with pools that exist in the same interpreter
    instance as the caller, namely thread pool executors, where objects
    do not need to be pickled to be communicated.
    """

    _executor: typing.Optional[concurrent.futures.ThreadPoolExecutor] = attr.field()
    _pointer: typing.BinaryIO = attr.field()

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        loop = asyncio.get_running_loop()

        while True:
            chunk = await loop.run_in_executor(self._executor, self._pointer.read, _BUFFER_SIZE)
            yield chunk
            if len(chunk) < _BUFFER_SIZE:
                break


def _open_path(path: pathlib.Path) -> typing.BinaryIO:
    return path.expanduser().open("rb")


@attr.define(weakref_slot=False)
@typing.final
class _ThreadedFileReader(AsyncReaderContextManager[ThreadedFileReader]):
    executor: typing.Optional[concurrent.futures.ThreadPoolExecutor] = attr.field()
    file: typing.Optional[typing.BinaryIO] = attr.field(default=None, init=False)
    filename: str = attr.field()
    path: pathlib.Path = attr.field()

    async def __aenter__(self) -> ThreadedFileReader:
        if self.file:
            raise RuntimeError("File is already open")

        loop = asyncio.get_running_loop()
        file = await loop.run_in_executor(self.executor, _open_path, self.path)
        self.file = file
        return ThreadedFileReader(self.filename, None, self.executor, file)

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        if not self.file:
            raise RuntimeError("File isn't open")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self.file.close)
        self.file = None


class File(Resource[ThreadedFileReader]):
    """A resource that exists on the local machine's storage to be uploaded."""

    __slots__: typing.Sequence[str] = ("path", "_filename", "is_spoiler")

    path: pathlib.Path
    """The path to the file."""

    is_spoiler: bool
    """Whether the file will be marked as a spoiler."""

    _filename: typing.Optional[str]

    def __init__(
        self,
        path: PathLike,
        /,
        filename: typing.Optional[str] = None,
        *,
        spoiler: bool = False,
    ) -> None:
        self.path = ensure_path(path)
        self.is_spoiler = spoiler
        self._filename = filename

    @property
    def filename(self) -> str:
        return self._filename if self._filename else self.path.name

    def stream(
        self,
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        head_only: bool = False,
    ) -> AsyncReaderContextManager[ThreadedFileReader]:
        if executor is None or isinstance(executor, concurrent.futures.ThreadPoolExecutor):
            # asyncio forces the default executor when this is None to always be a
            # thread pool executor anyway, so this is safe enough to do:
            return _ThreadedFileReader(executor, self.filename, self.path)

        raise TypeError("The executor must be a ThreadPoolExecutor or None")


# Web streams.


@attr.define(weakref_slot=False)
class WebReader(AsyncReader):
    """Asynchronous reader to use to read data from a web resource."""

    stream: aiohttp.StreamReader = attr.field(repr=False)
    """The `aiohttp.StreamReader` to read the content from."""

    url: str = attr.field(repr=False)
    """The URL being read from."""

    status: int = attr.field()
    """The initial HTTP response status."""

    reason: str = attr.field()
    """The HTTP response status reason."""

    charset: typing.Optional[str] = attr.field()
    """Optional character set information, if known."""

    size: typing.Optional[int] = attr.field()
    """The size of the resource, if known."""

    head_only: bool = attr.field()
    """If `True`, then only the HEAD was requested.
    In this case, neither `__aiter__` nor `read` would return anything other
    than an empty byte string.
    """

    async def read(self) -> bytes:
        return b"" if self.head_only else await self.stream.read()

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        if self.head_only:
            yield b""
        else:
            while not self.stream.at_eof():
                chunk, _ = await self.stream.readchunk()
                yield chunk


@attr.define(weakref_slot=False)
@typing.final
class _WebReader(AsyncReaderContextManager[WebReader]):

    _web_resource: URL = attr.field()
    _head_only: bool = attr.field()
    _exit_stack: typing.Optional[contextlib.AsyncExitStack] = None

    async def __aenter__(self) -> WebReader:
        stack = contextlib.AsyncExitStack()

        client_session = await stack.enter_async_context(aiohttp.ClientSession())
        method = "HEAD" if self._head_only else "GET"

        try:
            resp = await stack.enter_async_context(
                client_session.request(method, self._web_resource.url, raise_for_status=False)
            )

            if 200 <= resp.status < 400:
                mimetype = None
                filename = self._web_resource.filename

                if resp.content_disposition is not None:
                    mimetype = resp.content_disposition.type

                if mimetype is None:
                    mimetype = resp.content_type

                self._exit_stack = stack

                return WebReader(
                    stream=resp.content,
                    url=str(resp.real_url),
                    status=resp.status,
                    reason=str(resp.reason),  # pyright: ignore
                    filename=filename,
                    charset=resp.charset,
                    mimetype=mimetype,
                    size=resp.content_length,
                    head_only=self._head_only,
                )
            else:
                raise RuntimeError(f"{resp.status}, {await resp.read()}")

        except Exception:
            await stack.aclose()
            raise

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        if self._exit_stack:
            await self._exit_stack.aclose()


@typing.final
class URL(Resource[WebReader]):
    """A URL that represents a web resource."""

    __slots__: typing.Sequence[str] = ("_url",)

    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    @property
    def filename(self) -> str:
        url = urllib.parse.urlparse(self._url)
        return os.path.basename(url.path)

    def stream(
        self,
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        head_only: bool = False,
    ) -> AsyncReaderContextManager[WebReader]:
        return _WebReader(self, head_only)


# In-memory data and streams.


@attr.define(weakref_slot=False)
class IteratorReader(AsyncReader):
    """Asynchronous file reader that operates on in-memory data."""

    data: typing.Union[bytes, LazyByteIterator] = attr.field()
    """The data that will be yielded in chunks."""

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        buff = bytearray()
        iterator = self._wrap_iter()

        while True:
            try:
                while len(buff) < _BUFFER_SIZE:
                    chunk = await iterator.__anext__()
                    buff.extend(chunk)
                yield bytes(buff)
                buff.clear()
            except StopAsyncIteration:
                break

        if buff:
            yield bytes(buff)

    async def _wrap_iter(self) -> typing.AsyncGenerator[typing.Any, bytes]:  # noqa: C901
        if isinstance(self.data, bytes):
            for i in range(0, len(self.data), _BUFFER_SIZE):
                yield self.data[i : i + _BUFFER_SIZE]

        elif async_utils.is_async_iterator(self.data) or inspect.isasyncgen(self.data):
            try:
                while True:
                    yield self._assert_bytes(await self.data.__anext__())
            except StopAsyncIteration:
                pass

        elif isinstance(self.data, typing.Iterator):
            try:
                while True:
                    yield self._assert_bytes(next(self.data))  # pyright: ignore
            except StopIteration:
                pass

        elif inspect.isgenerator(self.data):
            try:
                while True:
                    yield self._assert_bytes(self.data.send(None))
            except StopIteration:
                pass

        elif async_utils.is_async_iterable(self.data):
            async for chunk in self.data:
                yield self._assert_bytes(chunk)

        elif isinstance(self.data, typing.Iterable):
            for chunk in self.data:
                yield self._assert_bytes(chunk)

        else:
            # Will always fail.
            self._assert_bytes(self.data)

    @staticmethod
    def _assert_bytes(data: typing.Any) -> bytes:
        if isinstance(data, str):
            return bytes(data, "utf-8")

        if not isinstance(data, bytes):
            raise TypeError(f"Expected bytes but received {type(data).__name__}")
        return data


@attr.define(weakref_slot=False)
class _NoOpAsyncReader(AsyncReaderContextManager[ReaderT]):
    impl: ReaderT = attr.field()

    async def __aenter__(self) -> ReaderT:
        return self.impl

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        pass


class Bytes(Resource[IteratorReader]):
    """Representation of in-memory data to upload."""

    __slots__: typing.Sequence[str] = ("data", "_filename", "mimetype", "is_spoiler")

    data: typing.Union[bytes, LazyByteIterator]
    """The raw data/provider of raw data to upload."""

    mimetype: typing.Optional[str]
    """The provided mimetype, if provided. Otherwise `None`."""

    is_spoiler: bool
    """Whether the file will be marked as a spoiler."""

    def __init__(
        self,
        data: typing.Union[RawData, LazyByteIterator],
        filename: str,
        /,
        mimetype: typing.Optional[str] = None,
        *,
        spoiler: bool = False,
    ) -> None:
        if isinstance(data, RawData):
            data = unwrap_bytes(data)

        self.data = data

        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(filename)

        if mimetype is None:
            mimetype = "text/plain;charset=UTF-8"

        self._filename = filename
        self.mimetype = mimetype
        self.is_spoiler = spoiler

    @property
    def filename(self) -> str:
        return self._filename

    def stream(
        self,
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        head_only: bool = False,
    ) -> AsyncReaderContextManager[IteratorReader]:
        """Start streaming the content in chunks."""
        return _NoOpAsyncReader(IteratorReader(self.filename, self.mimetype, self.data))
