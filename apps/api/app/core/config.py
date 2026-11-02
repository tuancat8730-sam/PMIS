from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """Cấu hình đọc từ biến môi trường. Thiếu secret bắt buộc thì ứng dụng không khởi động."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://pmis:pmis@localhost:5432/pmis"
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, gt=0)
    cccd_encryption_key: SecretStr
    cors_origins: list[str] = ["http://localhost:3000"]
    login_rate_limit_attempts: int = Field(default=5, gt=0)
    login_rate_limit_window_seconds: int = Field(default=900, gt=0)
    write_rate_limit_attempts: int = Field(default=30, gt=0)
    write_rate_limit_window_seconds: int = Field(default=60, gt=0)
    # File JSON khóa tài khoản dịch vụ Drive, nằm ngoài repo. Thiếu thì tính năng Drive tắt.
    drive_service_account_file: str | None = None
    # Token OAuth người dùng để ghi lên Drive, tạo bằng `drive_oauth_setup`, nằm ngoài repo.
    drive_oauth_token_file: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    # Thư mục lưu ảnh và biên bản ký tay từ thiết bị hiện trường (lưu cục bộ trước, Drive sau E5).
    field_photo_dir: str = "var/field_photos"

    @model_validator(mode="after")
    def _check_jwt_secret_length(self) -> "Settings":
        if len(self.jwt_secret.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(f"JWT_SECRET phải có ít nhất {MIN_JWT_SECRET_LENGTH} ký tự")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
