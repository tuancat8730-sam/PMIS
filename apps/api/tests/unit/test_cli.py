import pytest

from app.cli import main

pytestmark = pytest.mark.unit


def test_main_rejects_short_password_without_touching_database(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange
    monkeypatch.setattr("app.cli.getpass.getpass", lambda prompt: "ngan")

    # Act
    exit_code = main(["create-admin", "--email", "admin@example.com", "--name", "Quản trị"])

    # Assert
    assert exit_code == 1
    assert "Mật khẩu quá ngắn" in capsys.readouterr().out
