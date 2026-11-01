import json
from pathlib import Path

import pytest

from app.integrations.drive import GoogleDriveWriter

pytestmark = pytest.mark.unit


def _write_token(path: Path) -> None:
    token = {
        "client_id": "client-id-test",
        "client_secret": "client-secret-test",
        "refresh_token": "refresh-token-test",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/drive"],
    }
    path.write_text(json.dumps(token), encoding="utf-8")


def test_writer_is_built_from_user_token_file_without_network(tmp_path: Path) -> None:
    # Arrange
    token_path = tmp_path / "token.json"
    _write_token(token_path)

    # Act
    writer = GoogleDriveWriter.from_oauth_token_file(str(token_path))

    # Assert
    assert isinstance(writer, GoogleDriveWriter)


def test_missing_token_file_is_reported(tmp_path: Path) -> None:
    # Arrange
    missing = tmp_path / "khong-ton-tai.json"

    # Act / Assert
    with pytest.raises(FileNotFoundError):
        GoogleDriveWriter.from_oauth_token_file(str(missing))
