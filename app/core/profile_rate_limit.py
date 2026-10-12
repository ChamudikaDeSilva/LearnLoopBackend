"""Bounded, process-local limits for authenticated credential checks."""

from collections import OrderedDict, deque
from math import ceil
from threading import Lock
from time import monotonic


class ReauthenticationRateLimitError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = max(1, retry_after)
        super().__init__("Too many credential checks. Try again shortly.")


class ProfileReauthenticationLimiter:
    def __init__(self, limit: int = 5, window_seconds: int = 300, max_entries: int = 10000):
        if limit < 1 or window_seconds < 1 or max_entries < 2:
            raise ValueError("Rate limit settings must be positive.")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_entries = max_entries
        self._attempts: OrderedDict[tuple[str, object], deque[float]] = OrderedDict()
        self._lock = Lock()

    def check(self, user_id: int, client_address: str) -> None:
        keys = (("user", user_id), ("client", client_address))
        with self._lock:
            now = monotonic()
            cutoff = now - self.window_seconds
            # Ordering follows each key's latest use, so wholly expired keys are first.
            while self._attempts:
                first_key, timestamps = next(iter(self._attempts.items()))
                if timestamps[-1] > cutoff:
                    break
                del self._attempts[first_key]

            needed = sum(key not in self._attempts for key in keys)
            if len(self._attempts) + needed > self.max_entries:
                raise ReauthenticationRateLimitError(self.window_seconds)

            for key in keys:
                timestamps = self._attempts.get(key)
                if timestamps is None:
                    continue
                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()
                # Permit several accounts on one network without weakening account limits.
                limit = self.limit if key[0] == "user" else self.limit * 5
                if len(timestamps) >= limit:
                    raise ReauthenticationRateLimitError(
                        ceil(timestamps[0] + self.window_seconds - now)
                    )

            for key in keys:
                self._attempts.setdefault(key, deque()).append(now)
                self._attempts.move_to_end(key)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()
