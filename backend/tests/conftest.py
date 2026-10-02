"""Shared pytest setup.

Settings are loaded once at import time from env vars, so we set them here
*before* any `app.*` module is imported. Tests run against a throwaway SQLite
database instead of Postgres, and never call the real Anthropic API.
"""
import os
import sys
import tempfile
from pathlib import Path

_TMP_DIR = tempfile.mkdtemp(prefix="jobdash-tests-")

os.environ["CONFIG_PATH"] = str(Path(_TMP_DIR) / "no-config.json")  # never read a real config.json
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR) / 'test.db'}"
os.environ["ADMIN_USERNAME"] = "tester"
os.environ["ADMIN_PASSWORD"] = "s3cret-test-password"
os.environ["JWT_SECRET"] = "test-jwt-secret"
os.environ["JWT_TTL_HOURS"] = "1"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["DEMO_MODE"] = "false"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from app.config import settings  # noqa: E402


@pytest.fixture
def demo_mode(monkeypatch):
    """Flip the app into read-only public demo mode for one test."""
    monkeypatch.setattr(settings, "demo_mode", True)
    yield
