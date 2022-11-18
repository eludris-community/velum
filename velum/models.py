import attr
import typing


@attr.define(kw_only=True, weakref_slot=False)
class Message:

    content: str = attr.field()

    author: str = attr.field()


@attr.define(kw_only=True, weakref_slot=False)
class InstanceInfo:

    instance_name: str = attr.field()

    features: typing.Sequence[typing.Mapping[int, str]] = attr.field()
