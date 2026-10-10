"""Signing in to Resland's Auth0 tenant from a terminal.

`resland-mcp login` runs the OAuth device authorization flow: it prints a URL
and a code, you approve in the browser, and the access + refresh tokens land
in a 0600 file under ~/.config/resland-mcp. The server then refreshes the
access token on its own until the refresh token stops working.
"""

import asyncio
import json
import os
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from .config import Settings

DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
# offline_access asks for a refresh token, so one login lasts.
SCOPE = "openid profile offline_access"
# Refresh this long before expiry so a token can't lapse mid-request.
EXPIRY_LEEWAY_SECONDS = 60
LOGIN_HINT = "Run `resland-mcp login` in a terminal to sign in."


class AuthError(ToolError):
    """A login problem worded for the person (and the model) reading it."""


class NotLoggedIn(AuthError):
    pass


@dataclass
class Credentials:
    access_token: str
    # Epoch seconds.
    expires_at: float
    refresh_token: str | None = None


@dataclass
class DeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    # Seconds between polls, and until the code is no good.
    interval: int
    expires_in: int


class TokenStore:
    """The credentials file — readable by its owner only."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Credentials | None:
        try:
            return Credentials(**json.loads(self.path.read_text()))
        except (OSError, ValueError, TypeError):
            # Missing or unreadable: either way there's no usable login.
            return None

    def save(self, creds: Credentials) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        # Created 0600 rather than chmod-ed after, so the tokens are never
        # readable by anyone else, even briefly. O_EXCL after clearing a
        # leftover tmp file means the mode always comes from this open.
        tmp.unlink(missing_ok=True)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(asdict(creds), f)
        os.replace(tmp, self.path)

    def clear(self) -> bool:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return False
        return True


class Auth0:
    def __init__(
        self,
        settings: Settings,
        http: httpx2.AsyncClient,
        *,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        self.settings = settings
        self.http = http
        self.clock = clock
        self.sleep = sleep

    def _url(self, path: str) -> str:
        return f"https://{self.settings.auth0_domain}{path}"

    async def _post(self, path: str, data: dict[str, str]) -> httpx2.Response:
        try:
            return await self.http.post(self._url(path), data=data)
        except httpx2.RequestError as e:
            raise AuthError(
                f"Couldn't reach Auth0 at {self.settings.auth0_domain}: {e}"
            ) from e

    def _credentials(
        self, payload: dict, refresh_token: str | None = None
    ) -> Credentials:
        return Credentials(
            access_token=payload["access_token"],
            expires_at=self.clock() + float(payload.get("expires_in", 0)),
            refresh_token=payload.get("refresh_token") or refresh_token,
        )

    async def start_device_login(self) -> DeviceCode:
        resp = await self._post(
            "/oauth/device/code",
            {
                "client_id": self.settings.auth0_client_id,
                "audience": self.settings.auth0_audience,
                "scope": SCOPE,
            },
        )
        payload = _json(resp)
        if resp.is_error:
            raise AuthError(f"Auth0 refused the login: {_oauth_error(payload, resp)}")
        return DeviceCode(
            device_code=payload["device_code"],
            user_code=payload["user_code"],
            verification_uri=payload["verification_uri"],
            verification_uri_complete=payload.get("verification_uri_complete"),
            interval=int(payload.get("interval", 5)),
            expires_in=int(payload.get("expires_in", 900)),
        )

    async def finish_device_login(self, code: DeviceCode) -> Credentials:
        """Poll until the code is approved in the browser (RFC 8628 §3.4-3.5)."""
        deadline = self.clock() + code.expires_in
        interval = code.interval
        while True:
            await self.sleep(interval)
            if self.clock() > deadline:
                raise AuthError(
                    "The login code expired before it was approved. Try again."
                )
            resp = await self._post(
                "/oauth/token",
                {
                    "grant_type": DEVICE_GRANT,
                    "device_code": code.device_code,
                    "client_id": self.settings.auth0_client_id,
                },
            )
            payload = _json(resp)
            if not resp.is_error:
                return self._credentials(payload)
            error = payload.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            raise AuthError(f"Login failed: {_oauth_error(payload, resp)}")

    async def refresh(self, refresh_token: str) -> Credentials:
        resp = await self._post(
            "/oauth/token",
            {
                "grant_type": "refresh_token",
                "client_id": self.settings.auth0_client_id,
                "refresh_token": refresh_token,
            },
        )
        payload = _json(resp)
        if resp.is_error:
            raise NotLoggedIn(
                f"Your Resland login has expired ({_oauth_error(payload, resp)}). {LOGIN_HINT}"
            )
        # Without rotation Auth0 sends no new refresh token: keep the old one.
        return self._credentials(payload, refresh_token)


class TokenProvider:
    """Hands out a live access token, refreshing (and re-saving) as needed."""

    def __init__(
        self, auth0: Auth0, store: TokenStore, *, clock: Callable[[], float] = time.time
    ):
        self.auth0 = auth0
        self.store = store
        self.clock = clock
        self._lock = asyncio.Lock()

    async def token(self) -> str:
        # One refresh at a time: parallel tool calls would otherwise each
        # spend the refresh token, and with rotation only the first succeeds.
        async with self._lock:
            creds = self.store.load()
            if creds is None:
                raise NotLoggedIn(f"You're not signed in to Resland. {LOGIN_HINT}")
            if creds.expires_at - EXPIRY_LEEWAY_SECONDS > self.clock():
                return creds.access_token
            if not creds.refresh_token:
                raise NotLoggedIn(f"Your Resland login has expired. {LOGIN_HINT}")
            creds = await self.auth0.refresh(creds.refresh_token)
            self.store.save(creds)
            return creds.access_token


def _json(resp: httpx2.Response) -> dict:
    try:
        payload = resp.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _oauth_error(payload: dict, resp: httpx2.Response) -> str:
    error = payload.get("error") or f"HTTP {resp.status_code}"
    description = payload.get("error_description")
    return f"{error}: {description}" if description and description != error else error
