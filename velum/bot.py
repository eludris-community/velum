from __future__ import annotations

import asyncio
import logging
import time
import typing

from velum import entity_factory
from velum import event_factory
from velum import event_manager
from velum import event_manager_base
from velum import gateway
from velum import rest
from velum.events import base_events

T = typing.TypeVar("T")
_MaybeType = typing.Optional[typing.Type[T]]


_LOGGER = logging.getLogger("velum.bot")


class GatewayBot:
    def __init__(
        self,
        rest_url: typing.Optional[str] = None,
        # TODO: replace with prototypes
        entity_factory_impl: _MaybeType[entity_factory.EntityFactory] = None,
        event_factory_impl: _MaybeType[event_factory.EventFactory] = None,
        event_manager_impl: _MaybeType[event_manager.EventManager] = None,
        gateway_impl: _MaybeType[gateway.GatewayHandler] = None,
        rest_client_impl: _MaybeType[rest.RESTClient] = None,
    ):
        # Apply implementation defaults...
        entity_factory_impl = entity_factory_impl or entity_factory.EntityFactory
        event_factory_impl = event_factory_impl or event_factory.EventFactory
        event_manager_impl = event_manager_impl or event_manager.EventManager
        gateway_impl = gateway_impl or gateway.GatewayHandler
        rest_client_impl = rest_client_impl or rest.RESTClient

        self._entity_factory = entity_factory_impl()
        self._event_factory = event_factory_impl(self._entity_factory)
        self._event_manager = event_manager_impl(self._event_factory)

        # RESTful API.
        self._rest = rest_client_impl(rest_url=rest_url, entity_factory=self._entity_factory)

        # Gateway connection.
        self._gateway = gateway_impl(event_manager=self._event_manager)

        # Setup state.
        self._closing_event: typing.Optional[asyncio.Event] = None

    async def start(self) -> None:
        if self._closing_event:
            raise RuntimeError("Cannot start an already running bot.")

        start_time = time.monotonic()
        self._closing_event = asyncio.Event()

        self._rest.start()
        await self._gateway.start()

        _LOGGER.info(
            "Started succesfully in approximately %.2f [s].",
            time.monotonic() - start_time,
        )

        await self._closing_event.wait()

    async def close(self) -> None:
        if not self._closing_event:
            raise RuntimeError("Cannot close an inactive bot.")

        if self._closing_event.is_set():
            return

        self._closing_event.set()

        loop = asyncio.get_running_loop()

        async def handle(name: str, awaitable: typing.Awaitable[typing.Any]) -> None:
            future = asyncio.ensure_future(awaitable)

            try:
                await future
            except Exception as ex:
                loop.call_exception_handler(
                    {
                        "message": f"{name} raised an exception during shut down",
                        "future": future,
                        "exception": ex,
                    }
                )

        await handle("gateway", self._gateway.close())
        await handle("rest", self._rest.close())

        self._closing_event = None

        _LOGGER.info("Bot closed successfully.")

    @property
    def entity_factory(self) -> entity_factory.EntityFactory:
        return self._entity_factory

    @property
    def event_factory(self) -> event_factory.EventFactory:
        return self._event_factory

    @property
    def event_manager(self) -> event_manager.EventManager:
        return self._event_manager

    @property
    def rest(self) -> rest.RESTClient:
        return self._rest

    @property
    def gateway(self) -> gateway.GatewayHandler:
        return self._gateway

    @property
    def is_alive(self) -> bool:
        return self._closing_event is not None

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        return self._event_manager.dispatch(event)

    def get_listeners(
        self,
        event_type: typing.Type[base_events.EventT],
        /,
        *,
        polymorphic: bool = True,
    ) -> typing.Collection[base_events.EventCallbackT[base_events.EventT]]:
        return self._event_manager.get_listeners(event_type, polymorphic=polymorphic)

    def listen(
        self, *event_types: typing.Type[base_events.EventT]
    ) -> typing.Callable[
        [base_events.EventCallbackT[base_events.EventT]],
        base_events.EventCallbackT[base_events.EventT],
    ]:
        return self._event_manager.listen(*event_types)

    def subscribe(
        self,
        event_type: typing.Type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        self._event_manager.subscribe(event_type, callback)

    def unsubscribe(
        self,
        event_type: typing.Type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        self._event_manager.unsubscribe(event_type, callback)

    async def wait_for(
        self,
        event_type: typing.Type[base_events.EventT],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_manager_base.EventPredicateT[base_events.EventT]] = None,
    ) -> base_events.EventT:
        return await self._event_manager.wait_for(event_type, timeout=timeout, predicate=predicate)
