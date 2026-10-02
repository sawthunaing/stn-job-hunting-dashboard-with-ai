"""Unit tests for app.config loading (JSON file + env var overrides)."""
import json

import pytest

from app import config


@pytest.fixture
def clean_env(monkeypatch):
    for name in config.Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    return monkeypatch


def test_defaults():
    s = config.Settings()
    assert s.admin_username == "admin"
    assert s.demo_mode is False
    assert s.jwt_ttl_hours == 24 * 30


class TestLoadFromJson:
    def test_valid_file(self, tmp_path):
        f = tmp_path / "c.json"
        f.write_text(json.dumps({"admin_username": "bob"}))
        assert config._load_from_json(f) == {"admin_username": "bob"}

    def test_missing_file(self, tmp_path):
        assert config._load_from_json(tmp_path / "nope.json") == {}

    def test_invalid_json(self, tmp_path):
        f = tmp_path / "c.json"
        f.write_text("{not json")
        assert config._load_from_json(f) == {}


class TestLoadFromEnv:
    def test_picks_up_uppercased_field_names_only(self, clean_env):
        clean_env.setenv("ADMIN_USERNAME", "envuser")
        clean_env.setenv("UNRELATED_VAR", "x")
        assert config._load_from_env() == {"admin_username": "envuser"}

    def test_ttl_cast_to_int(self, clean_env):
        clean_env.setenv("JWT_TTL_HOURS", "12")
        assert config._load_from_env()["jwt_ttl_hours"] == 12

    def test_bad_ttl_dropped(self, clean_env):
        clean_env.setenv("JWT_TTL_HOURS", "twelve")
        assert "jwt_ttl_hours" not in config._load_from_env()

    @pytest.mark.parametrize("val,expected", [
        ("1", True), ("true", True), ("YES", True), ("on", True),
        ("0", False), ("false", False), ("", False), ("nope", False),
    ])
    def test_demo_mode_parsing(self, clean_env, val, expected):
        clean_env.setenv("DEMO_MODE", val)
        assert config._load_from_env()["demo_mode"] is expected


class TestLoad:
    def test_env_overrides_file(self, clean_env, tmp_path):
        f = tmp_path / "c.json"
        f.write_text(json.dumps({"admin_username": "fileuser", "cors_origin": "https://file"}))
        clean_env.setenv("CONFIG_PATH", str(f))
        clean_env.setenv("ADMIN_USERNAME", "envuser")
        s = config._load()
        assert s.admin_username == "envuser"
        assert s.cors_origin == "https://file"

    def test_legacy_openai_keys_still_accepted(self, clean_env, tmp_path):
        f = tmp_path / "c.json"
        f.write_text(json.dumps({"openai_api_key": "sk-old", "openai_model": "gpt-4o"}))
        clean_env.setenv("CONFIG_PATH", str(f))
        assert config._load().openai_api_key == "sk-old"
