"""Đăng nhập OAuth một lần để tạo token ghi Drive cho tài khoản người dùng.

Chạy từ `apps/api`:
    ./.venv/bin/python -m app.integrations.drive_oauth_setup \
        --client-file ~/.secrets/pmis-drive-oauth-client.json \
        --token-file ~/.secrets/pmis-drive-oauth-token.json

Trình duyệt sẽ mở để đăng nhập. File token được tạo với quyền 600 và nằm ngoài repo.
"""

import argparse
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from app.integrations.drive import DRIVE_WRITE_SCOPE

OWNER_ONLY_MODE = 0o600


def run_consent(client_file: Path, token_file: Path) -> None:
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes=[DRIVE_WRITE_SCOPE])
    credentials = flow.run_local_server(port=0)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    os.chmod(token_file, OWNER_ONLY_MODE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo token OAuth ghi Google Drive.")
    parser.add_argument("--client-file", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    args = parser.parse_args()
    run_consent(args.client_file.expanduser(), args.token_file.expanduser())
    print(f"Đã lưu token tại {args.token_file.expanduser()}")


if __name__ == "__main__":
    main()
