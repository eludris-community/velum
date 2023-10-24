from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import sys
import time
import typing

import aiohttp

from velum import errors
from velum import events
from velum import models
from velum.api import event_manager_trait
from velum.api import gateway_trait
from velum.api import rate_limit_trait
from velum.events import connection_events
from velum.impl import rate_limits
from velum.internal import async_utils
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("GatewayHandler",)


if typing.TYPE_CHECKING:

    class _WSMessage(typing.Protocol):
        type: aiohttp.WSMsgType
        data: str | bytes | None
        extra: str | None

        def json(self, loads: typing.Callable[[typing.Any], typing.Any] = ...) -> typing.Any:  # noqa: ANN401
            ...


_BACKOFF_WINDOW: typing.Final[float] = 15.0
_GATEWAY_URL: typing.Final[str] = "wss://ws.eludris.gay"

# Payload attributes.
_OP: typing.Final[str] = sys.intern("op")
_D: typing.Final[str] = sys.intern("d")

# Special opcodes.
_PONG: typing.Final[str] = sys.intern("PONG")
_PING: typing.Final[str] = sys.intern("PING")
_HELLO: typing.Final[str] = sys.intern("HELLO")
_AUTHENTICATE: typing.Final[str] = sys.intern("AUTHENTICATE")


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
    ) -> None:
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
            session = await exit_stack.enter_async_context(
                aiohttp.ClientSession(json_serialize=data_binding.dump_json),
            )
            ws = await exit_stack.enter_async_context(
                session.ws_connect(  # pyright: ignore[reportUnknownMemberType]
                    url,
                    max_msg_size=0,
                    autoclose=False,
                ),
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

            if isinstance(exc, aiohttp.ClientConnectionError | aiohttp.ClientResponseError):
                raise errors.GatewayConnectionError(str(exc)) from None
            if isinstance(exc, asyncio.TimeoutError):
                msg = "Connection timed out."
                raise errors.GatewayConnectionError(msg) from None

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

    async def send_json(self, data: typing.Mapping[str, typing.Any]) -> None:
        payload = data_binding.dump_json(data)

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Sending payload with size %s:\n\t%s", len(payload), payload)

        await self._ws.send_str(payload)

    async def receive_json(self) -> data_binding.JSONObject:
        payload = await self._receive_and_validate_text()

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Received payload with size %s:\n\t%s", len(payload), payload)

        data = data_binding.load_json(payload)
        assert isinstance(data, dict)

        return data

    async def _receive_and_validate_text(self) -> str:
        message = typing.cast("_WSMessage", await self._ws.receive())

        if message.type == aiohttp.WSMsgType.TEXT:
            assert isinstance(message.data, str)
            return message.data

        self._raise_for_unhandled_message(message)
        return None

    # TODO: implement zlib whenever eludris does

    def _raise_for_unhandled_message(self, message: _WSMessage) -> typing.NoReturn:
        if message.type == aiohttp.WSMsgType.TEXT:
            msg = "Unexpected message type: received TEXT, expected BINARY."
            raise errors.GatewayError(msg)

        if message.type == aiohttp.WSMsgType.BINARY:
            msg = "Unexpected message type: received BINARY, expected TEXT."
            raise errors.GatewayError(msg)

        if message.type == aiohttp.WSMsgType.CLOSE:
            assert message.data is not None
            assert message.extra is not None
            close_code = int(message.data)

            raise errors.GatewayConnectionClosedError(message.extra, close_code)

        if message.type in (aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
            msg = "Socket was closed."
            raise errors.GatewayConnectionError(msg)

        msg = "Unexpected websocket exception from gateway."
        raise errors.GatewayError(msg) from self._ws.exception()


class GatewayHandler(gateway_trait.GatewayHandler):
    __slots__ = (
        "_authenticated_event",
        "_connection_event",
        "_event_manager",
        "_gateway_url",
        "_gateway_ws",
        "_heartbeat_latency",
        "_is_closing",
        "_keep_alive_task",
        "_last_heartbeat",
        "_last_heartbeat_ack",
        "_logger",
        "_started_at",
        "_token",
        "_user",
    )

    _connection_event: asyncio.Event | None
    _authenticated_event: asyncio.Event
    _event_manager: event_manager_trait.EventManager
    _gateway_ws: GatewayWebsocket | None
    _heartbeat_latency: float
    _keep_alive_task: asyncio.Task[None] | None
    _last_heartbeat: float
    _last_heartbeat_ack: float
    _logger: logging.Logger
    _started_at: float
    _user: models.User | None

    def __init__(
        self,
        *,
        gateway_url: str | None = None,
        event_manager: event_manager_trait.EventManager,
        token: str,
    ) -> None:
        self._event_manager = event_manager

        event_manager.subscribe(events.AuthenticatedEvent, self._handle_authenticated)

        self._connection_event = None
        self._authenticated_event = asyncio.Event()
        self._gateway_url = gateway_url or _GATEWAY_URL
        self._token = token
        self._gateway_ws = None
        self._heartbeat_latency = float("nan")
        self._keep_alive_task = None
        self._is_closing = False
        self._last_heartbeat = float("nan")
        self._last_heartbeat_ack = float("nan")
        self._logger = logging.getLogger("velum.gateway")
        self._started_at = float("-inf")
        self._user = None

    @property
    def is_alive(self) -> bool:
        return self._keep_alive_task is not None

    @property
    def user(self) -> models.User:
        if self._user is None:
            msg = "Cannot access user before authentication."
            raise RuntimeError(msg)

        return self._user

    async def start(self) -> None:
        if self._connection_event:
            msg = "Cannot start an already connected GatewayHandler."
            raise RuntimeError(msg)

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
            msg = "Connection was closed before it could start successfully."
            raise RuntimeError(msg)

        self._keep_alive_task = keep_alive_task

    async def close(self) -> None:
        if not self._keep_alive_task:
            msg = "Cannot close an inactive GatewayHandler"
            raise RuntimeError(msg)

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

    async def _handle_authenticated(self, event: events.AuthenticatedEvent) -> None:
        self._user = event.user
        self._authenticated_event.set()

    async def _poll_hello_event(self) -> float:
        assert self._gateway_ws is not None
        assert self._connection_event is not None

        payload = await self._gateway_ws.receive_json()
        assert isinstance(payload, dict)

        op = payload[_OP]

        if op != _HELLO:
            self._logger.debug(
                "Expected %r opcode, received %r. Closing connection.",
                _HELLO,
                op,
            )
            # TODO: Custom exception and don't use magic number.
            await self._gateway_ws.send_close(code=1002, message=b"Expected HELLO op.")
            msg = f"Expected opcode {_HELLO}, received {op} instead."
            raise RuntimeError(msg)

        data = typing.cast(data_binding.JSONObject, payload[_D])
        heartbeat_interval = typing.cast(float, data["heartbeat_interval"])  # in ms

        # TODO: Maybe return fully deserialised event and use ratelimit info.
        #       For now, only using the heartbeat interval will do.
        return heartbeat_interval / 1_000.0

    async def _poll_events(self) -> None:
        assert self._gateway_ws is not None
        assert self._connection_event is not None

        while True:
            payload = await self._gateway_ws.receive_json()
            op = payload[_OP]
            assert isinstance(op, str)

            if op == _PONG:
                now = time.monotonic()
                self._last_heartbeat_ack = now
                self._heartbeat_latency = now - self._last_heartbeat
                self._logger.debug("Received PONG in %.2f [ms].", self._heartbeat_latency * 1000)

            else:
                data = payload[_D]
                assert isinstance(data, dict)

                self._event_manager.consume_raw_event(op, self, data)

    async def _keep_alive(self, backoff: rate_limit_trait.RateLimiter) -> None:
        assert self._connection_event is not None

        lifetime_tasks: tuple[asyncio.Task[typing.Any], ...] = ()

        while True:
            self._connection_event.clear()

            if time.monotonic() - self._started_at < _BACKOFF_WINDOW:
                backoff_time = next(backoff)
                self._logger.info("Backing off of reconnecting for %.2f [s].", backoff_time)
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
                    "Failed to communicate with the gateway, with reason '%s'. "
                    "Attempting to reconnect shortly...",
                    exc.reason,
                )

            except asyncio.CancelledError:
                self._is_closing = True
                return

            except Exception as exc:
                self._logger.exception(
                    "Encountered an unhandled error in communicating with the gateway.",
                    exc_info=exc,
                )

            finally:
                await async_utils.cancel_futures(lifetime_tasks)

                if self._gateway_ws:
                    ws = self._gateway_ws
                    self._gateway_ws = None

                    await ws.send_close(code=1000, message=b"see ya")

                self._event_manager.dispatch(connection_events.DisconnectEvent())

    async def _connect(self) -> tuple[asyncio.Task[typing.Any], ...]:
        if self._gateway_ws is not None:
            msg = "This GatewayConnection is already connected with the gateway."
            raise RuntimeError(msg)

        assert self._connection_event is not None

        self._gateway_ws = await GatewayWebsocket.connect(
            logger=self._logger,
            url=self._gateway_url,
        )

        heartbeat_interval = await self._poll_hello_event()

        await self._gateway_ws.send_json({_OP: _AUTHENTICATE, _D: self._token})

        heartbeat_task = asyncio.create_task(self._heartbeat(heartbeat_interval), name="heartbeat")
        poll_events_task = asyncio.create_task(self._poll_events(), name="poll events")

        try:
            await asyncio.wait_for(self._authenticated_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            msg = "Failed to authenticate with the gateway."
            raise errors.GatewayConnectionError(msg) from None

        # Indicate connection logic is done.
        self._connection_event.set()
        self._event_manager.dispatch(connection_events.ConnectionEvent())

        return (heartbeat_task, poll_events_task)

    async def _send_heartbeat(self) -> None:
        self._logger.debug("Sending heartbeat.")

        assert self._gateway_ws
        await self._gateway_ws.send_json({_OP: _PING})

        self._last_heartbeat = time.monotonic()

    async def _heartbeat(self, heartbeat_interval: float) -> None:
        assert self._gateway_ws is not None

        jitter = random.random() * heartbeat_interval
        self._last_heartbeat_ack = time.monotonic()
        self._logger.debug(
            "Waiting %.2f [s] before starting heartbeat with interval %.2f [s].",
            jitter,
            heartbeat_interval,
        )

        await asyncio.sleep(jitter)

        while True:
            if self._last_heartbeat_ack <= self._last_heartbeat:
                self._logger.error(
                    "Heartbeat was not acknowledged for approximately %.2f [s], "
                    "we will now disconnect and attempt to reconnect.",
                    time.monotonic() - self._last_heartbeat_ack,
                )
                return

            await self._send_heartbeat()
            await asyncio.sleep(heartbeat_interval)
