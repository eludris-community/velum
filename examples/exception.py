import asyncio
import typing

import velum

# It may be desirable to catch any exceptions that are raised in a listener.
# To this end, one can create a second listener listing for `ExceptionEvent`s,
# which is an event type that is automatically dispatched when any normal
# event raises an exception.

bot = velum.GatewayBot()


@bot.listen()
async def broken_listener(event: velum.MessageCreateEvent) -> None:
    # For the sake of illustration, we immediately raise an exception.
    if event.author != "Velum":
        raise Exception("Oops!")


# We then make a listener for `ExceptionEvent`s. This event contains information
# on the event that failed, the callback that raised the exception, the raised
# exception, etc.


@bot.listen()
async def exception_handler(event: velum.ExceptionEvent[typing.Any]) -> None:
    if isinstance(event.failed_event, velum.MessageCreateEvent):
        await bot.rest.send_message(
            "Velum",
            f"Listener {event.failed_callback.__name__} raised an exception: {event.exception!r}",
        )


# Finally, the bot can be started as per usual.

asyncio.run(bot.start())
