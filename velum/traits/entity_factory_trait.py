import typing

from velum import models


class EntityFactory(typing.Protocol):

    __slots__: typing.Sequence[str] = ()

    def deserialize_message(self, payload: typing.Dict[str, typing.Any]) -> models.Message:
        ...

    def deserialize_instance_info(
        self, payload: typing.Dict[str, typing.Any]
    ) -> models.InstanceInfo:
        ...
