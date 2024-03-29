from __future__ import annotations

import asyncio
import logging
import time
import typing

from velum import traits
from velum.impl import entity_factory
from velum.impl import event_factory
from velum.impl import event_manager
from velum.impl import gateway
from velum.impl import rest

if typing.TYPE_CHECKING:
    from velum.api import entity_factory_trait
    from velum.api import event_factory_trait
    from velum.api import event_manager_trait
    from velum.api import gateway_trait
    from velum.api import rest_trait
    from velum.events import base_events

__all__: typing.Sequence[str] = ("GatewayClient",)


_T = typing.TypeVar("_T")
_MaybeType = type[_T] | None


_LOGGER = logging.getLogger("velum.client")


class GatewayClient(traits.GatewayClientAware):
    __slots__: typing.Sequence[str] = (
        "_entity_factory",
        "_event_factory",
        "_event_manager",
        "_rest",
        "_gateway",
        "_closing_event",
    )

    _entity_factory: entity_factory_trait.EntityFactory
    _event_factory: event_factory_trait.EventFactory
    _event_manager: event_manager_trait.EventManager
    _rest: rest_trait.RESTClient
    _gateway: gateway_trait.GatewayHandler
    _closing_event: asyncio.Event | None

    def __init__(
        self,
        cdn_url: str | None = None,
        gateway_url: str | None = None,
        rest_url: str | None = None,
        entity_factory_impl: entity_factory_trait.EntityFactory | None = None,
        event_factory_impl: event_factory_trait.EventFactory | None = None,
        event_manager_impl: event_manager_trait.EventManager | None = None,
        gateway_impl: gateway_trait.GatewayHandler | None = None,
        rest_client_impl: rest_trait.RESTClient | None = None,
        *,
        token: str,
    ) -> None:
        self._entity_factory = (
            entity_factory_impl
            if entity_factory_impl is not None
            else entity_factory.EntityFactory()
        )
        self._event_factory = (
            event_factory_impl
            if event_factory_impl is not None
            else event_factory.EventFactory(self._entity_factory)
        )
        self._event_manager = (
            event_manager_impl
            if event_manager_impl is not None
            else event_manager.EventManager(self._event_factory)
        )

        # RESTful API.
        self._rest = (
            rest_client_impl
            if rest_client_impl is not None
            else rest.RESTClient(
                rest_url=rest_url,
                cdn_url=cdn_url,
                token=token,
                entity_factory=self._entity_factory,
            )
        )

        # Gateway connection.
        self._gateway = (
            gateway_impl
            if gateway_impl is not None
            else gateway.GatewayHandler(
                gateway_url=gateway_url,
                event_manager=self._event_manager,
                token=token,
            )
        )

        # Setup state.
        self._closing_event: asyncio.Event | None = None

    async def start(self) -> None:
        if self._closing_event:
            msg = "Cannot start an already running client."
            raise RuntimeError(msg)

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
            msg = "Cannot close an inactive client."
            raise RuntimeError(msg)

        if self._closing_event.is_set():
            return

        self._closing_event.set()

        loop = asyncio.get_running_loop()

        async def handle(name: str, awaitable: typing.Awaitable[typing.Any]) -> None:
            future = asyncio.ensure_future(awaitable)

            try:
                await future
            except Exception as ex:  # noqa: BLE001
                loop.call_exception_handler(
                    {
                        "message": f"{name} raised an exception during shut down",
                        "future": future,
                        "exception": ex,
                    },
                )

        await handle("gateway", self._gateway.close())
        await handle("rest", self._rest.close())

        self._closing_event = None

        _LOGGER.info("Client closed successfully.")

    @property
    def entity_factory(self) -> entity_factory_trait.EntityFactory:
        return self._entity_factory

    @property
    def event_factory(self) -> event_factory_trait.EventFactory:
        return self._event_factory

    @property
    def event_manager(self) -> event_manager_trait.EventManager:
        return self._event_manager

    @property
    def rest(self) -> rest_trait.RESTClient:
        return self._rest

    @property
    def gateway(self) -> gateway_trait.GatewayHandler:
        return self._gateway

    @property
    def is_alive(self) -> bool:
        return self._closing_event is not None

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        return self._event_manager.dispatch(event)

    def get_listeners(
        self,
        event_type: type[base_events.EventT],
        /,
        *,
        polymorphic: bool = True,
    ) -> typing.Collection[base_events.EventCallbackT[base_events.EventT]]:
        return self._event_manager.get_listeners(event_type, polymorphic=polymorphic)

    def listen(
        self,
        *event_types: type[base_events.EventT],
    ) -> typing.Callable[
        [base_events.EventCallbackT[base_events.EventT]],
        base_events.EventCallbackT[base_events.EventT],
    ]:
        return self._event_manager.listen(*event_types)

    def subscribe(
        self,
        event_type: type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        self._event_manager.subscribe(event_type, callback)

    def unsubscribe(
        self,
        event_type: type[base_events.EventT],
        callback: base_events.EventCallbackT[base_events.EventT],
    ) -> None:
        self._event_manager.unsubscribe(event_type, callback)

    async def wait_for(
        self,
        event_type: type[base_events.EventT],
        /,
        timeout: float | None,
        predicate: event_manager_trait.EventPredicateT[base_events.EventT] | None = None,
    ) -> base_events.EventT:
        return await self._event_manager.wait_for(event_type, timeout=timeout, predicate=predicate)
