# TODO: fancy stuff when ratelimits and url params become a thing

from __future__ import annotations

import sys
import typing

import attr

__all__: typing.Sequence[str] = (
    "Route",
    "CompiledRoute",
    "GET",
    "POST",
    "GET_INFO",
    "POST_MESSAGE",
    "POST_ATTACHMENT",
)


@attr.define(hash=True, weakref_slot=False)
class Route:

    method: str = attr.field()

    destination: str = attr.field()

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

    @property
    def destination(self) -> str:
        return self.route.destination

    def create_url(self, base_url: str) -> str:
        return base_url + self.compiled_path

    def __str__(self) -> str:
        return f"{self.method} {self.compiled_path}"


GET: typing.Final[str] = "GET"
POST: typing.Final[str] = "POST"

OPRISH: typing.Final[str] = sys.intern("OPRISH")
EFFIS: typing.Final[str] = sys.intern("EFFIS")


# Oprish routes.

GET_INFO = Route(GET, OPRISH, "/")
POST_MESSAGE = Route(POST, OPRISH, "/messages")


# Effis routes.

POST_ATTACHMENT = Route(POST, EFFIS, "/")
GET_ATTACHMENT = Route(GET, EFFIS, "/{id}")
GET_ATTACHMENT_INFO = Route(GET, EFFIS, "/{id}/data")
POST_FILE = Route(POST, EFFIS, "/{bucket}")
GET_FILE = Route(GET, EFFIS, "/{bucket}/{id}")
GET_FILE_INFO = Route(GET, EFFIS, "/{bucket}/{id}/data")
GET_STATIC_FILE = Route(GET, EFFIS, "/static/{name}")
