"""In-memory limiter for failed login attempts.

State lives in this process, which is fine for the single-worker, single-user
deployment. Two buckets are checked: one per client IP, and one global bucket
so that guessing the admin password from many IPs is throttled too.
"""
import threading
import time
from collections import deque

_MAX_TRACKED_IPS = 10_000


class LoginLimiter:
    def __init__(self, max_failures: int, window_seconds: int, global_multiplier: int = 4):
        self.max_failures = max_failures
        self.window = window_seconds
        self.global_max = max_failures * global_multiplier
        self._per_ip: dict[str, deque[float]] = {}
        self._global: deque[float] = deque()
        self._lock = threading.Lock()

    def _prune(self, q: deque, now: float) -> None:
        while q and q[0] <= now - self.window:
            q.popleft()

    def _retry_after(self, q: deque, limit: int, now: float) -> int:
        self._prune(q, now)
        if len(q) < limit:
            return 0
        return max(1, int(q[len(q) - limit] + self.window - now) + 1)

    def retry_after(self, ip: str) -> int:
        """Seconds the caller must wait before another attempt, or 0 if allowed."""
        now = time.monotonic()
        with self._lock:
            wait_ip = self._retry_after(self._per_ip.get(ip, deque()), self.max_failures, now)
            wait_global = self._retry_after(self._global, self.global_max, now)
            return max(wait_ip, wait_global)

    def record_failure(self, ip: str) -> None:
        now = time.monotonic()
        with self._lock:
            if ip not in self._per_ip and len(self._per_ip) >= _MAX_TRACKED_IPS:
                for key in [k for k, q in self._per_ip.items() if not q or q[-1] <= now - self.window]:
                    del self._per_ip[key]
            self._per_ip.setdefault(ip, deque()).append(now)
            self._global.append(now)

    def reset(self, ip: str) -> None:
        with self._lock:
            self._per_ip.pop(ip, None)
