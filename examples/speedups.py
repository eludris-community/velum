# Velum can be installed as `pip install velum[speedups]`.
# Doing so installs a couple extra dependencies that can considerably improve
# the performance of your bot. This example will go over what to do to actually
# opt into all the speedup features.

import asyncio

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


# Finally, we instantiate and run a bot as per usual.

bot = velum.GatewayBot()


@bot.listen()
async def on_message(event: velum.MessageCreateEvent):
    if event.author == "velum[speedups]":
        return

    match event.content:
        case "!speed":
            await bot.rest.send_message("velum[speedups]", "I am the fast.")

        case _:
            return


asyncio.run(bot.start())
