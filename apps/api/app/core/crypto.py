from cryptography.fernet import Fernet


class FieldCipher:
    """Mã hóa đối xứng cho trường nhạy cảm như số CCCD. Mỗi lần mã hóa ra chuỗi khác nhau."""

    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Ném `cryptography.fernet.InvalidToken` khi khóa sai hoặc dữ liệu bị sửa."""
        return self._fernet.decrypt(token.encode()).decode()
