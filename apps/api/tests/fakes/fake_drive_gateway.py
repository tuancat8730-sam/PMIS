from collections.abc import Mapping

from app.integrations.drive_gateway import DriveEntry


class FakeDriveGateway:
    """Cây Drive trong bộ nhớ, thay cho adapter Google trong test. Không gọi mạng."""

    def __init__(
        self,
        children: Mapping[str, list[DriveEntry]],
        contents: Mapping[str, bytes] | None = None,
    ) -> None:
        self._children = children
        self._contents = dict(contents or {})

    def list_children(self, folder_id: str) -> list[DriveEntry]:
        return list(self._children.get(folder_id, []))

    def download(self, drive_file_id: str) -> bytes:
        return self._contents[drive_file_id]
