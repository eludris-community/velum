import asyncio

import velum

bot = velum.GatewayBot()


def file_attachment() -> velum.Resource[velum.AsyncReader]:
    return velum.File("path/to/some/image.png")


def url_attachment() -> velum.Resource:
    return velum.URL("https://cdn.eludris.gay/369504572271420716171591703")


def raw_attachment() -> velum.Resource:
    import contextlib
    import io

    sio = io.StringIO()

    with contextlib.redirect_stdout(sio):
        print("ayy lmao")

    sio.seek(0)
    return velum.Bytes(sio, "test.txt")


async def main():
    async with bot.rest as rest_client:
        resp = await rest_client.upload_attachment(raw_attachment(), spoiler=True)

    print(resp)


asyncio.run(main())
