import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.core.crypto import FieldCipher

pytestmark = pytest.mark.unit


def test_encrypt_then_decrypt_returns_original_value() -> None:
    # Arrange
    cipher = FieldCipher(Fernet.generate_key().decode())

    # Act
    token = cipher.encrypt("001085012345")
    value = cipher.decrypt(token)

    # Assert
    assert value == "001085012345"


def test_ciphertext_does_not_contain_plaintext() -> None:
    # Arrange
    cipher = FieldCipher(Fernet.generate_key().decode())

    # Act
    token = cipher.encrypt("001085012345")

    # Assert
    assert "001085012345" not in token


def test_same_plaintext_encrypts_to_different_ciphertexts() -> None:
    # Arrange
    cipher = FieldCipher(Fernet.generate_key().decode())

    # Act
    first = cipher.encrypt("001085012345")
    second = cipher.encrypt("001085012345")

    # Assert
    assert first != second


def test_decrypt_with_other_key_raises_invalid_token() -> None:
    # Arrange
    token = FieldCipher(Fernet.generate_key().decode()).encrypt("001085012345")
    other = FieldCipher(Fernet.generate_key().decode())

    # Act / Assert
    with pytest.raises(InvalidToken):
        other.decrypt(token)


def test_invalid_key_is_rejected_at_construction() -> None:
    # Act / Assert
    with pytest.raises(ValueError):
        FieldCipher("khong-phai-khoa-fernet")
