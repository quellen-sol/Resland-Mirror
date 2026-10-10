"""Settings from the environment, set where the MCP client launches the
server (`claude mcp add ... -e KEY=value`) or in your shell for the CLI."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_API_URL = "https://api.resland.org"
DEFAULT_APP_URL = "https://resland.org"

# The Auth0 tenant values have no defaults: they come from the Native
# application set up for this server (see README).
REQUIRED = ("RESLAND_AUTH0_DOMAIN", "RESLAND_AUTH0_CLIENT_ID", "RESLAND_AUTH0_AUDIENCE")


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    api_url: str
    app_url: str
    auth0_domain: str
    auth0_client_id: str
    auth0_audience: str
    credentials_path: Path
    export_dir: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        missing = [key for key in REQUIRED if not env.get(key)]
        if missing:
            raise ConfigError(
                f"Set {', '.join(missing)} (see backend/resland-mcp/README.md)."
            )
        config_home = Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        return cls(
            api_url=env.get("RESLAND_API_URL", DEFAULT_API_URL).rstrip("/"),
            app_url=env.get("RESLAND_APP_URL", DEFAULT_APP_URL).rstrip("/"),
            auth0_domain=env["RESLAND_AUTH0_DOMAIN"]
            .removeprefix("https://")
            .rstrip("/"),
            auth0_client_id=env["RESLAND_AUTH0_CLIENT_ID"],
            auth0_audience=env["RESLAND_AUTH0_AUDIENCE"],
            credentials_path=Path(
                env.get("RESLAND_CREDENTIALS_PATH")
                or config_home / "resland-mcp" / "credentials.json"
            ).expanduser(),
            export_dir=Path(
                env.get("RESLAND_EXPORT_DIR") or Path.home() / "Downloads" / "resland"
            ).expanduser(),
        )
