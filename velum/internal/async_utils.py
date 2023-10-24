import asyncio
import contextlib
import inspect
import typing

__all__: typing.Sequence[str] = (
    "create_completed_future",
    "cancel_futures",
    "first_completed",
    "is_async_iterator",
    "is_async_iterable",
)


_T = typing.TypeVar("_T")


def create_completed_future(
    result: _T | None = None,
    /,
) -> asyncio.Future[_T | None]:
    future = asyncio.get_running_loop().create_future()
    future.set_result(result)
    return future


async def cancel_futures(futures: typing.Iterable[asyncio.Future[typing.Any]]) -> None:
    for future in futures:
        if not future.done() and not future.cancelled():
            future.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await future


async def first_completed(
    *awaitables: typing.Awaitable[typing.Any],
    timeout: float | None = None,
) -> None:
    futures = tuple(map(asyncio.ensure_future, awaitables))
    iter_ = asyncio.as_completed(futures, timeout=timeout)

    try:
        await next(iter_)
    finally:
        await cancel_futures(futures)


def is_async_iterator(obj: object) -> typing.TypeGuard[typing.AsyncIterator[object]]:
    """Determine if the object is an async iterator or not."""
    return asyncio.iscoroutinefunction(getattr(obj, "__anext__", None))


def is_async_iterable(obj: object) -> typing.TypeGuard[typing.AsyncIterable[object]]:
    """Determine if the object is an async iterable or not."""
    attr = getattr(obj, "__aiter__", None)
    return inspect.isfunction(attr) or inspect.ismethod(attr)
