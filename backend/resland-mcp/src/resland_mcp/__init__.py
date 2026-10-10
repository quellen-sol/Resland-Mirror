"""resland-mcp: Resland as an MCP server for Claude Code / Claude Desktop.

resland-mcp login    sign in (once) with Auth0's device flow
resland-mcp          serve over stdio (what the MCP client launches)
resland-mcp status   show who's signed in
resland-mcp logout   forget the saved login
"""

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from .api import ReslandApi
from .auth import Auth0, AuthError, TokenProvider, TokenStore
from .config import ConfigError, Settings
from .server import create_server


async def login(
    settings: Settings,
    store: TokenStore,
    http: httpx2.AsyncClient,
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> int:
    auth0 = Auth0(settings, http, sleep=sleep)
    try:
        code = await auth0.start_device_login()
        url = code.verification_uri_complete or code.verification_uri
        print(
            f"Open {url}\nand confirm the code {code.user_code} to sign in to Resland."
        )
        creds = await auth0.finish_device_login(code)
    except AuthError as e:
        print(f"resland-mcp: {e}", file=sys.stderr)
        return 1
    store.save(creds)
    print(f"Signed in. The login is saved in {store.path}.")
    return 0


async def status(
    settings: Settings, store: TokenStore, http: httpx2.AsyncClient
) -> int:
    api = ReslandApi(
        settings.api_url, TokenProvider(Auth0(settings, http), store), http
    )
    try:
        profile = await api.get_profile()
    except ToolError as e:
        print(f"resland-mcp: {e}", file=sys.stderr)
        return 1
    who = profile.get("full_name") or profile.get("email") or "your account"
    print(f"Signed in as {who} on {settings.api_url}.")
    return 0


def serve(settings: Settings, store: TokenStore) -> None:
    # stdout is the MCP channel from here on; anything human goes to stderr.
    http = httpx2.AsyncClient()
    api = ReslandApi(
        settings.api_url, TokenProvider(Auth0(settings, http), store), http
    )
    create_server(api, settings).run("stdio")


async def _with_http(run: Callable[[httpx2.AsyncClient], Awaitable[int]]) -> int:
    async with httpx2.AsyncClient() as http:
        return await run(http)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="resland-mcp",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        choices=["serve", "login", "status", "logout"],
    )
    args = parser.parse_args(argv)
    try:
        settings = Settings.from_env()
    except ConfigError as e:
        print(f"resland-mcp: {e}", file=sys.stderr)
        return 2
    store = TokenStore(settings.credentials_path)

    match args.command:
        case "login":
            return asyncio.run(_with_http(lambda http: login(settings, store, http)))
        case "status":
            return asyncio.run(_with_http(lambda http: status(settings, store, http)))
        case "logout":
            print("Signed out." if store.clear() else "You weren't signed in.")
            return 0
        case _:
            serve(settings, store)
            return 0
