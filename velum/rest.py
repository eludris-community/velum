import types
import typing

import aiohttp
import typing_extensions

from velum import errors
from velum import models
from velum import routes

_REST_URL: typing.Final[str] = "https://eludris.tooty.xyz/"
_APPLICATION_JSON: typing.Final[str] = "application/json"


class RESTClient:
    def __init__(self, *, rest_url: typing.Optional[str] = None):
        # TODO: make unshittified
        self._session = aiohttp.ClientSession()
        self._rest_url = rest_url or _REST_URL

    async def close(self) -> None:
        await self._session.close()

    async def __aenter__(self) -> typing_extensions.Self:
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
        response = await self._session.request(
            route.method,
            url,
            params=query,
            json=json,
        )

        if 200 <= response.status < 300:
            content_type = response.content_type

            if content_type == _APPLICATION_JSON:
                # TODO: replace with centralised customisable json loader.
                return await response.json()

            real_url = str(response.real_url)
            raise errors.HTTPError(f"Expected JSON response. ({content_type=}, {real_url=})")

        raise errors.HTTPError("get good lol")

    @typing.overload
    async def send_message(self, message: models.Message) -> None:
        ...

    @typing.overload
    async def send_message(self, message: str, author: str) -> None:
        ...

    async def send_message(
        self,
        message: models.Message | str,
        author: typing.Optional[str] = None,
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
            raise RuntimeError("idk yet")

        await self._request(routes.POST_MESSAGE.compile(), json=body)

    async def get_instance_info(self) -> models.InstanceInfo:
        response = await self._request(routes.GET_INFO.compile())
        return models.InstanceInfo(**response)
