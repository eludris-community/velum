import asyncio
import os

import velum

VELUM_URL = "https://github.com/Chromosomologist/velum"


# By default, the client will connect to the default eludris instance at
#
# GATEWAY:  wss://ws.eludris.gay/
# REST:     https://api.eludris.gay/
#
# Custom gateway and rest urls, pointing to some other eludris instance,
# can be set though the client constructor's `gateway_url` and `rest_url`
# arguments.
#
# The token can be obtained by creating a session with an existing user.
# To create a session with velum, run `python -m velum <username> <password> [-U <url>]`
# or `py`, `python3` or whichever variation works.
#
# `url` is optional, and should be set to `https://api.eludris.gay/next` if you want to
# use the above instance, but with the `next` branch as users is not in main yet.

__import__("logging").getLogger("velum").setLevel("DEBUG")
bot = velum.GatewayClient(
    token=os.environ["TOKEN"],
    rest_url="https://api.eludris.gay/next",
    gateway_url="https://ws.eludris.gay/next/",
    cdn_url="https://cdn.eludris.gay/next",
)


# Register a listener for messages.
# The event type can be provided to the listener, or it can be automatically
# resolved from the annotation of the first function parameter.


@bot.listen()
async def on_message(event: velum.MessageCreateEvent):
    if event.author == bot.gateway.user:
        return

    match event.content:  # noqa: E999
        case "!pog":
            await bot.rest.send_message("Pog!")

        case "!velum":
            await bot.rest.send_message(VELUM_URL)

        case _:
            return


# Start the client!

asyncio.run(bot.start())
