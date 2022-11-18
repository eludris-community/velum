import asyncio
import typing


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
