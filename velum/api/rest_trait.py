import types
import typing

import typing_extensions

from velum import files
from velum import models
from velum.api import entity_factory_trait

__all__: typing.Sequence[str] = ("RESTClient",)


@typing.runtime_checkable
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

    # Ordered by docs.
    # Files.

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

    async def fetch_file_from_bucket(self, bucket: str, /, id: int) -> files.URL:
        ...

    async def fetch_attachment(self, id: int) -> files.URL:
        ...

    async def fetch_file_data_from_bucket(self, bucket: str, /, id: int) -> models.FileData:
        ...

    async def fetch_attachment_data(self, id: int) -> models.FileData:
        ...

    async def fetch_static_file(self, name: str) -> files.URL:
        ...

    # Instance.

    async def get_instance_info(self, rate_limits: bool = False) -> models.InstanceInfo:
        ...

    # Messaging.

    async def send_message(self, content: str) -> models.Message:
        ...

    # Sessions

    async def create_session(
        self, *, identifier: str, password: str, platform: str = ..., client: str = ...
    ) -> typing.Tuple[str, models.Session]:
        ...

    async def delete_session(self, *, id: int) -> None:
        ...

    async def get_sessions(self) -> typing.Sequence[models.Session]:
        ...

    # Users

    async def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
    ) -> models.User:
        ...

    async def delete_user(self, password: str) -> None:
        ...

    async def get_self(self) -> models.User:
        ...

    async def get_user(self, identifier: typing.Union[int, str], /) -> models.User:
        ...

    async def update_profile(
        self,
        *,
        display_name: typing.Optional[str] = None,
        status: typing.Optional[str] = None,
        status_type: typing.Optional[models.StatusType] = None,
        bio: typing.Optional[str] = None,
        avatar: typing.Optional[int] = None,
        banner: typing.Optional[int] = None,
    ) -> models.User:
        ...

    async def update_user(
        self,
        *,
        password: str,
        username: typing.Optional[str] = None,
        email: typing.Optional[str] = None,
        new_password: typing.Optional[str] = None,
    ) -> models.User:
        ...

    async def verify_user(self, *, code: int) -> None:
        ...
