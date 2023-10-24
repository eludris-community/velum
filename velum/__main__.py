import argparse
import asyncio
import typing

import velum


async def create_password(username: str, password: str, url: typing.Optional[str]) -> str:
    async with velum.RESTClient(rest_url=url) as client:
        token, _ = await client.create_session(
            identifier=username,
            password=password,
        )
        return token


def main() -> None:
    parser = argparse.ArgumentParser(prog="velum")
    parser.add_argument("username-or-email")
    parser.add_argument("password")
    parser.add_argument("--url", "-U", default=None)

    args = parser.parse_args()

    identifier = getattr(args, "username-or-email")
    password = args.password
    url = args.url

    token = asyncio.run(create_password(identifier, password, url))
    print(token)


if __name__ == "__main__":
    main()
