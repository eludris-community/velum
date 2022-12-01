# TODO: fancy stuff when ratelimits and url params become a thing

from __future__ import annotations

import typing

import attr

__all__: typing.Sequence[str] = (
    "Route",
    "CompiledRoute",
    "GET",
    "POST",
    "GET_INFO",
    "POST_MESSAGE",
)


@attr.define(hash=True, weakref_slot=False)
class Route:

    method: str = attr.field()

    path_template: str = attr.field()

    def compile(self, **url_params: typing.Any) -> CompiledRoute:
        return CompiledRoute(self, self.path_template.format_map(url_params))

    def __str__(self) -> str:
        return self.path_template


@attr.define(hash=True, weakref_slot=False)
class CompiledRoute:

    route: Route = attr.field()

    compiled_path: str = attr.field()

    @property
    def method(self) -> str:
        return self.route.method

    def create_url(self, base_url: str) -> str:
        return base_url + self.compiled_path

    def __str__(self) -> str:
        return f"{self.method} {self.compiled_path}"


GET: typing.Final[str] = "GET"
POST: typing.Final[str] = "POST"

GET_INFO = Route(GET, "/")
POST_MESSAGE = Route(POST, "/messages")
GET_RATELIMITS = Route(GET, "/ratelimits")
