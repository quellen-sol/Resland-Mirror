"""account.sweeper.run_forever — the loop around sweep_once (the sweep
itself runs against live Postgres in test_account_pg).

Run: .venv/bin/python -m unittest backend.api.tests.test_account_sweeper -v
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api.account import sweeper


def _connect():
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=MagicMock(name="conn"))
    cm.__aexit__ = AsyncMock(return_value=False)
    return AsyncMock(return_value=cm)


class RunForever(unittest.IsolatedAsyncioTestCase):
    async def test_keeps_sweeping_after_a_failed_pass_until_cancelled(self):
        passes = []
        done = asyncio.Event()

        async def sweep(conn, auth0):
            passes.append(conn)
            if len(passes) == 1:
                raise RuntimeError("database down")
            if len(passes) == 3:
                done.set()
            return sweeper.SweepResult(logins_deleted=1, purged=0)

        with (
            patch.object(sweeper.AsyncConnection, "connect", new=_connect()),
            patch.object(sweeper, "sweep_once", new=sweep),
            patch.object(sweeper, "auth0_management", return_value=MagicMock()),
        ):
            task = asyncio.create_task(sweeper.run_forever(interval_s=0))
            await asyncio.wait_for(done.wait(), 2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertGreaterEqual(len(passes), 3)


if __name__ == "__main__":
    unittest.main()
