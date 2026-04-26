"""Application configuration.

Loads from config.json if present, otherwise falls back to environment variables.
This means local dev can use the simple JSON file while production AWS uses env
vars (set by Terraform / Amplify). Best of both worlds.

config.json is gitignored - copy config.example.json and fill in real values.
"""
import json
import os
from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Database
    database_url: str = "postgresql+psycopg://trajectory:trajectory@localhost:5432/trajectory"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Auth - login credentials for the dashboard
    admin_username: str = "admin"
    admin_password: str = "change-me-before-deploying"
    # Secret used to sign session tokens. Make this long and random in production.
    jwt_secret: str = "change-me-before-deploying"
    # Token lifetime in hours
    jwt_ttl_hours: int = 24 * 30  # 30 days = stays logged in for a month

    # CORS
    cors_origin: str = "http://localhost:3000"


def _load_from_json(path: Path) -> dict:
    """Read config.json and return a dict suitable for Settings."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[config] {path}: {e}")
        return {}


def _load_from_env() -> dict:
    """Pull config values from environment variables.

    Env var names are uppercase versions of field names: openai_api_key -> OPENAI_API_KEY
    """
    out: dict = {}
    for name in Settings.model_fields:
        env_key = name.upper()
        if env_key in os.environ:
            out[name] = os.environ[env_key]
    # Coerce ints back from string env vars
    if "jwt_ttl_hours" in out:
        try:
            out["jwt_ttl_hours"] = int(out["jwt_ttl_hours"])
        except ValueError:
            del out["jwt_ttl_hours"]
    return out


def _load() -> Settings:
    # Look for config.json next to the backend code
    candidate_paths = [
        Path(os.environ.get("CONFIG_PATH", "")) if os.environ.get("CONFIG_PATH") else None,
        Path("config.json"),
        Path("/app/config.json"),
        Path(__file__).resolve().parent.parent / "config.json",
    ]
    file_data: dict = {}
    for p in candidate_paths:
        if p and p.exists():
            file_data = _load_from_json(p)
            print(f"[config] loaded from {p}")
            break

    # Env vars override file values - this is what AWS deploy relies on
    env_data = _load_from_env()
    merged = {**file_data, **env_data}
    return Settings(**merged)


settings = _load()
