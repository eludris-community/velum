# Velum

Velum is an opinionated wrapper for the [Eludris](https://eludris.com) API written in Python, very much inspired by [Hikari](https://github.com/hikari-py/hikari).
It can handle connection, keep-alive, gateway events and interacting with Eludris' REST-api. If you are looking for a command handler to go with Velum, please take a look at [Velum-Sail](https://github.com/eludris-community/velum-sail).

Please keep in mind that this library is still in its infancy, and some much needed features such as documentation are coming in the near<sup>TM</sup> future.


# Installing

*Python 3.10 or higher is required.*

To install the library, currently the only option is to install it off of this very github page.
```
python3 -m pip install -U git+https://github.com/eludris-community/velum
```
To install optional dependencies to make everything run faster, Velum can also be installed through
```
python3 -m pip install -U -e git+https://github.com/eludris-community/velum.git#egg=velum[speedups]
```
This will install `aiohttp` with speedups extras, `uvloop`, and `orjson`. For more information, please see the [example on speedups](https://github.com/eludris-community/velum/blob/master/examples/speedups.py).


# Example

```py
import asyncio

import velum


client = velum.GatewayClient()


@client.listen()
async def listener(event: velum.MessageCreateEvent) -> None:
    await client.rest.send_message(f"{event.author} just sent a message!")


asyncio.run(client.start())
```
For more in-depth examples, please see the [examples directory](https://github.com/eludris-community/velum/tree/master/examples).
