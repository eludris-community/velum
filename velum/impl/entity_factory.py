import typing

from velum import models
from velum.traits import entity_factory_trait


class EntityFactory(entity_factory_trait.EntityFactory):

    __slots__ = ()

    def deserialize_message(self, payload: typing.Dict[str, typing.Any]) -> models.Message:
        return models.Message(content=payload["content"], author=payload["author"])

    def deserialize_instance_info(
        self, payload: typing.Dict[str, typing.Any]
    ) -> models.InstanceInfo:
        return models.InstanceInfo(
            instance_name=payload["instance_name"], features=payload["features"]
        )
