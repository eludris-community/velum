import typing

from velum.traits import entity_factory_trait
from velum.traits import event_factory_trait
from velum.traits import event_manager_trait
from velum.traits import gateway_trait
from velum.traits import rest_trait

__all__: typing.Sequence[str] = (
    "GatewayAware",
    "RESTAware",
    "EventAware",
    "EntityAware",
)


class GatewayAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def gateway(self) -> gateway_trait.GatewayHandler:
        ...


class RESTAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def rest(self) -> rest_trait.RESTClient:
        ...


class EventAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def event_factory(self) -> event_factory_trait.EventFactory:
        ...

    @property
    def event_manager(self) -> event_manager_trait.EventManager:
        ...


class EntityAware(typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    @property
    def entity_factory(self) -> entity_factory_trait.EntityFactory:
        ...
