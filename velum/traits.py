import typing

from velum.api import entity_factory_trait
from velum.api import event_factory_trait
from velum.api import event_manager_trait
from velum.api import gateway_trait
from velum.api import rest_trait

__all__: typing.Sequence[str] = (
    "EntityFactoryAware",
    "RESTAware",
    "EventFactoryAware",
    "EventManagerAware",
    "GatewayAware",
    "Runnable",
    "GatewayClientAware",
)


@typing.runtime_checkable
class EntityFactoryAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def entity_factory(self) -> entity_factory_trait.EntityFactory:
        ...


@typing.runtime_checkable
class RESTAware(EntityFactoryAware, typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def rest(self) -> rest_trait.RESTClient:
        ...


@typing.runtime_checkable
class EventFactoryAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def event_factory(self) -> event_factory_trait.EventFactory:
        ...


@typing.runtime_checkable
class EventManagerAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def event_manager(self) -> event_manager_trait.EventManager:
        ...


@typing.runtime_checkable
class GatewayAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def gateway(self) -> gateway_trait.GatewayHandler:
        ...


@typing.runtime_checkable
class Runnable(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def is_alive(self) -> bool:
        ...

    async def close(self) -> None:
        ...

    async def start(self) -> None:
        ...


@typing.runtime_checkable
class GatewayClientAware(
    EventFactoryAware,
    EventManagerAware,
    GatewayAware,
    RESTAware,
    Runnable,
    typing.Protocol,
):
    __slots__: typing.Sequence[str] = ()
