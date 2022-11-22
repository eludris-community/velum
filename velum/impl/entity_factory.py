import typing

from velum import models
from velum.internal import data_binding
from velum.traits import entity_factory_trait


class EntityFactory(entity_factory_trait.EntityFactory):

    __slots__ = ()

    def deserialize_message(self, payload: data_binding.JSONObject) -> models.Message:
        content = typing.cast(str, payload["content"])
        author = typing.cast(str, payload["author"])

        return models.Message(content=content, author=author)

    def deserialize_instance_info(self, payload: data_binding.JSONObject) -> models.InstanceInfo:
        instance_name = typing.cast(str, payload["instance_name"])
        features = typing.cast(models.FeatureSequence, payload["features"])

        return models.InstanceInfo(instance_name=instance_name, features=features)
