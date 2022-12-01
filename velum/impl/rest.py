import types
import typing

import aiohttp
import typing_extensions

from velum import errors
from velum import models
from velum import routes
from velum.internal import data_binding
from velum.traits import entity_factory_trait
from velum.traits import rest_trait

__all__: typing.Sequence[str] = ("RESTClient",)


_REST_URL: typing.Final[str] = "https://eludris.tooty.xyz/"
_APPLICATION_JSON: typing.Final[str] = "application/json"


class RESTClient(rest_trait.RESTClient):

    __slots__ = (
        "_entity_factory",
        "_rest_url",
        "_session",
    )

    _session: typing.Optional[aiohttp.ClientSession]

    def __init__(
        self,
        *,
        rest_url: typing.Optional[str] = None,
        entity_factory: entity_factory_trait.EntityFactory,
    ):
        self._entity_factory = entity_factory
        self._rest_url = rest_url or _REST_URL
        self._session = None

    @property
    def is_alive(self) -> bool:
        return self._session is not None

    @property
    def entity_factory(self) -> entity_factory_trait.EntityFactory:
        return self._entity_factory

    def _assert_and_return_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("Cannot use an inactive RESTClient.")

        return self._session

    def start(self) -> None:
        if self._session is not None:
            raise RuntimeError("Cannot start an already running RESTClient.")

        self._session = aiohttp.ClientSession(json_serialize=data_binding.dump_json)

    async def close(self) -> None:
        await self._assert_and_return_session().close()

    async def __aenter__(self) -> typing_extensions.Self:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()

    async def _request(
        self,
        route: routes.CompiledRoute,
        *,
        query: typing.Optional[typing.Any] = None,
        json: typing.Optional[typing.Any] = None,
    ):
        url = route.create_url(self._rest_url)
        response = await self._assert_and_return_session().request(
            route.method,
            url,
            params=query,
            json=json,
        )

        if 200 <= response.status < 300:
            content_type = response.content_type

            if content_type == _APPLICATION_JSON:
                return data_binding.load_json(await response.read())

            real_url = str(response.real_url)
            raise errors.HTTPError(f"Expected JSON response. ({content_type=}, {real_url=})")

        raise errors.HTTPError("get good lol")

    @typing.overload
    async def send_message(self, *, message: models.Message) -> None:
        ...

    @typing.overload
    async def send_message(
        self,
        author: str,
        message: str,
    ) -> None:
        ...

    async def send_message(
        self,
        author: typing.Optional[str] = None,
        message: typing.Optional[models.Message | str] = None,
    ) -> None:
        if isinstance(message, models.Message):
            body = {
                "author": message.author,
                "content": message.content,
            }
        elif author is not None:
            body = {
                "author": author,
                "content": message,
            }
        else:
            raise TypeError(
                f"Please provide either a fully qualified {models.Message.__qualname__}, "
                "or an author and a message string."
            )

        await self._request(routes.POST_MESSAGE.compile(), json=body)

    async def get_instance_info(self) -> models.InstanceInfo:
        response = await self._request(routes.GET_INFO.compile())
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_instance_info(response)

    async def get_ratelimits(self) -> models.InstanceRatelimits:
        response = await self._request(routes.GET_RATELIMITS.compile())
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_ratelimits(response)
