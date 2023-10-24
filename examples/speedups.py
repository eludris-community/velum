# Velum can be installed as `pip install velum[speedups]`.
# Doing so installs a couple extra dependencies that can considerably improve
# the performance of your client. This example will go over what to do to actually
# opt into all the speedup features.

import asyncio
import os

import uvloop

import velum

# First and foremost, we will use orjson instead of the default json library.
# This can easily achieved with a helper function provided by Velum.
# Note that this will raise an `ImportError` if orjson is not installed.

velum.set_json_impl(impl=velum.JSONImpl.ORJSON)


# Next, and probably the most impactful, is uvloop. This only works on
# Unix, and is therefore not installed with speedups if you are on a
# different platform.

uvloop.install()


# Finally, we instantiate and run a client as per usual.

client = velum.GatewayClient(token=os.environ["TOKEN"])


@client.listen()
async def on_message(event: velum.MessageCreateEvent):
    if event.author == client.gateway.user:
        return

    match event.content:  # noqa: E999
        case "!speed":
            await client.rest.send_message("I am the fast.")

        case _:
            return


asyncio.run(client.start())
