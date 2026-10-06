"""Account routes — wire shapes for GET /account/export and DELETE /account,
plus the row-lock helper the job paths share (api.user_row).

Run: .venv/bin/python -m unittest backend.api.tests.test_account_router -v
"""

import io
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from api import api as api_app
from api.account import model, router, service
from api.auth import require_auth0_id
from api.deps import get_pg_conn
from api.user_row import share_user_row

from .helpers import _Pg, one


class Routes(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router.router)
        app.dependency_overrides[require_auth0_id] = lambda: "auth0|u1"
        app.dependency_overrides[get_pg_conn] = lambda: None
        self.client = TestClient(app)

    def test_export_streams_a_zip_download(self):
        archive = io.BytesIO(b"PK\x03\x04 zip bytes")
        with (
            patch.object(
                service, "export_account", new=AsyncMock(return_value=archive)
            ) as export,
            patch.object(
                service, "export_filename", return_value="resland-data-2026-10-06.zip"
            ),
        ):
            resp = self.client.get("/account/export")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/zip")
        self.assertEqual(
            resp.headers["content-disposition"],
            'attachment; filename="resland-data-2026-10-06.zip"',
        )
        self.assertEqual(resp.content, b"PK\x03\x04 zip bytes")
        self.assertEqual(export.call_args.kwargs["user_id"], "auth0|u1")
        # The spooled archive is closed once streamed.
        self.assertTrue(archive.closed)

    def test_delete_returns_ok(self):
        with patch.object(
            service,
            "delete_account",
            new=AsyncMock(return_value=model.DeleteAccountResponse()),
        ) as delete:
            resp = self.client.delete("/account")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})
        self.assertEqual(delete.call_args.kwargs["user_id"], "auth0|u1")

    def test_delete_conflict_passes_through(self):
        with patch.object(
            service,
            "delete_account",
            new=AsyncMock(side_effect=HTTPException(409, "busy")),
        ):
            resp = self.client.delete("/account")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json(), {"detail": "busy"})

    def test_routes_need_a_token(self):
        app = FastAPI()
        app.include_router(router.router)
        app.dependency_overrides[get_pg_conn] = lambda: None
        client = TestClient(app)
        self.assertEqual(client.get("/account/export").status_code, 401)
        self.assertEqual(client.delete("/account").status_code, 401)


class AppWiring(unittest.TestCase):
    def test_routes_are_mounted(self):
        paths = api_app.app.openapi()["paths"]
        self.assertIn("get", paths["/account/export"])
        self.assertIn("delete", paths["/account"])

    def test_cors_exposes_the_download_filename(self):
        cors = next(
            m for m in api_app.app.user_middleware if m.cls.__name__ == "CORSMiddleware"
        )
        self.assertIn("Content-Disposition", cors.kwargs["expose_headers"])


class ShareUserRow(unittest.IsolatedAsyncioTestCase):
    async def test_locks_the_row_for_key_share(self):
        pg = _Pg([one((1,))])
        await share_user_row(pg, "auth0|u1")
        query, params = pg.queries[0]
        self.assertIn('FROM "user"', query)
        self.assertIn("FOR KEY SHARE", query)
        self.assertEqual(params, ("auth0|u1",))

    async def test_deleted_account_404s(self):
        with self.assertRaises(HTTPException) as ctx:
            await share_user_row(_Pg([]), "auth0|u1")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
