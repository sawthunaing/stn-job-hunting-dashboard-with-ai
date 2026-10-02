"""Unit tests for app.auth - the hand-rolled HS256 JWT and auth dependencies."""
import json
import time

import pytest
from fastapi import HTTPException

from app import auth
from app.config import settings


def _parts(token):
    h, p, s = token.split(".")
    return json.loads(auth._b64url_decode(h)), json.loads(auth._b64url_decode(p)), s


class TestBase64Url:
    @pytest.mark.parametrize("raw", [b"", b"a", b"ab", b"abc", b"\xff\xfe\x00binary"])
    def test_round_trip(self, raw):
        assert auth._b64url_decode(auth._b64url(raw)) == raw

    def test_no_padding_or_unsafe_chars(self):
        enc = auth._b64url(b"\xfb\xff\xbf" * 5 + b"x")
        assert "=" not in enc and "+" not in enc and "/" not in enc


class TestIssueToken:
    def test_has_three_parts_and_expected_claims(self):
        before = int(time.time())
        header, payload, sig = _parts(auth.issue_token("alice"))
        assert header == {"alg": "HS256", "typ": "JWT"}
        assert payload["sub"] == "alice"
        assert before <= payload["iat"] <= int(time.time())
        assert payload["exp"] == payload["iat"] + settings.jwt_ttl_hours * 3600
        assert sig


class TestVerifyToken:
    def test_valid_token(self):
        payload = auth.verify_token(auth.issue_token("alice"))
        assert payload is not None and payload["sub"] == "alice"

    @pytest.mark.parametrize("bad", ["", "abc", "a.b", "a.b.c.d"])
    def test_malformed(self, bad):
        assert auth.verify_token(bad) is None

    def test_tampered_payload_rejected(self):
        h, _, s = auth.issue_token("alice").split(".")
        forged = auth._b64url(json.dumps({"sub": "mallory", "exp": 9999999999}).encode())
        assert auth.verify_token(f"{h}.{forged}.{s}") is None

    def test_tampered_signature_rejected(self):
        h, p, s = auth.issue_token("alice").split(".")
        assert auth.verify_token(f"{h}.{p}.{s[:-2]}xx") is None

    def test_different_secret_rejected(self, monkeypatch):
        token = auth.issue_token("alice")
        monkeypatch.setattr(settings, "jwt_secret", "another-secret")
        assert auth.verify_token(token) is None

    def test_expired_rejected(self, monkeypatch):
        monkeypatch.setattr(settings, "jwt_ttl_hours", -1)
        assert auth.verify_token(auth.issue_token("alice")) is None

    def test_validly_signed_garbage_payload_rejected(self):
        h = auth._b64url(b'{"alg":"HS256"}')
        p = auth._b64url(b"not json")
        sig = auth._b64url(auth._sign(f"{h}.{p}".encode(), settings.jwt_secret))
        assert auth.verify_token(f"{h}.{p}.{sig}") is None


class TestAuthenticate:
    def test_correct_credentials(self):
        assert auth.authenticate(settings.admin_username, settings.admin_password)

    @pytest.mark.parametrize("user,pw", [
        ("tester", "wrong"),
        ("wrong", "s3cret-test-password"),
        ("", ""),
        ("TESTER", "s3cret-test-password"),
    ])
    def test_wrong_credentials(self, user, pw):
        assert not auth.authenticate(user, pw)


class TestRequireAuth:
    def test_returns_username(self):
        assert auth.require_auth(f"Bearer {auth.issue_token('tester')}") == "tester"

    def test_tolerates_whitespace_after_bearer(self):
        assert auth.require_auth(f"Bearer   {auth.issue_token('tester')}  ") == "tester"

    @pytest.mark.parametrize("header", ["", "Basic abc", "bearer xyz", "Token abc"])
    def test_missing_or_wrong_scheme(self, header):
        with pytest.raises(HTTPException) as exc:
            auth.require_auth(header)
        assert exc.value.status_code == 401
        assert "bearer" in exc.value.detail

    def test_invalid_token(self):
        with pytest.raises(HTTPException) as exc:
            auth.require_auth("Bearer not.a.token")
        assert exc.value.status_code == 401

    def test_refuses_when_default_password_is_still_set(self, monkeypatch):
        monkeypatch.setattr(settings, "admin_password", "change-me-before-deploying")
        with pytest.raises(HTTPException) as exc:
            auth.require_auth(f"Bearer {auth.issue_token('tester')}")
        assert exc.value.status_code == 401
        assert "not configured" in exc.value.detail


class TestReadWriteGuards:
    def test_read_requires_auth_outside_demo(self):
        with pytest.raises(HTTPException):
            auth.require_read("")

    def test_read_is_public_in_demo(self, demo_mode):
        assert auth.require_read("") == "demo-visitor"

    def test_write_passes_with_token(self):
        assert auth.require_write(f"Bearer {auth.issue_token('tester')}") == "tester"

    def test_write_forbidden_in_demo_even_with_token(self, demo_mode):
        with pytest.raises(HTTPException) as exc:
            auth.require_write(f"Bearer {auth.issue_token('tester')}")
        assert exc.value.status_code == 403
