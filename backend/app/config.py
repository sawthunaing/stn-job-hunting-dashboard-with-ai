"""Application configuration.

Loads from config.json if present, otherwise falls back to environment variables.
This means local dev can use the simple JSON file while production AWS uses env
vars (set by Terraform / Amplify). Best of both worlds.

config.json is gitignored - copy config.example.json and fill in real values.
"""
import json
import os
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    # Database
    database_url: str = "postgresql+psycopg://trajectory:trajectory@localhost:5432/trajectory"

    # OpenAI
    openai_api_key: str = ""
    # Default to a current widely-available model. Common picks:
    #   gpt-4o-mini       - cheap, classic Chat Completions API
    #   gpt-5.4-mini      - newer, smarter, still cheap
    #   gpt-5.5           - flagship
    openai_model: str = "gpt-4o-mini"

    # Auth
    admin_username: str = "admin"
    admin_password: str = "change-me-before-deploying"
    jwt_secret: str = "change-me-before-deploying"
    jwt_ttl_hours: int = 24 * 30  # 30 days

    # CORS
    cors_origin: str = "http://localhost:3000"

    # Demo mode - when True, the API is public read-only (no auth required for
    # GET endpoints) and all write/AI endpoints return 403. Used for the
    # interviewer-facing public demo deployment.
    demo_mode: bool = False


def _load_from_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[config] {path}: {e}")
        return {}


def _load_from_env() -> dict:
    """Pull config values from env vars. Names are uppercased field names."""
    out: dict = {}
    for name in Settings.model_fields:
        env_key = name.upper()
        if env_key in os.environ:
            out[name] = os.environ[env_key]
    if "jwt_ttl_hours" in out:
        try:
            out["jwt_ttl_hours"] = int(out["jwt_ttl_hours"])
        except ValueError:
            del out["jwt_ttl_hours"]
    if "demo_mode" in out:
        out["demo_mode"] = str(out["demo_mode"]).lower() in ("1", "true", "yes", "on")
    return out


def _load() -> Settings:
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

    env_data = _load_from_env()
    merged = {**file_data, **env_data}
    return Settings(**merged)


settings = _load()
