"""Minimal Auth0 Management API client: read and delete one user.

Uses a client-credentials (machine-to-machine) application authorized for the
tenant's Management API with `read:users` and `delete:users`. A fresh token is
fetched per call — these are rare, user-initiated operations, so caching a
24-hour token isn't worth the invalidation logic.
"""

from typing import Any

import httpx

from ..env_vars import (
    AUTH0_DOMAIN,
    AUTH0_MGMT_CLIENT_ID,
    AUTH0_MGMT_CLIENT_SECRET,
    AUTH0_MGMT_DOMAIN,
)

TIMEOUT_SECONDS = 10.0

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
        raise NotImplementedError

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """The user's Auth0 profile, trimmed to PROFILE_FIELDS; None when
        Auth0 has no such user."""
        raise NotImplementedError

    async def delete_user(self, user_id: str) -> None:
        """Delete the Auth0 user. An already-deleted user counts as done, so
        a retried account deletion can finish."""
        raise NotImplementedError


def auth0_management() -> Auth0Management:
    """Client from env. AUTH0_MGMT_DOMAIN overrides AUTH0_DOMAIN for tenants
    whose login runs on a custom domain — the Management API only answers on
    the canonical `<tenant>.<region>.auth0.com` domain."""
    return Auth0Management(
        domain=AUTH0_MGMT_DOMAIN or AUTH0_DOMAIN,
        client_id=AUTH0_MGMT_CLIENT_ID,
        client_secret=AUTH0_MGMT_CLIENT_SECRET,
    )
