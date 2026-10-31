import pytest

from app.core.rate_limit import SlidingWindowRateLimiter

pytestmark = pytest.mark.unit

WINDOW_SECONDS = 60.0


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _limiter(max_hits: int, clock: FakeClock) -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter(
        max_hits=max_hits,
        window_seconds=WINDOW_SECONDS,
        clock=clock,
    )


def test_allows_hits_up_to_the_limit() -> None:
    # Arrange
    clock = FakeClock()
    limiter = _limiter(max_hits=3, clock=clock)

    # Act
    results = [limiter.acquire("10.0.0.1") for _ in range(3)]

    # Assert
    assert results == [0.0, 0.0, 0.0]


def test_rejects_hit_over_limit_with_seconds_until_oldest_hit_expires() -> None:
    # Arrange
    clock = FakeClock()
    limiter = _limiter(max_hits=2, clock=clock)
    limiter.acquire("10.0.0.1")  # t = 0
    clock.now = 10.0
    limiter.acquire("10.0.0.1")  # t = 10

    # Act
    clock.now = 30.0
    wait_seconds = limiter.acquire("10.0.0.1")

    # Assert
    assert wait_seconds == pytest.approx(30.0)


def test_allows_again_once_oldest_hit_leaves_the_window() -> None:
    # Arrange
    clock = FakeClock()
    limiter = _limiter(max_hits=1, clock=clock)
    limiter.acquire("10.0.0.1")

    # Act
    clock.now = WINDOW_SECONDS

    # Assert
    assert limiter.acquire("10.0.0.1") == 0.0


def test_keys_are_limited_independently() -> None:
    # Arrange
    clock = FakeClock()
    limiter = _limiter(max_hits=1, clock=clock)
    limiter.acquire("10.0.0.1")

    # Act
    wait_seconds = limiter.acquire("10.0.0.2")

    # Assert
    assert wait_seconds == 0.0


def test_rejected_hits_do_not_extend_the_block() -> None:
    # Arrange
    clock = FakeClock()
    limiter = _limiter(max_hits=1, clock=clock)
    limiter.acquire("10.0.0.1")  # t = 0, được phép

    # Act
    clock.now = 30.0
    rejected_wait = limiter.acquire("10.0.0.1")
    clock.now = WINDOW_SECONDS
    allowed_wait = limiter.acquire("10.0.0.1")

    # Assert
    assert rejected_wait == pytest.approx(30.0)
    assert allowed_wait == 0.0


def test_keys_still_inside_the_window_survive_a_sweep() -> None:
    # Arrange
    clock = FakeClock()
    limiter = _limiter(max_hits=1, clock=clock)
    limiter.acquire("10.0.0.1")  # t = 0, hết hạn lúc 60
    clock.now = 30.0
    limiter.acquire("10.0.0.2")  # t = 30, còn hiệu lực lúc 60

    # Act
    clock.now = WINDOW_SECONDS
    limiter.acquire("10.0.0.3")  # kích hoạt quét tại t = 60

    # Assert
    assert limiter.tracked_key_count == 2
    assert limiter.acquire("10.0.0.2") == pytest.approx(30.0)


def test_expired_keys_are_dropped_from_memory() -> None:
    # Arrange
    clock = FakeClock()
    limiter = _limiter(max_hits=1, clock=clock)
    limiter.acquire("10.0.0.1")
    limiter.acquire("10.0.0.2")

    # Act
    clock.now = WINDOW_SECONDS
    limiter.acquire("10.0.0.3")

    # Assert
    assert limiter.tracked_key_count == 1
