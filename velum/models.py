import typing

import attr


@attr.define(kw_only=True, weakref_slot=False)
class Message:

    author: str = attr.field()

    content: str = attr.field()


@attr.define(kw_only=True, weakref_slot=False)
class InstanceInfo:

    instance_name: str = attr.field()

    features: typing.Sequence[typing.Mapping[int, str]] = attr.field()
