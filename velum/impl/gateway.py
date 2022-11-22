from __future__ import annotations

import asyncio
import contextlib
import json  # TODO: remove
import logging
import time
import typing

import aiohttp

from velum import errors
from velum.impl import rate_limits
from velum.internal import async_utils
from velum.internal import typing_patches
from velum.traits import event_manager_trait
from velum.traits import gateway_trait
from velum.traits import rate_limit_trait

_BACKOFF_WINDOW: typing.Final[float] = 15.0
_GATEWAY_URL: typing.Final[str] = "wss://eludris.tooty.xyz/ws/"
_HEARTBEAT_INTERVAL: typing.Final[float] = 20.0


class GatewayWebsocket:

    __slots__ = (
        "_gateway_url",
        "_logger",
        "_ws",
        "_exit_stack",
        "_closed",
    )

    def __init__(
        self,
        *,
        gateway_url: str,
        logger: logging.Logger,
        websocket: aiohttp.ClientWebSocketResponse,
        exit_stack: contextlib.AsyncExitStack,
    ):
        self._gateway_url = gateway_url
        self._logger = logger
        self._ws = websocket
        self._exit_stack = exit_stack

        self._closed = False

    @classmethod
    async def connect(
        cls,
        *,
        logger: logging.Logger,
        url: str,
    ) -> GatewayWebsocket:
        exit_stack = contextlib.AsyncExitStack()

        try:
            session = await exit_stack.enter_async_context(aiohttp.ClientSession())
            ws = await exit_stack.enter_async_context(
                session.ws_connect(  # pyright: ignore[reportUnknownMemberType]
                    url,
                    max_msg_size=0,
                    autoclose=False,
                )
            )

            return cls(
                gateway_url=url,
                logger=logger,
                websocket=ws,
                exit_stack=exit_stack,
            )

        except Exception as exc:
            await exit_stack.aclose()
            await asyncio.sleep(0.25)  # Workaround for aiohttp fuckywucky

            if isinstance(exc, (aiohttp.ClientConnectionError, aiohttp.ClientResponseError)):
                raise errors.GatewayConnectionError(str(exc)) from None
            elif isinstance(exc, asyncio.TimeoutError):
                raise errors.GatewayConnectionError("Connection timed out.") from None

            raise

    async def send_close(self, *, code: int, message: str | bytes) -> None:
        if self._closed:
            return

        if isinstance(message, str):
            message = message.encode()

        self._closed = True
        self._logger.debug("Sending close frame with opcode %s and message %s.", code, message)

        try:
            await asyncio.wait_for(self._ws.close(code=code, message=message), timeout=5)

        except asyncio.TimeoutError:
            self._logger.debug("Failed to send close frame. Connection may be faulty.")

        finally:
            await self._exit_stack.aclose()
            await asyncio.sleep(0.25)

    async def send_ping(self) -> None:
        await self._ws.ping()

    async def send_json(self, data: typing.Mapping[str, typing.Any]) -> None:
        payload = json.dumps(data)  # TODO: provide entrypoint to change json loads/dumps funcs

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Sending payload with size %s:\n\t%s", len(payload), payload)

        await self._ws.send_str(payload)

    async def receive_json(self) -> typing.Any:
        payload = await self._receive_and_validate_text()

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Received payload with size %s:\n\t%s", len(payload), payload)

        return json.loads(payload)  # TODO: provide entrypoint to change json loads/dumps funcs

    async def _receive_and_validate_text(self) -> str:
        message = typing.cast(typing_patches.WSMessage, await self._ws.receive())

        if message.type == aiohttp.WSMsgType.TEXT:
            assert isinstance(message.data, str)
            return message.data

        self._raise_for_unhandled_message(message)

    # TODO: implement zlib whenever eludris does

    def _raise_for_unhandled_message(self, message: typing_patches.WSMessage) -> typing.NoReturn:
        if message.type == aiohttp.WSMsgType.TEXT:
            raise errors.GatewayError("Unexpected message type: received TEXT, expected BINARY.")

        if message.type == aiohttp.WSMsgType.BINARY:
            raise errors.GatewayError("Unexpected message type: received BINARY, expected TEXT.")

        if message.type == aiohttp.WSMsgType.CLOSE:
            assert message.data is not None
            assert message.extra is not None
            close_code = int(message.data)

            raise errors.GatewayConnectionClosedError(message.extra, close_code)

        if message.type in (aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
            raise errors.GatewayConnectionError("Socket was closed.")

        raise errors.GatewayError(
            "Unexpected websocket exception from gateway."
        ) from self._ws.exception()


class GatewayHandler(gateway_trait.GatewayHandler):

    __slots__ = (
        "_connection_event",
        "_event_manager",
        "_gateway_url",
        "_gateway_ws",
        "_is_closing",
        "_keep_alive_task",
        "_last_heartbeat",
        "_last_heartbeat_ack",
        "_logger",
        "_started_at",
    )

    _connection_event: typing.Optional[asyncio.Event]
    _event_manager: event_manager_trait.EventManager
    _gateway_ws: typing.Optional[GatewayWebsocket]
    _keep_alive_task: typing.Optional[asyncio.Task[None]]
    _last_heartbeat: float
    _last_heartbeat_ack: float
    _logger: logging.Logger
    _started_at: float

    def __init__(
        self,
        *,
        gateway_url: typing.Optional[str] = None,
        event_manager: event_manager_trait.EventManager,
    ):
        self._event_manager = event_manager

        self._connection_event = None
        self._gateway_url = gateway_url or _GATEWAY_URL
        self._gateway_ws = None
        self._keep_alive_task = None
        self._is_closing = False
        self._last_heartbeat = float("nan")
        self._last_heartbeat_ack = float("nan")
        self._logger = logging.getLogger("velum.gateway")
        self._started_at = float("-inf")

    @property
    def is_alive(self) -> bool:
        return self._keep_alive_task is not None

    async def start(self) -> None:
        if self._connection_event:
            raise RuntimeError("Cannot start an already connected GatewayHandler.")

        self._connection_event = asyncio.Event()

        backoff = rate_limits.ExponentialBackoff()
        keep_alive_task = asyncio.create_task(
            self._keep_alive(backoff=backoff),
            name="keep-alive",
        )

        await async_utils.first_completed(
            self._connection_event.wait(),
            asyncio.shield(keep_alive_task),
        )

        if not self._connection_event.is_set():
            keep_alive_task.result()
            raise RuntimeError("Connection was closed before it could start successfully.")

        self._keep_alive_task = keep_alive_task

    async def close(self) -> None:
        if not self._keep_alive_task:
            raise RuntimeError("Cannot close an inactive GatewayHandler")

        if self._is_closing:
            # Repeated call of this method. Wait for the keep-alive task to finish and just return.
            await asyncio.wait_for(asyncio.shield(self._keep_alive_task), timeout=None)
            return

        self._logger.info("Attempting to close gateway connection...")
        self._is_closing = True

        await async_utils.cancel_futures((self._keep_alive_task,))

        self._keep_alive_task = None
        self._is_closing = False
        self._logger.info("Gateway connection closed successfully.")

    async def _poll_events(self) -> None:
        assert self._gateway_ws is not None
        assert self._connection_event is not None

        while True:
            payload = await self._gateway_ws.receive_json()

            # NOTE: Currently the only event dispatched by eludris.
            #       Waiting on a proper payload implementation so we can get tje
            #       event name from the actual payload.
            event_name = "MESSAGE_CREATE"

            self._event_manager.consume_raw_event(event_name, self, payload)

    # TODO: make backoff protocol, replace typehint with proto
    async def _keep_alive(self, backoff: rate_limit_trait.RateLimiter) -> None:
        assert self._connection_event is not None

        lifetime_tasks: typing.Tuple[asyncio.Task[typing.Any], ...] = ()

        while True:
            self._connection_event.clear()

            if time.monotonic() - self._started_at < _BACKOFF_WINDOW:
                backoff_time = next(backoff)
                self._logger.info("Backing off of reconnecting for %s [s].", backoff_time)
                await asyncio.sleep(backoff_time)

            try:
                self._started_at = time.monotonic()
                lifetime_tasks = await self._connect()

                if not self._connection_event.is_set():
                    continue

                # Keep running until one of the tasks stops
                await async_utils.first_completed(*lifetime_tasks)

                backoff.reset()

            except errors.GatewayConnectionError as exc:
                self._logger.warning(
                    "Failed to communicate with the gateway, with reason %s. "
                    "Attempting to reconnect shortly...",
                    exc.reason,
                )

            except asyncio.CancelledError:
                self._is_closing = True
                return

            except Exception as exc:
                self._logger.error(
                    "Encountered an unhandled error in communicating with the gateway.",
                    exc_info=exc,
                )

            finally:
                await async_utils.cancel_futures(lifetime_tasks)

                if self._gateway_ws:
                    ws = self._gateway_ws
                    self._gateway_ws = None

                    await ws.send_close(code=1000, message=b"see ya")

                # TODO: dispatch "disconnected" event?

    async def _connect(self) -> typing.Tuple[asyncio.Task[typing.Any], ...]:
        if self._gateway_ws is not None:
            raise RuntimeError("This GatewayConnection is already connected with the gateway.")

        assert self._connection_event is not None

        self._gateway_ws = await GatewayWebsocket.connect(
            logger=self._logger, url=self._gateway_url
        )

        heartbeat_task = asyncio.create_task(self._heartbeat(), name="heartbeat")
        poll_events_task = asyncio.create_task(self._poll_events(), name="poll events")

        # Indicate connection logic is done.
        self._connection_event.set()

        return (heartbeat_task, poll_events_task)

    async def _heartbeat(self) -> None:
        assert self._gateway_ws is not None

        self._last_heartbeat_ack = time.monotonic()
        self._logger.debug("Starting heartbeat with interval %s [s].", _HEARTBEAT_INTERVAL)

        while True:

            # TODO: uncomment when eludris switches to opcode pings

            # if self._last_heartbeat_ack <= self._last_heartbeat:
            #     self._logger.error(
            #         "Heartbeat was not acknowledged for approximately %s [s], "
            #         "we will now disconnect and attempt to reconnect.",
            #         time.monotonic() - self._last_heartbeat_ack,
            #     )
            #     return

            self._logger.debug("Sending heartbeat.")
            await self._gateway_ws.send_ping()
            self._last_heartbeat = time.monotonic()

            await asyncio.sleep(_HEARTBEAT_INTERVAL)
