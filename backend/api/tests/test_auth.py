"""Auth tests — real RS256 JWTs through _verify_token (with JWKS patched to
a known key), the FastAPI dependency wrappers, and the site-admin check.

Run: .venv/bin/python -m unittest backend.api.tests.test_auth -v
     (from the repo root with the workspace venv)
"""

import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from api import auth, deps

DOMAIN = "test.auth0.local"
AUDIENCE = "resland-test"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUB = _KEY.public_key()


def _token(sub="auth0|u1", aud=AUDIENCE, iss=f"https://{DOMAIN}/", exp=None, key=None):
    claims = {
        "sub": sub,
        "aud": aud,
        "iss": iss,
        "iat": int(time.time()),
        "exp": exp if exp is not None else int(time.time()) + 600,
    }
    return pyjwt.encode(claims, key or _KEY, algorithm="RS256")


def _verify_patched():
    """Patch JWKS lookups to return our public key and pin the issuer/aud."""
    return (
        patch.object(auth, "AUTH0_DOMAIN", DOMAIN),
        patch.object(auth, "AUTH0_AUDIENCE", AUDIENCE),
        patch.object(
            auth._jwks,
            "get_signing_key_from_jwt",
            return_value=SimpleNamespace(key=_PUB),
        ),
    )


class VerifyToken(unittest.TestCase):
    def test_valid_token_returns_sub(self):
        p1, p2, p3 = _verify_patched()
        with p1, p2, p3:
            self.assertEqual(auth._verify_token(_token()), "auth0|u1")

    def test_wrong_audience_rejected(self):
        p1, p2, p3 = _verify_patched()
        with p1, p2, p3:
            with self.assertRaises(Exception):
                auth._verify_token(_token(aud="other"))

    def test_wrong_issuer_rejected(self):
        p1, p2, p3 = _verify_patched()
        with p1, p2, p3:
            with self.assertRaises(Exception):
                auth._verify_token(_token(iss="https://evil/"))

    def test_expired_token_rejected(self):
        p1, p2, p3 = _verify_patched()
        with p1, p2, p3:
            with self.assertRaises(Exception):
                auth._verify_token(_token(exp=int(time.time()) - 60))

    def test_wrong_signing_key_rejected(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        p1, p2, p3 = _verify_patched()
        with p1, p2, p3:
            with self.assertRaises(Exception):
                auth._verify_token(_token(key=other))

    def test_garbage_token_rejected(self):
        p1, p2, p3 = _verify_patched()
        with p1, p2, p3:
            with self.assertRaises(Exception):
                auth._verify_token("not.a.jwt")


class RequireAuth0Id(unittest.IsolatedAsyncioTestCase):
    async def test_missing_header_401(self):
        with self.assertRaises(HTTPException) as ctx:
            await auth.require_auth0_id(None)
        self.assertEqual(ctx.exception.status_code, 401)

    async def test_non_bearer_scheme_401(self):
        with self.assertRaises(HTTPException) as ctx:
            await auth.require_auth0_id("Basic abc")
        self.assertEqual(ctx.exception.status_code, 401)

    async def test_verify_failure_401(self):
        with (
            patch.object(auth, "_verify_token", side_effect=ValueError("bad")),
            self.assertRaises(HTTPException) as ctx,
        ):
            await auth.require_auth0_id("Bearer x")
        self.assertEqual(ctx.exception.status_code, 401)

    async def test_valid_token_returns_sub(self):
        with patch.object(auth, "_verify_token", return_value="auth0|u1"):
            self.assertEqual(
                await auth.require_auth0_id("Bearer tok"), "auth0|u1"
            )


def _admin_conn(row):
    """Fake async conn whose cursor yields `row` from fetchone."""
    cursor = MagicMock()
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    res = MagicMock()
    res.fetchone = AsyncMock(return_value=row)
    cursor.execute = AsyncMock(return_value=res)
    conn = MagicMock()
    conn.cursor = MagicMock(return_value=cursor)
    return conn


class IsSiteAdmin(unittest.IsolatedAsyncioTestCase):
    async def test_admin_row_true(self):
        self.assertTrue(await auth._is_site_admin(_admin_conn((True,)), "u1"))

    async def test_admin_row_false(self):
        self.assertFalse(await auth._is_site_admin(_admin_conn((False,)), "u1"))

    async def test_missing_row_false(self):
        self.assertFalse(await auth._is_site_admin(_admin_conn(None), "u1"))


class RequireSiteAdmin(unittest.IsolatedAsyncioTestCase):
    async def test_non_admin_403(self):
        with patch.object(
            auth, "_is_site_admin", new=AsyncMock(return_value=False)
        ):
            with self.assertRaises(HTTPException) as ctx:
                await auth.require_site_admin("u1", MagicMock())
        self.assertEqual(ctx.exception.status_code, 403)

    async def test_admin_returns_user_id(self):
        with patch.object(
            auth, "_is_site_admin", new=AsyncMock(return_value=True)
        ):
            self.assertEqual(
                await auth.require_site_admin("u1", MagicMock()), "u1"
            )


class IsSiteAdminRequest(unittest.IsolatedAsyncioTestCase):
    def _request(self, header=None):
        req = MagicMock()
        req.headers = {"authorization": header} if header else {}
        return req

    async def test_no_header_false(self):
        self.assertFalse(await auth.is_site_admin_request(self._request()))

    async def test_non_bearer_false(self):
        self.assertFalse(
            await auth.is_site_admin_request(self._request("Basic x"))
        )

    async def test_verify_failure_false(self):
        with patch.object(
            auth, "_verify_token", side_effect=ValueError("bad")
        ):
            self.assertFalse(
                await auth.is_site_admin_request(self._request("Bearer x"))
            )

    async def test_admin_true(self):
        conn = _admin_conn((True,))
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=False)
        with (
            patch.object(auth, "_verify_token", return_value="auth0|u1"),
            patch.object(
                auth.AsyncConnection, "connect", new=AsyncMock(return_value=cm)
            ),
        ):
            self.assertTrue(
                await auth.is_site_admin_request(self._request("Bearer x"))
            )

    async def test_db_failure_false(self):
        with (
            patch.object(auth, "_verify_token", return_value="auth0|u1"),
            patch.object(
                auth.AsyncConnection,
                "connect",
                new=AsyncMock(side_effect=RuntimeError("down")),
            ),
        ):
            self.assertFalse(
                await auth.is_site_admin_request(self._request("Bearer x"))
            )


class IsDocsRequest(unittest.TestCase):
    def _req(self, path):
        req = MagicMock()
        req.url.path = path
        return req

    def test_docs_path_true(self):
        self.assertTrue(auth.is_docs_request(self._req("/docs")))

    def test_docs_subpath_true(self):
        self.assertTrue(auth.is_docs_request(self._req("/docs/oauth2")))

    def test_other_path_false(self):
        self.assertFalse(auth.is_docs_request(self._req("/resume/export")))


class Deps(unittest.IsolatedAsyncioTestCase):
    async def test_get_amqp_client_unset_raises(self):
        with patch.object(deps, "amqp_client", None):
            with self.assertRaises(RuntimeError):
                deps.get_amqp_client()

    async def test_get_amqp_client_returns_set(self):
        sentinel = MagicMock()
        with patch.object(deps, "amqp_client", sentinel):
            self.assertIs(deps.get_amqp_client(), sentinel)

    async def test_get_pg_conn_yields_then_closes(self):
        conn = MagicMock()
        conn.close = AsyncMock()
        with patch.object(
            deps.AsyncConnection, "connect", new=AsyncMock(return_value=conn)
        ):
            gen = deps.get_pg_conn()
            yielded = await gen.__anext__()
            self.assertIs(yielded, conn)
            with self.assertRaises(StopAsyncIteration):
                await gen.__anext__()
            conn.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
