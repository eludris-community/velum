import contextlib
import types
import typing

import aiohttp
import typing_extensions

from velum import errors
from velum import files
from velum import models
from velum import routes
from velum.api import entity_factory_trait
from velum.api import rest_trait
from velum.impl import entity_factory as entity_factory_impl
from velum.internal import data_binding

__all__: typing.Sequence[str] = ("RESTClient",)


_REST_URL: typing.Final[str] = "https://api.eludris.gay/"
_CDN_URL: typing.Final[str] = "https://cdn.eludris.gay/"
_APPLICATION_JSON: typing.Final[str] = "application/json"


class RESTClient(rest_trait.RESTClient):
    __slots__ = (
        "_entity_factory",
        "_routes",
        "_token",
        "_session",
    )

    _session: aiohttp.ClientSession | None

    def __init__(
        self,
        *,
        cdn_url: str | None = None,
        rest_url: str | None = None,
        token: str | None = None,
        entity_factory: entity_factory_trait.EntityFactory | None = None,
    ) -> None:
        self._entity_factory = (
            entity_factory if entity_factory is not None else entity_factory_impl.EntityFactory()
        )
        self._routes = {
            routes.OPRISH: rest_url or _REST_URL,
            routes.EFFIS: cdn_url or _CDN_URL,
        }
        self._token = token
        self._session = None

    @property
    def is_alive(self) -> bool:
        return self._session is not None

    @property
    def entity_factory(self) -> entity_factory_trait.EntityFactory:
        return self._entity_factory

    def _assert_and_return_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            msg = "Cannot use an inactive RESTClient."
            raise RuntimeError(msg)

        return self._session

    def start(self) -> None:
        if self._session is not None:
            msg = "Cannot start an already running RESTClient."
            raise RuntimeError(msg)

        self._session = aiohttp.ClientSession(json_serialize=data_binding.dump_json)

    async def close(self) -> None:
        await self._assert_and_return_session().close()
        self._session = None

    async def __aenter__(self) -> typing_extensions.Self:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self.close()

    def _complete_route(self, route: routes.CompiledRoute) -> str:
        base_url = self._routes[route.destination]
        return route.create_url(base_url)

    async def _request(
        self,
        route: routes.CompiledRoute,
        *,
        json: typing.Any | None = None,
        form_builder: data_binding.FormBuilder | None = None,
        query: typing.Mapping[str, str] | None = None,
    ):
        url = self._complete_route(route)
        headers: dict[str, str] = {}

        if route.requires_authentication is not None:
            # Does not require authentication, but is preferred (higher rate limit).
            if not route.requires_authentication and self._token is not None:
                headers["Authorization"] = self._token
            elif route.requires_authentication:
                if self._token is None:
                    msg = "Cannot use an authenticated route without a token."
                    raise errors.HTTPError(msg)

                headers["Authorization"] = self._token

        stack = contextlib.AsyncExitStack()
        async with stack:
            form = await form_builder.build(stack) if form_builder else None

            response = await self._assert_and_return_session().request(
                route.method,
                url,
                params=query,
                json=json,
                data=form,
                headers=headers,
            )

        if 200 <= response.status < 300:
            content_type = response.content_type

            if content_type == _APPLICATION_JSON:
                return data_binding.load_json(await response.read())

            real_url = str(response.real_url)
            msg = f"Expected JSON response. (content_type={content_type!r}, real_url={real_url!r})"
            raise errors.HTTPError(msg)

        print(response.status, await response.read())

        msg = "get good lol"
        raise errors.HTTPError(msg)

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
        form = (
            data_binding.FormBuilder()
            .add_resource("file", files.ensure_resource(file))
            .add_field("spoiler", "true" if spoiler else "false", content_type="form-data")
        )

        response = await self._request(routes.POST_FILE.compile(bucket=bucket), form_builder=form)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_file_data(response)

    async def upload_attachment(
        self,
        attachment: files.ResourceLike,
        /,
        *,
        spoiler: bool = False,
    ) -> models.FileData:
        return await self.upload_to_bucket("attachments", attachment, spoiler=spoiler)

    async def fetch_file_from_bucket(self, bucket: str, /, id: int) -> files.URL:  # noqa: A002
        url = self._complete_route(routes.GET_FILE.compile(bucket=bucket, id=id))
        return files.URL(url)

    async def fetch_attachment(self, id: int) -> files.URL:  # noqa: A002
        return await self.fetch_file_from_bucket("attachments", id)

    async def fetch_file_data_from_bucket(
        self,
        bucket: str,
        /,
        id: int,  # noqa: A002
    ) -> models.FileData:
        route = routes.GET_FILE_INFO.compile(bucket=bucket, id=id)

        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_file_data(response)

    async def fetch_attachment_data(self, id: int) -> models.FileData:  # noqa: A002
        return await self.fetch_file_data_from_bucket("attachments", id)

    async def fetch_static_file(self, name: str) -> files.URL:
        url = self._complete_route(routes.GET_FILE_INFO.compile(name=name))
        return files.URL(url)

    # Instance.

    async def get_instance_info(self, *, rate_limits: bool = False) -> models.InstanceInfo:
        query = {"ratelimits": "1"} if rate_limits else {}
        response = await self._request(routes.GET_INFO.compile(), query=query)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_instance_info(response)

    # Messaging.

    async def send_message(self, content: str) -> models.Message:
        body = {"content": content}
        response = await self._request(routes.CREATE_MESSAGE.compile(), json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    # Sessions

    async def create_session(
        self,
        *,
        identifier: str,
        password: str,
        platform: str = "python",
        client: str = "velum",
    ) -> tuple[str, models.Session]:
        body = {
            "identifier": identifier,
            "password": password,
            "platform": platform,
            "client": client,
        }
        response = await self._request(routes.CREATE_SESSION.compile(), json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_session_created(response)

    async def delete_session(self, *, id: int) -> None:  # noqa: A002
        await self._request(routes.DELETE_SESSION.compile(id=id))

    async def get_sessions(self) -> typing.Sequence[models.Session]:
        response = await self._request(routes.GET_SESSIONS.compile())
        assert isinstance(response, list)
        return [
            self._entity_factory.deserialize_session(typing.cast(data_binding.JSONObject, session))
            for session in response
        ]

    # Users

    async def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
    ) -> models.User:
        body = {"username": username, "email": email, "password": password}
        response = await self._request(routes.CREATE_USER.compile(), json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_user(response)

    async def delete_user(self, password: str) -> None:
        body = {"password": password}
        await self._request(routes.DELETE_USER.compile(), json=body)

    async def get_self(self) -> models.User:
        response = await self._request(routes.GET_SELF.compile())
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_user(response)

    async def get_user(self, identifier: int | str, /) -> models.User:
        response = await self._request(routes.GET_USER.compile(identifier=identifier))
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_user(response)

    async def update_profile(
        self,
        *,
        display_name: str | None = None,
        status: str | None = None,
        status_type: models.StatusType | None = None,
        bio: str | None = None,
        avatar: int | None = None,
        banner: int | None = None,
    ) -> models.User:
        body = {
            "display_name": display_name,
            "status": status,
            "status_type": status_type,
            "bio": bio,
            "avatar": avatar,
            "banner": banner,
        }
        response = await self._request(routes.UPDATE_PROFILE.compile(), json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_user(response)

    async def update_user(
        self,
        *,
        password: str,
        username: str | None = None,
        email: str | None = None,
        new_password: str | None = None,
    ) -> models.User:
        body = {
            "password": password,
            "username": username,
            "email": email,
            "new_password": new_password,
        }
        response = await self._request(routes.UPDATE_USER.compile(), json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_user(response)

    async def verify_user(self, *, code: int) -> None:
        query = {"code": str(code)}
        await self._request(routes.VERIFY_USER.compile(), query=query)
