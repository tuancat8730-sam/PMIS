from collections.abc import Mapping

from app.integrations.drive_gateway import DriveEntry


class FakeDriveGateway:
    """Cây Drive trong bộ nhớ, thay cho adapter Google trong test. Không gọi mạng."""

    def __init__(self, children: Mapping[str, list[DriveEntry]]) -> None:
        self._children = children

    def list_children(self, folder_id: str) -> list[DriveEntry]:
        return list(self._children.get(folder_id, []))
