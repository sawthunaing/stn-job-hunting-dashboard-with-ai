from app import ratelimit
from app.config import settings
from app.main import login_limiter

PASSWORD = settings.admin_password


def _login(client, password):
    return client.post("/auth/login", json={"username": settings.admin_username, "password": password})


def test_blocks_after_repeated_failures_then_success_resets(client):
    login_limiter.reset("testclient")
    for _ in range(login_limiter.max_failures):
        assert _login(client, "wrong").status_code == 401
    blocked = _login(client, PASSWORD)
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    login_limiter.reset("testclient")
    assert _login(client, PASSWORD).status_code == 200


def test_success_clears_ip_counter(client):
    login_limiter.reset("testclient")
    for _ in range(login_limiter.max_failures - 1):
        _login(client, "wrong")
    assert _login(client, PASSWORD).status_code == 200
    for _ in range(login_limiter.max_failures):
        assert _login(client, "wrong").status_code == 401
    login_limiter.reset("testclient")


def test_window_expiry_and_global_cap(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(ratelimit.time, "monotonic", lambda: clock[0])
    lim = ratelimit.LoginLimiter(max_failures=2, window_seconds=60, global_multiplier=2)
    lim.record_failure("a"); lim.record_failure("a")
    assert lim.retry_after("a") > 0 and lim.retry_after("b") == 0
    clock[0] += 61
    assert lim.retry_after("a") == 0
    for ip in "wxyz":
        lim.record_failure(ip)
    assert lim.retry_after("brand-new-ip") > 0  # global cap (4) reached
