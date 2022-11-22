import typing

from velum import models
from velum.traits import entity_factory_trait

__all__: typing.Sequence[str] = ("RESTClient",)


class RESTClient(typing.Protocol):

    __slots__: typing.Sequence[str] = ()

    @property
    def is_alive(self) -> bool:
        ...

    @property
    def entity_factory(self) -> entity_factory_trait.EntityFactory:
        ...

    def start(self) -> None:
        ...

    async def close(self) -> None:
        ...

    @typing.overload
    async def send_message(self, *, message: models.Message) -> None:
        ...

    @typing.overload
    async def send_message(self, author: str, message: str) -> None:
        ...

    async def send_message(
        self,
        author: typing.Optional[str] = None,
        message: typing.Optional[models.Message | str] = None,
    ) -> None:
        ...

    async def get_instance_info(self) -> models.InstanceInfo:
        ...
