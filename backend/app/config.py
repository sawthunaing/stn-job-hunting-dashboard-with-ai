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

    # Anthropic Claude (active AI provider)
    anthropic_api_key: str = ""
    # Model picks:
    #   claude-sonnet-4-6           - best balance of quality and cost (recommended)
    #   claude-haiku-4-5-20251001   - cheapest, fast, good for extraction
    #   claude-opus-4-7             - flagship quality, most expensive
    anthropic_model: str = "claude-sonnet-4-6"

    # OpenAI (legacy - no longer used after Claude migration, kept so old
    # config.json files don't break validation)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Auth
    admin_username: str = "admin"
    admin_password: str = "change-me-before-deploying"
    jwt_secret: str = "change-me-before-deploying"
    jwt_ttl_hours: int = 24 * 30  # 30 days

    # CORS
    cors_origin: str = "http://localhost:3000"

    # Demo mode - kept for compatibility with existing main.py / auth.py.
    # (Demo deployment removal is a separate step.)
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
