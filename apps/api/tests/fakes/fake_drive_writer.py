from collections.abc import Mapping
from dataclasses import dataclass, field

from app.integrations.drive_gateway import DriveEntry, UpsertResult

FILE_MIME = "application/octet-stream"


@dataclass
class FakeDriveWriter:
    """Cây Drive trong bộ nhớ có ghi được, không gọi mạng. File đã đẩy lên nằm trong `uploads`."""

    tree: Mapping[str, list[DriveEntry]]
    uploads: dict[tuple[str, str], tuple[str, bytes]] = field(default_factory=dict)
    _next_id: int = 0

    def find_child(self, folder_id: str, name: str) -> DriveEntry | None:
        for entry in self.tree.get(folder_id, []):
            if entry.name == name:
                return entry
        uploaded = self.uploads.get((folder_id, name))
        if uploaded is None:
            return None
        return DriveEntry(
            drive_file_id=uploaded[0],
            parent_id=folder_id,
            name=name,
            mime_type=FILE_MIME,
            size=len(uploaded[1]),
            web_view_link=None,
            modified_time="2026-11-01T00:00:00Z",
            is_folder=False,
        )

    def upsert_file(
        self, folder_id: str, name: str, content: bytes, mime_type: str
    ) -> UpsertResult:
        key = (folder_id, name)
        if key in self.uploads:
            file_id, _ = self.uploads[key]
            self.uploads[key] = (file_id, content)
            return UpsertResult(file_id=file_id, created=False)
        self._next_id += 1
        file_id = f"new-file-{self._next_id}"
        self.uploads[key] = (file_id, content)
        return UpsertResult(file_id=file_id, created=True)
