import time
from collections import deque
from collections.abc import Callable

Clock = Callable[[], float]


class SlidingWindowRateLimiter:
    """Giới hạn số lần thao tác theo khóa trong cửa sổ trượt (trạng thái trong bộ nhớ tiến trình).

    Gọi trong event loop (không có `await` giữa các bước), nên không cần khóa.
    """

    def __init__(
        self,
        *,
        max_hits: int,
        window_seconds: float,
        clock: Clock = time.monotonic,
    ) -> None:
        self._max_hits = max_hits
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._next_sweep_at = clock() + window_seconds

    @property
    def tracked_key_count(self) -> int:
        return len(self._hits)

    def acquire(self, key: str) -> float:
        """Ghi nhận một lần thao tác. Trả 0 nếu được phép, hoặc số giây phải chờ nếu bị từ chối."""
        now = self._clock()
        self._sweep_expired(now)
        hits = self._hits.setdefault(key, deque())
        self._drop_expired(hits, now)
        if len(hits) >= self._max_hits:
            return hits[0] + self._window_seconds - now
        hits.append(now)
        return 0.0

    def _drop_expired(self, hits: deque[float], now: float) -> None:
        while hits and now - hits[0] >= self._window_seconds:
            hits.popleft()

    def _sweep_expired(self, now: float) -> None:
        # Quét toàn bộ khóa một lần mỗi cửa sổ để IP chỉ gọi một lần không làm bộ nhớ phình mãi.
        if now < self._next_sweep_at:
            return
        for key in list(self._hits):
            hits = self._hits[key]
            self._drop_expired(hits, now)
            if not hits:
                del self._hits[key]
        self._next_sweep_at = now + self._window_seconds
