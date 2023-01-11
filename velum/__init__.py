# TODO: Move meta info to its own file.

import typing

__title__: typing.Final[str] = "velum"
__author__: typing.Final[str] = "Chromosomologist"
__license__: typing.Final[str] = "MIT"
__copyright__: typing.Final[str] = "© 2022-present Chromosomologist"
__version__: typing.Final[str] = "0.2.0"


from velum import events as events
from velum import traits as traits
from velum.errors import *
from velum.events import Event as Event
from velum.events import ExceptionEvent as ExceptionEvent
from velum.events.connection_events import *
from velum.events.message_events import *
from velum.files import *
from velum.impl.client import GatewayClient as GatewayClient
from velum.internal.data_binding import JSONImpl as JSONImpl
from velum.internal.data_binding import set_json_impl as set_json_impl
from velum.models import Message as Message
