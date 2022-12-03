import types
import typing

import typing_extensions

from velum import files
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

    async def __aenter__(self) -> typing_extensions.Self:
        ...

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
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

    # Effis.

    async def upload_to_bucket(
        self,
        bucket: str,
        /,
        file: files.ResourceLike,
        *,
        spoiler: bool = False,
    ) -> models.FileData:
        ...

    async def upload_attachment(
        self,
        attachment: files.ResourceLike,
        /,
        *,
        spoiler: bool = False,
    ) -> models.FileData:
        ...

    async def fetch_from_bucket(self, bucket: str, /, id: int) -> files.URL:
        ...

    async def fetch_attachment(self, id: int) -> files.URL:
        ...
