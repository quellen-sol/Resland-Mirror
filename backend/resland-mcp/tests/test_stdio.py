"""The installed `resland-mcp` command over real stdio, the way Claude Code
launches it: it must speak MCP on stdout from the first byte.

Run: uv run pytest tests/test_stdio.py -v   (from backend/resland-mcp)
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

from mcp import Client, StdioServerParameters

COMMAND = Path(sys.executable).parent / "resland-mcp"


@unittest.skipUnless(COMMAND.exists(), "resland-mcp isn't installed in this venv")
class Stdio(unittest.IsolatedAsyncioTestCase):
    async def test_serves_tools_and_asks_for_login(self):
        tmp = Path(tempfile.mkdtemp())
        env = {
            **os.environ,
            "RESLAND_AUTH0_DOMAIN": "tenant.auth0.test",
            "RESLAND_AUTH0_CLIENT_ID": "cli-123",
            "RESLAND_AUTH0_AUDIENCE": "aud",
            # No credentials here, so no request ever leaves the machine.
            "RESLAND_CREDENTIALS_PATH": str(tmp / "credentials.json"),
        }
        params = StdioServerParameters(command=str(COMMAND), env=env)
        async with Client(params) as client:
            tools = {t.name for t in (await client.list_tools()).tools}
            result = await client.call_tool("get_profile", {})
        self.assertIn("save_tailored_resume", tools)
        self.assertTrue(result.is_error)
        self.assertIn("resland-mcp login", result.content[0].text)
