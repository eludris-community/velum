import typing

from velum import models
from velum.internal import data_binding


class EntityFactory(typing.Protocol):

    __slots__: typing.Sequence[str] = ()

    def deserialize_message(self, payload: data_binding.JSONObject) -> models.Message:
        ...

    def deserialize_instance_info(self, payload: data_binding.JSONObject) -> models.InstanceInfo:
        ...

    def deserialize_ratelimits(self, payload: data_binding.JSONObject) -> models.InstanceRatelimits:
        ...

    def deserialize_file_data(self, payload: data_binding.JSONObject) -> models.FileData:
        ...
