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
        version = typing.cast(str, payload["version"])
        description = typing.cast(typing.Optional[str], payload["description"])
        message_limit = typing.cast(int, payload["message_limit"])
        oprish_url = typing.cast(str, payload["oprish_url"])
        pandemonium_url = typing.cast(str, payload["pandemonium_url"])
        effis_url = typing.cast(str, payload["effis_url"])
        file_size = typing.cast(int, payload["file_size"])
        attachment_file_size = typing.cast(int, payload["attachment_file_size"])

        rate_limits = typing.cast(
            typing.Optional[data_binding.JSONObject], payload.get("rate_limits")
        )
        if rate_limits is not None:
            rate_limits = self.deserialize_ratelimits(rate_limits)

        return models.InstanceInfo(
            instance_name=instance_name,
            description=description,
            version=version,
            message_limit=int(message_limit),
            oprish_url=oprish_url,
            pandemonium_url=pandemonium_url,
            effis_url=effis_url,
            file_size=int(file_size),
            attachment_file_size=int(attachment_file_size),
            rate_limits=rate_limits,
        )

    def _deserialize_ratelimit_config(
        self,
        payload: data_binding.JSONObject,
    ) -> models.RatelimitConf:
        reset_after = typing.cast(int, payload["reset_after"])
        limit = typing.cast(int, payload["limit"])

        return models.RatelimitConf(reset_after=reset_after, limit=limit)

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
    ) -> models.EffisRatelimitConf:
        reset_after = typing.cast(int, payload["reset_after"])
        limit = typing.cast(int, payload["limit"])
        file_size_limit = typing.cast(int, payload["file_size_limit"])

        return models.EffisRatelimitConf(
            reset_after=reset_after,
            limit=limit,
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
        fetch_file = self._deserialize_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["fetch_file"])
        )

        return models.EffisRatelimits(assets=assets, attachments=attachments, fetch_file=fetch_file)

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
        width = typing.cast(typing.Optional[int], payload.get("width"))
        height = typing.cast(typing.Optional[int], payload.get("height"))

        return models.FileMetadata(type=type_, width=width, height=height)

    def deserialize_file_data(self, payload: data_binding.JSONObject) -> models.FileData:
        id = typing.cast(int, payload["id"])
        name = typing.cast(str, payload["name"])
        bucket = typing.cast(str, payload["bucket"])
        spoiler = typing.cast(typing.Optional[bool], payload.get("spoiler"))
        metadata = self._deserialize_file_metadata(
            typing.cast(data_binding.JSONObject, payload["metadata"])
        )

        return models.FileData(
            id=id, name=name, bucket=bucket, spoiler=bool(spoiler), metadata=metadata
        )

    def _deserialize_pandemonium_config(
        self, payload: data_binding.JSONObject
    ) -> models.PandemoniumConf:
        url = typing.cast(str, payload["url"])
        rate_limit = self._deserialize_ratelimit_config(
            typing.cast(data_binding.JSONObject, payload["rate_limit"])
        )

        return models.PandemoniumConf(url=url, rate_limit=rate_limit)

    def deserialize_hello(self, payload: data_binding.JSONObject) -> models.Hello:
        heartbeat_interval = typing.cast(int, payload["heartbeat_interval"])
        instance_info = self.deserialize_instance_info(
            typing.cast(data_binding.JSONObject, payload["instance_info"])
        )
        pandemonium_info = self._deserialize_pandemonium_config(
            typing.cast(data_binding.JSONObject, payload["pandemonium_info"])
        )

        return models.Hello(
            heartbeat_interval=heartbeat_interval,
            instance_info=instance_info,
            pandemonium_info=pandemonium_info,
        )

    def deserialize_ratelimit(self, payload: data_binding.JSONObject) -> models.RatelimitData:
        wait = typing.cast(int, payload["wait"])

        return models.RatelimitData(wait=wait)
