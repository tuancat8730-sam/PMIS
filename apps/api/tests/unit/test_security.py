from datetime import timedelta

import pytest
from jwt import InvalidTokenError

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit

SECRET = "x" * 32
OTHER_SECRET = "y" * 32
ALGORITHM = "HS256"


def test_hash_password_does_not_store_plaintext() -> None:
    # Arrange
    plain = "mat-khau-rat-dai-123"

    # Act
    hashed = hash_password(plain)

    # Assert
    assert hashed != plain
    assert verify_password(plain, hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    # Arrange
    hashed = hash_password("mat-khau-dung-123")

    # Act
    result = verify_password("mat-khau-sai-456", hashed)

    # Assert
    assert result is False


def test_access_token_round_trip_returns_subject_and_role() -> None:
    # Arrange
    token = create_access_token(
        subject="user-1",
        role="PM",
        secret=SECRET,
        algorithm=ALGORITHM,
        expires_in=timedelta(minutes=5),
    )

    # Act
    claims = decode_access_token(token, secret=SECRET, algorithm=ALGORITHM)

    # Assert
    assert claims.subject == "user-1"
    assert claims.role == "PM"


def test_expired_access_token_is_rejected() -> None:
    # Arrange
    token = create_access_token(
        subject="user-1",
        role="PM",
        secret=SECRET,
        algorithm=ALGORITHM,
        expires_in=timedelta(seconds=-1),
    )

    # Act / Assert
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret=SECRET, algorithm=ALGORITHM)


def test_token_signed_with_other_secret_is_rejected() -> None:
    # Arrange
    token = create_access_token(
        subject="user-1",
        role="PM",
        secret=OTHER_SECRET,
        algorithm=ALGORITHM,
        expires_in=timedelta(minutes=5),
    )

    # Act / Assert
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret=SECRET, algorithm=ALGORITHM)
