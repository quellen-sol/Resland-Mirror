"""Minimal Auth0 Management API client: read and delete one user.

Uses a client-credentials (machine-to-machine) application authorized for the
tenant's Management API with `read:users` and `delete:users`. The token is
cached in-process until shortly before it expires — Auth0's free plan caps how
many machine-to-machine tokens a tenant can mint a month.
"""

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
import jwt

from ..env_vars import (
    AUTH0_DOMAIN,
    AUTH0_MGMT_CLIENT_ID,
    AUTH0_MGMT_CLIENT_SECRET,
    AUTH0_MGMT_DOMAIN,
)

TIMEOUT_SECONDS = 10.0
# Refresh a cached token this long before Auth0 says it expires.
TOKEN_REFRESH_MARGIN_S = 300.0

# The parts of the Auth0 profile an export includes. Tokens, app_metadata and
# user_metadata stay out: they're credentials or our own bookkeeping.
PROFILE_FIELDS = (
    "user_id",
    "email",
    "email_verified",
    "name",
    "given_name",
    "family_name",
    "nickname",
    "picture",
    "locale",
    "created_at",
    "updated_at",
    "last_login",
    "last_ip",
    "logins_count",
)
IDENTITY_FIELDS = ("provider", "connection", "isSocial")


class Auth0ManagementError(Exception):
    """Auth0 didn't do what was asked (network failure, 4xx/5xx)."""


class Auth0NotReady(Auth0ManagementError):
    """The Management API can't be used as configured: credentials unset or
    rejected, or the token lacks a scope we need."""


@dataclass(frozen=True)
class _Token:
    value: str
    scopes: frozenset[str]
    expires_at: float  # time.monotonic()


# (domain, client_id) -> token. Process-wide, so every client built from the
# same env shares one token until it's near expiry.
_TOKENS: dict[tuple[str, str], _Token] = {}


def clear_token_cache() -> None:
    """Forget cached tokens (tests; a rotated secret)."""
    _TOKENS.clear()


def _granted_scopes(body: dict, token: str) -> frozenset[str]:
    """Scopes from the token response, or from the token itself when the
    response leaves them out. Only read, never trusted for auth: Auth0
    enforces them on every call; this just lets us fail before erasing."""
    scope = body.get("scope")
    if not isinstance(scope, str):
        try:
            claims = jwt.decode(token, options={"verify_signature": False})
        except jwt.PyJWTError:
            claims = {}
        scope = claims.get("scope") or ""
    return frozenset(scope.split())


class Auth0Management:
    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.domain and self.client_id and self.client_secret)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=f"https://{self.domain}",
            timeout=TIMEOUT_SECONDS,
            transport=self._transport,
        )

    @property
    def _cache_key(self) -> tuple[str, str]:
        return (self.domain, self.client_id)

    async def _token(self, client: httpx.AsyncClient) -> _Token:
        cached = _TOKENS.get(self._cache_key)
        if cached and time.monotonic() < cached.expires_at - TOKEN_REFRESH_MARGIN_S:
            return cached
        res = await client.post(
            "/oauth/token",
            json={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": f"https://{self.domain}/api/v2/",
            },
        )
        if res.status_code != 200:
            raise Auth0ManagementError(
                f"token request failed: {res.status_code} {res.text[:200]}"
            )
        try:
            body = res.json()
            value = body["access_token"]
        except (ValueError, KeyError, TypeError) as e:
            raise Auth0ManagementError("token response had no access_token") from e
        token = _Token(
            value=value,
            scopes=_granted_scopes(body, value),
            expires_at=time.monotonic() + float(body.get("expires_in") or 0),
        )
        _TOKENS[self._cache_key] = token
        return token

    async def _user_request(self, method: str, user_id: str) -> httpx.Response:
        try:
            async with self._client() as client:
                token = await self._token(client)
                # Auth0 ids contain `|` — it must be percent-encoded.
                res = await client.request(
                    method,
                    f"/api/v2/users/{quote(user_id, safe='')}",
                    headers={"Authorization": f"Bearer {token.value}"},
                )
        except httpx.HTTPError as e:
            raise Auth0ManagementError(f"{method} user failed: {e!r}") from e
        if res.status_code == 401:
            # Revoked or rotated: don't keep handing it out.
            _TOKENS.pop(self._cache_key, None)
        return res

    async def ensure_scopes(self, *scopes: str) -> None:
        """Fetch (or reuse) a token and check it carries `scopes`. Raises
        Auth0NotReady otherwise — call it before starting anything that
        needs Auth0 to finish."""
        if not self.configured:
            raise Auth0NotReady("Management API credentials aren't set")
        try:
            async with self._client() as client:
                token = await self._token(client)
        except httpx.HTTPError as e:
            raise Auth0NotReady(f"token request failed: {e!r}") from e
        except Auth0ManagementError as e:
            raise Auth0NotReady(str(e)) from e
        missing = set(scopes) - token.scopes
        if missing:
            raise Auth0NotReady(f"token lacks {' '.join(sorted(missing))}")

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """The user's Auth0 profile, trimmed to PROFILE_FIELDS; None when
        Auth0 has no such user."""
        res = await self._user_request("GET", user_id)
        if res.status_code == 404:
            return None
        if res.status_code != 200:
            raise Auth0ManagementError(f"GET user: {res.status_code} {res.text[:200]}")
        try:
            body = res.json()
        except ValueError as e:
            raise Auth0ManagementError("GET user: response wasn't JSON") from e
        profile = {k: body[k] for k in PROFILE_FIELDS if k in body}
        if "identities" in body:
            profile["identities"] = [
                {k: ident[k] for k in IDENTITY_FIELDS if k in ident}
                for ident in body["identities"]
            ]
        return profile

    async def delete_user(self, user_id: str) -> None:
        """Delete the Auth0 user. An already-deleted user counts as done, so
        a retried account deletion can finish."""
        res = await self._user_request("DELETE", user_id)
        if res.status_code not in (200, 204, 404):
            raise Auth0ManagementError(
                f"DELETE user: {res.status_code} {res.text[:200]}"
            )


def auth0_management() -> Auth0Management:
    """Client from env. AUTH0_MGMT_DOMAIN overrides AUTH0_DOMAIN for tenants
    whose login runs on a custom domain — the Management API only answers on
    the canonical `<tenant>.<region>.auth0.com` domain."""
    return Auth0Management(
        domain=AUTH0_MGMT_DOMAIN or AUTH0_DOMAIN,
        client_id=AUTH0_MGMT_CLIENT_ID,
        client_secret=AUTH0_MGMT_CLIENT_SECRET,
    )
