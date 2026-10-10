# resland-mcp

A personal MCP server that lets Claude Code or Claude Desktop tailor resumes
against your Resland account. Claude does the writing on your own Claude plan;
the server only reads and saves through the Resland API (as you, with your
Auth0 login). Nothing goes through OpenRouter, and nothing is charged to your
Resland balance.

It runs locally over stdio. Anthropic doesn't let third-party apps sign people
in with their Claude subscription, so this is the supported shape: you add a
server to your own Claude app, and Claude calls it.

## What Claude gets

| Tool | What it does |
|---|---|
| `get_profile` | Your base profile, with experience and bullet ids |
| `list_memory` / `remember_facts` | Read and add to your memory bank (shared with the site's agents) |
| `save_tailored_resume` | Save a tailored resume to your board (`POST /tailored`) |
| `list_tailored_resumes` / `get_tailored_resume` / `update_tailored_resume` | Work with saved ones |
| `export_tailored_resume` | Download the DOCX (in your uploaded resume's layout), or a PDF via LibreOffice |

Plus a `tailor` prompt: `/resland:tailor` in Claude Code (paste the posting
when Claude asks), or pick it from the prompts menu in Claude Desktop. It
carries the same bullet-writing and memory rules the site's tailor agent uses
(`shared.writing`, `shared.memory`).

## One-time Auth0 setup

The server signs in with Auth0's device flow, which needs its own Native
application in the Resland tenant:

1. **Applications → Create Application → Native**, named e.g. "Resland MCP".
2. In its **Settings → Advanced Settings → Grant Types**, enable
   **Device Code** and **Refresh Token**.
3. Under **APIs**, open the Resland API (its identifier is the API's
   `AUTH0_AUDIENCE`) and turn on **Allow Offline Access**, so a login comes
   with a refresh token. If the API's user-access policy only admits
   authorized applications, authorize "Resland MCP" there too.
4. Note the tenant **Domain** and the new app's **Client ID**.

## Install

From the repo root:

```bash
export RESLAND_AUTH0_DOMAIN=<tenant>.us.auth0.com
export RESLAND_AUTH0_CLIENT_ID=<Resland MCP client id>
export RESLAND_AUTH0_AUDIENCE=<API identifier>

# Sign in once. Prints a URL and a code to approve in the browser.
uv run --package resland-mcp resland-mcp login

# Claude Code (user scope, so it's available in every project):
claude mcp add --scope user --transport stdio \
  -e RESLAND_AUTH0_DOMAIN=$RESLAND_AUTH0_DOMAIN \
  -e RESLAND_AUTH0_CLIENT_ID=$RESLAND_AUTH0_CLIENT_ID \
  -e RESLAND_AUTH0_AUDIENCE=$RESLAND_AUTH0_AUDIENCE \
  resland -- uv run --directory "$PWD/backend/resland-mcp" resland-mcp
```

For Claude Desktop, add the same command to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "resland": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/resland/backend/resland-mcp", "resland-mcp"],
      "env": {
        "RESLAND_AUTH0_DOMAIN": "<tenant>.us.auth0.com",
        "RESLAND_AUTH0_CLIENT_ID": "<Resland MCP client id>",
        "RESLAND_AUTH0_AUDIENCE": "<API identifier>"
      }
    }
  }
}
```

`resland-mcp status` shows who you're signed in as; `resland-mcp logout`
deletes the saved login. When the refresh token stops working, tools answer
with "Run `resland-mcp login`".

## Settings

| Variable | Default |
|---|---|
| `RESLAND_AUTH0_DOMAIN`, `RESLAND_AUTH0_CLIENT_ID`, `RESLAND_AUTH0_AUDIENCE` | required |
| `RESLAND_API_URL` | `https://api.resland.org` (`http://localhost:3001` for the local stack) |
| `RESLAND_APP_URL` | `https://resland.org`, for links to saved resumes |
| `RESLAND_CREDENTIALS_PATH` | `~/.config/resland-mcp/credentials.json` (written 0600) |
| `RESLAND_EXPORT_DIR` | `~/Downloads/resland` |

PDF export shells out to `soffice` (LibreOffice); DOCX needs nothing extra.

## Tests

```bash
cd backend/resland-mcp && uv run pytest --cov
```

The tests fake the API and Auth0 over an `httpx2.MockTransport` and drive the
tools through an in-process MCP client.
