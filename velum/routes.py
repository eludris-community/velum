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
    "PATCH",
    "DELETE",
    "GET_INFO",
    "CREATE_MESSAGE",
)


@attr.define(hash=True, weakref_slot=False)
class Route:
    method: str = attr.field()

    destination: str = attr.field()

    path_template: str = attr.field()

    requires_authentication: typing.Optional[bool] = attr.field(default=None)

    def compile(self, **url_params: typing.Any) -> CompiledRoute:
        return CompiledRoute(
            self, self.path_template.format_map(url_params), self.requires_authentication
        )

    def __str__(self) -> str:
        return self.path_template


@attr.define(hash=True, weakref_slot=False)
class CompiledRoute:
    route: Route = attr.field()

    compiled_path: str = attr.field()

    requires_authentication: typing.Optional[bool] = attr.field(default=None)

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
PATCH: typing.Final[str] = "PATCH"
DELETE: typing.Final[str] = "DELETE"

OPRISH: typing.Final[str] = sys.intern("OPRISH")
EFFIS: typing.Final[str] = sys.intern("EFFIS")


# Files.

POST_ATTACHMENT = Route(POST, EFFIS, "/")
GET_ATTACHMENT = Route(GET, EFFIS, "/{id}")
GET_ATTACHMENT_INFO = Route(GET, EFFIS, "/{id}/data")
POST_FILE = Route(POST, EFFIS, "/{bucket}")
GET_FILE = Route(GET, EFFIS, "/{bucket}/{id}")
GET_FILE_INFO = Route(GET, EFFIS, "/{bucket}/{id}/data")
GET_STATIC_FILE = Route(GET, EFFIS, "/static/{name}")

# Instance.

GET_INFO = Route(GET, OPRISH, "/")

# Messaging.

CREATE_MESSAGE = Route(POST, OPRISH, "/messages", True)
