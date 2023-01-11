import typing

from velum import models
from velum.api import entity_factory_trait
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("EntityFactory",)


class EntityFactory(entity_factory_trait.EntityFactory):

    __slots__ = ()

    def deserialize_message(self, payload: data_binding.JSONObject) -> models.Message:
        content = typing.cast(str, payload["content"])
        author = typing.cast(str, payload["author"])

        return models.Message(content=content, author=author)

    def deserialize_instance_info(self, payload: data_binding.JSONObject) -> models.InstanceInfo:
        instance_name = typing.cast(str, payload["instance_name"])
        description = typing.cast(typing.Optional[str], payload["description"])
        message_limit = typing.cast(str, payload["message_limit"])
        oprish_url = typing.cast(str, payload["oprish_url"])
        pandemonium_url = typing.cast(str, payload["pandemonium_url"])
        effis_url = typing.cast(str, payload["effis_url"])
        file_size = typing.cast(str, payload["file_size"])
        attachment_file_size = typing.cast(str, payload["attachment_file_size"])

        return models.InstanceInfo(
            instance_name=instance_name,
            description=description,
            message_limit=int(message_limit),
            oprish_url=oprish_url,
            pandemonium_url=pandemonium_url,
            effis_url=effis_url,
            file_size=int(file_size),
            attachment_file_size=int(attachment_file_size),
        )

    def _deserialize_ratelimit_config(
        self,
        payload: data_binding.JSONObject,
    ) -> models.RatelimitConfig:
        reset_after = typing.cast(str, payload["reset_after"])
        limit = typing.cast(str, payload["limit"])

        return models.RatelimitConfig(reset_after=int(reset_after), limit=int(limit))

    def _deserialize_oprish_ratelimits(
        self,
        payload: data_binding.JSONObject,
    ) -> models.OprishRatelimits:
        info = self._deserialize_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["info"])
        )
        message_create = self._deserialize_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["message_create"])
        )
        ratelimits = self._deserialize_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["ratelimits"])
        )

        return models.OprishRatelimits(
            info=info,
            message_create=message_create,
            ratelimits=ratelimits,
        )

    def _deserialize_effis_ratelimit_config(
        self,
        payload: data_binding.JSONObject,
    ) -> models.EffisRatelimitConfig:
        reset_after = typing.cast(str, payload["reset_after"])
        limit = typing.cast(str, payload["limit"])
        file_size_limit = typing.cast(str, payload["file_size_limit"])

        return models.EffisRatelimitConfig(
            reset_after=int(reset_after),
            limit=int(limit),
            file_size_limit=file_size_limit,
        )

    def _deserialize_effis_ratelimits(
        self,
        payload: data_binding.JSONObject,
    ) -> models.EffisRatelimits:
        assets = self._deserialize_effis_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["assets"])
        )
        attachments = self._deserialize_effis_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["attachments"])
        )

        return models.EffisRatelimits(assets=assets, attachments=attachments)

    def deserialize_ratelimits(self, payload: data_binding.JSONObject) -> models.InstanceRatelimits:
        oprish = self._deserialize_oprish_ratelimits(
            typing.cast(data_binding.JSONObject, payload["oprish"])
        )
        pandemonium = self._deserialize_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["pandemonium"])
        )
        effis = self._deserialize_effis_ratelimits(
            typing.cast(data_binding.JSONObject, payload["effis"])
        )

        return models.InstanceRatelimits(
            oprish=oprish,
            pandemonium=pandemonium,
            effis=effis,
        )

    def _deserialize_file_metadata(self, payload: data_binding.JSONObject) -> models.FileMetadata:
        type_ = typing.cast(str, payload["type"])
        width = typing.cast(typing.Optional[str], payload.get("width"))
        height = typing.cast(typing.Optional[str], payload.get("height"))

        return models.FileMetadata(
            type=type_,
            width=int(width) if width else None,
            height=int(height) if height else None,
        )

    def deserialize_file_data(self, payload: data_binding.JSONObject) -> models.FileData:
        id = typing.cast(str, payload["id"])
        name = typing.cast(str, payload["name"])
        bucket = typing.cast(str, payload["bucket"])
        spoiler = typing.cast(typing.Optional[str], payload.get("spoiler"))
        metadata = self._deserialize_file_metadata(
            typing.cast(data_binding.JSONObject, payload["metadata"])
        )

        return models.FileData(
            id=int(id),
            name=name,
            bucket=bucket,
            spoiler=True if spoiler else False,
            metadata=metadata,
        )
