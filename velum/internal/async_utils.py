import asyncio
import typing

__all__: typing.Sequence[str] = (
    "create_completed_future",
    "cancel_futures",
    "first_completed",
)


_T = typing.TypeVar("_T")


def create_completed_future(
    result: typing.Optional[_T] = None, /
) -> asyncio.Future[typing.Optional[_T]]:
    future = asyncio.get_running_loop().create_future()
    future.set_result(result)
    return future


async def cancel_futures(futures: typing.Iterable[asyncio.Future[typing.Any]]) -> None:
    for future in futures:
        if not future.done() and not future.cancelled():
            future.cancel()
            try:
                await future
            except asyncio.CancelledError:
                pass


async def first_completed(
    *awaitables: typing.Awaitable[typing.Any],
    timeout: typing.Optional[float] = None,
) -> None:
    futures = tuple(map(asyncio.ensure_future, awaitables))
    iter_ = asyncio.as_completed(futures, timeout=timeout)

    try:
        await next(iter_)
    except Exception:
        raise
    finally:
        await cancel_futures(futures)
