from types import SimpleNamespace

import pytest

from app import ai


def _resp(text, stop="end_turn"):
    return SimpleNamespace(content=[SimpleNamespace(text=text)], stop_reason=stop)


def _fake_client(responses):
    calls = iter(responses)
    messages = SimpleNamespace(create=lambda **kw: next(calls))
    return lambda: SimpleNamespace(messages=messages)


def test_retries_once_then_succeeds(monkeypatch):
    monkeypatch.setattr(ai, "client", _fake_client([_resp("not json"), _resp('```json\n{"a": 1}\n```')]))
    assert ai._call_json("s", "u") == {"a": 1}


def test_truncated_reply_raises(monkeypatch):
    monkeypatch.setattr(ai, "client", _fake_client([_resp('{"a"', "max_tokens")] * 2))
    with pytest.raises(ai.AIError):
        ai._call_json("s", "u")
