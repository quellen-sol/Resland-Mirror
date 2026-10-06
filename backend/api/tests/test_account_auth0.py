"""account.auth0_mgmt — client-credentials token, then one Management API
call. HTTP is served by an httpx.MockTransport; nothing leaves the process.

Run: .venv/bin/python -m unittest backend.api.tests.test_account_auth0 -v
"""

import json
import unittest
from unittest import mock

import httpx

from api.account import auth0_mgmt
from api.account.auth0_mgmt import (
    Auth0Management,
    Auth0ManagementError,
    Auth0NotReady,
)

DOMAIN = "resland.us.auth0.com"
USER = "google-oauth2|1234"


class _Auth0Server:
    """Scripted Auth0: answers /oauth/token, then `user_status`/`user_body`
    for the /api/v2/users call. Records every request."""

    def __init__(
        self,
        user_status=204,
        user_body=None,
        token_status=200,
        scope="read:users delete:users",
        expires_in=86400,
    ):
        self.user_status = user_status
        self.user_body = user_body
        self.token_status = token_status
        self.scope = scope
        self.expires_in = expires_in
        self.requests: list[httpx.Request] = []
        self.tokens_issued = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/oauth/token":
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "denied"})
            self.tokens_issued += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"mgmt-token-{self.tokens_issued}",
                    "token_type": "Bearer",
                    "scope": self.scope,
                    "expires_in": self.expires_in,
                },
            )
        if self.user_body is not None:
            return httpx.Response(self.user_status, json=self.user_body)
        return httpx.Response(self.user_status)

    def client(self) -> Auth0Management:
        return Auth0Management(
            DOMAIN, "cid", "secret", transport=httpx.MockTransport(self)
        )


class _FreshCache(unittest.IsolatedAsyncioTestCase):
    """Tokens are cached per process — every test starts without one."""

    def setUp(self):
        auth0_mgmt.clear_token_cache()
        self.addCleanup(auth0_mgmt.clear_token_cache)


class Configured(unittest.TestCase):
    def test_needs_domain_and_credentials(self):
        self.assertTrue(Auth0Management(DOMAIN, "cid", "secret").configured)
        self.assertFalse(Auth0Management(DOMAIN, "", "secret").configured)
        self.assertFalse(Auth0Management(DOMAIN, "cid", "").configured)
        self.assertFalse(Auth0Management("", "cid", "secret").configured)

    def test_env_domain_override(self):
        with mock.patch.multiple(
            auth0_mgmt,
            AUTH0_DOMAIN="login.resland.org",
            AUTH0_MGMT_DOMAIN="resland.us.auth0.com",
            AUTH0_MGMT_CLIENT_ID="cid",
            AUTH0_MGMT_CLIENT_SECRET="s",
        ):
            self.assertEqual(auth0_mgmt.auth0_management().domain, DOMAIN)
        with mock.patch.multiple(
            auth0_mgmt, AUTH0_DOMAIN="login.resland.org", AUTH0_MGMT_DOMAIN=""
        ):
            self.assertEqual(auth0_mgmt.auth0_management().domain, "login.resland.org")


class DeleteUser(_FreshCache):
    async def test_fetches_a_token_then_deletes(self):
        server = _Auth0Server(user_status=204)
        await server.client().delete_user(USER)

        token_req, delete_req = server.requests
        self.assertEqual(str(token_req.url), f"https://{DOMAIN}/oauth/token")
        self.assertEqual(
            json.loads(token_req.content),
            {
                "grant_type": "client_credentials",
                "client_id": "cid",
                "client_secret": "secret",
                "audience": f"https://{DOMAIN}/api/v2/",
            },
        )
        self.assertEqual(delete_req.method, "DELETE")
        # The `|` in an Auth0 id must be percent-encoded in the path.
        self.assertEqual(
            delete_req.url.raw_path.decode(), "/api/v2/users/google-oauth2%7C1234"
        )
        self.assertEqual(delete_req.headers["authorization"], "Bearer mgmt-token-1")

    async def test_already_deleted_counts_as_done(self):
        await _Auth0Server(user_status=404).client().delete_user(USER)

    async def test_server_error_raises(self):
        with self.assertRaises(Auth0ManagementError):
            await _Auth0Server(user_status=500).client().delete_user(USER)

    async def test_missing_scope_raises(self):
        with self.assertRaises(Auth0ManagementError):
            await _Auth0Server(user_status=403).client().delete_user(USER)

    async def test_token_failure_raises(self):
        server = _Auth0Server(token_status=401)
        with self.assertRaises(Auth0ManagementError):
            await server.client().delete_user(USER)
        self.assertEqual(len(server.requests), 1)  # never reached the delete

    async def test_network_failure_raises(self):
        def unreachable(request):
            raise httpx.ConnectError("down", request=request)

        client = Auth0Management(
            DOMAIN, "cid", "secret", transport=httpx.MockTransport(unreachable)
        )
        with self.assertRaises(Auth0ManagementError):
            await client.delete_user(USER)


class GetUser(_FreshCache):
    async def test_trims_the_profile(self):
        body = {
            "user_id": USER,
            "email": "jane@example.com",
            "name": "Jane",
            "last_ip": "203.0.113.9",
            "app_metadata": {"internal": True},
            "identities": [
                {
                    "provider": "google-oauth2",
                    "connection": "google-oauth2",
                    "isSocial": True,
                    "access_token": "secret-idp-token",
                    "user_id": "1234",
                }
            ],
        }
        server = _Auth0Server(user_status=200, user_body=body)
        profile = await server.client().get_user(USER)
        self.assertEqual(profile["email"], "jane@example.com")
        self.assertEqual(profile["last_ip"], "203.0.113.9")
        self.assertNotIn("app_metadata", profile)
        self.assertEqual(
            profile["identities"],
            [
                {
                    "provider": "google-oauth2",
                    "connection": "google-oauth2",
                    "isSocial": True,
                }
            ],
        )
        self.assertEqual(server.requests[1].method, "GET")

    async def test_unknown_user_is_none(self):
        server = _Auth0Server(user_status=404, user_body={"error": "nope"})
        self.assertIsNone(await server.client().get_user(USER))

    async def test_error_raises(self):
        server = _Auth0Server(user_status=500, user_body={"error": "boom"})
        with self.assertRaises(Auth0ManagementError):
            await server.client().get_user(USER)

    async def test_non_json_success_raises_the_client_error(self):
        # A proxy answering 200 with HTML must degrade the export (no login
        # profile), not crash it.
        def html(request):
            if request.url.path == "/oauth/token":
                return httpx.Response(200, json={"access_token": "t"})
            return httpx.Response(200, text="<html>hi</html>")

        client = Auth0Management(
            DOMAIN, "cid", "secret", transport=httpx.MockTransport(html)
        )
        with self.assertRaises(Auth0ManagementError):
            await client.get_user(USER)


class EnsureScopes(_FreshCache):
    """The deletion's pre-flight: a bad secret, a missing scope or a wrong
    domain must show up before anything is erased, not after."""

    async def test_token_with_the_scopes_passes(self):
        await _Auth0Server().client().ensure_scopes("delete:users")

    async def test_missing_scope_is_not_ready(self):
        server = _Auth0Server(scope="read:users")
        with self.assertRaises(Auth0NotReady):
            await server.client().ensure_scopes("delete:users")

    async def test_rejected_credentials_are_not_ready(self):
        with self.assertRaises(Auth0NotReady):
            await _Auth0Server(token_status=401).client().ensure_scopes("delete:users")

    async def test_unreachable_domain_is_not_ready(self):
        def unreachable(request):
            raise httpx.ConnectError("no such host", request=request)

        client = Auth0Management(
            DOMAIN, "cid", "secret", transport=httpx.MockTransport(unreachable)
        )
        with self.assertRaises(Auth0NotReady):
            await client.ensure_scopes("delete:users")

    async def test_unconfigured_is_not_ready(self):
        with self.assertRaises(Auth0NotReady):
            await Auth0Management(DOMAIN, "", "").ensure_scopes("delete:users")

    async def test_scopes_from_the_token_when_the_response_omits_them(self):
        import jwt as pyjwt

        token = pyjwt.encode({"scope": "delete:users"}, "k", algorithm="HS256")

        def handler(request):
            if request.url.path == "/oauth/token":
                return httpx.Response(
                    200, json={"access_token": token, "expires_in": 60}
                )
            return httpx.Response(204)

        client = Auth0Management(
            DOMAIN, "cid", "secret", transport=httpx.MockTransport(handler)
        )
        await client.ensure_scopes("delete:users")
        with self.assertRaises(Auth0NotReady):
            await client.ensure_scopes("read:users")


class TokenCache(_FreshCache):
    async def test_one_token_serves_many_calls_and_clients(self):
        server = _Auth0Server()
        await server.client().ensure_scopes("delete:users")
        await server.client().delete_user(USER)
        await server.client().delete_user("auth0|other")
        self.assertEqual(server.tokens_issued, 1)
        deletes = [r for r in server.requests if r.method == "DELETE"]
        self.assertEqual(
            {r.headers["authorization"] for r in deletes}, {"Bearer mgmt-token-1"}
        )

    async def test_token_near_expiry_is_refreshed(self):
        # Inside the refresh margin, a cached token isn't reused.
        server = _Auth0Server(expires_in=int(auth0_mgmt.TOKEN_REFRESH_MARGIN_S) - 1)
        await server.client().delete_user(USER)
        await server.client().delete_user(USER)
        self.assertEqual(server.tokens_issued, 2)

    async def test_rejected_token_is_dropped_from_the_cache(self):
        server = _Auth0Server(user_status=401)
        with self.assertRaises(Auth0ManagementError):
            await server.client().delete_user(USER)
        server.user_status = 204
        await server.client().delete_user(USER)
        self.assertEqual(server.tokens_issued, 2)


if __name__ == "__main__":
    unittest.main()
