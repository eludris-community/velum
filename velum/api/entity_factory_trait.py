import typing

from velum import models
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("EntityFactory",)


@typing.runtime_checkable
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

    def deserialize_hello(self, payload: data_binding.JSONObject) -> models.Hello:
        ...

    def deserialize_ratelimit(self, payload: data_binding.JSONObject) -> models.RatelimitData:
        ...

    def deserialize_authenticated(self, payload: data_binding.JSONObject) -> models.Authenticated:
        ...
