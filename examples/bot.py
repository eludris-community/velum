import asyncio

import velum

SELF_AUTHOR = "Velum"  # Author name to use for messages sent to eludris.
VELUM_URL = "https://github.com/Chromosomologist/velum"


# By default, the client will connect to the default eludris instance at
#
# GATEWAY:  wss://eludris.tooty.xyz/ws/
# REST:     https://eludris.tooty.xyz/
#
# Custom gateway and rest urls, pointing to some other eludris instance,
# can be set though the client constructor's `gateway_url` and `rest_url`
# arguments.

bot = velum.GatewayClient()


# Register a listener for messages.
# The event type can be provided to the listener, or it can be automatically
# resolved from the annotation of the first function parameter.


@bot.listen()
async def on_message(event: velum.MessageCreateEvent):
    if event.author == SELF_AUTHOR:
        return

    match event.content:  # noqa: E999
        case "!pog":
            await bot.rest.send_message(SELF_AUTHOR, "Pog!")

        case "!velum":
            await bot.rest.send_message(SELF_AUTHOR, VELUM_URL)

        case _:
            return


# Start the client!

asyncio.run(bot.start())
