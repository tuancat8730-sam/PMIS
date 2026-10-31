import pytest

from app.cli import main
from app.core.config import Settings

pytestmark = pytest.mark.integration

ADMIN_PASSWORD = "mat-khau-admin-tu-cli-2026"
ADMIN_ARGUMENTS = ["create-admin", "--email", "cli-admin@example.com", "--name", "Quản trị CLI"]


@pytest.fixture
def cli_settings(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> Settings:
    monkeypatch.setattr("app.cli.get_settings", lambda: settings)
    monkeypatch.setattr("app.cli.getpass.getpass", lambda prompt: ADMIN_PASSWORD)
    return settings


def test_main_creates_admin_and_returns_zero(
    cli_settings: Settings,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Act
    exit_code = main(ADMIN_ARGUMENTS)

    # Assert
    assert exit_code == 0
    assert "Đã tạo tài khoản ADMIN: cli-admin@example.com" in capsys.readouterr().out


def test_main_returns_one_when_email_already_exists(
    cli_settings: Settings,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange
    main(ADMIN_ARGUMENTS)
    capsys.readouterr()

    # Act
    exit_code = main(ADMIN_ARGUMENTS)

    # Assert
    assert exit_code == 1
    assert "đã tồn tại" in capsys.readouterr().out
