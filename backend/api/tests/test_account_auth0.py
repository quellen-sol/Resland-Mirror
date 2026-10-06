"""account.auth0_mgmt — client-credentials token, then one Management API
call. HTTP is served by an httpx.MockTransport; nothing leaves the process.

Run: .venv/bin/python -m unittest backend.api.tests.test_account_auth0 -v
"""

import json
import unittest
from unittest import mock

import httpx

from api.account import auth0_mgmt
from api.account.auth0_mgmt import Auth0Management, Auth0ManagementError

DOMAIN = "resland.us.auth0.com"
USER = "google-oauth2|1234"


class _Auth0Server:
    """Scripted Auth0: answers /oauth/token, then `user_status`/`user_body`
    for the /api/v2/users call. Records every request."""

    def __init__(self, user_status=204, user_body=None, token_status=200):
        self.user_status = user_status
        self.user_body = user_body
        self.token_status = token_status
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/oauth/token":
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "denied"})
            return httpx.Response(
                200, json={"access_token": "mgmt-token", "token_type": "Bearer"}
            )
        if self.user_body is not None:
            return httpx.Response(self.user_status, json=self.user_body)
        return httpx.Response(self.user_status)

    def client(self) -> Auth0Management:
        return Auth0Management(
            DOMAIN, "cid", "secret", transport=httpx.MockTransport(self)
        )


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


class DeleteUser(unittest.IsolatedAsyncioTestCase):
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
        self.assertEqual(delete_req.headers["authorization"], "Bearer mgmt-token")

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


class GetUser(unittest.IsolatedAsyncioTestCase):
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


if __name__ == "__main__":
    unittest.main()
