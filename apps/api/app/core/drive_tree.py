"""Duyệt cây Drive và lập kế hoạch đồng bộ (thuần, không chạm DB hay mạng).

`walk_tree` chỉ đi qua cổng `DriveGateway`. `plan_sync` so sánh ảnh chụp với bản ghi đã có
theo `drive_file_id` để quyết định tạo mới hay cập nhật, nên chạy lại nhiều lần vẫn idempotent.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.drive_file_kinds import classify_file
from app.integrations.drive_gateway import DriveEntry, DriveGateway

MAX_TREE_DEPTH = 10
PATH_SEPARATOR = "/"


@dataclass(frozen=True)
class DriveFileSnapshot:
    """Ảnh chụp một file Drive đã qua bộ lọc định dạng, sẵn sàng để so sánh và ghi."""

    drive_file_id: str
    drive_parent_id: str | None
    file_name: str
    drive_path: str
    mime_type: str
    file_size: int | None
    web_view_link: str | None
    modified_time: datetime


@dataclass(frozen=True)
class SyncPlan:
    to_create: list[DriveFileSnapshot] = field(default_factory=list)
    to_update: list[DriveFileSnapshot] = field(default_factory=list)


def walk_tree(
    gateway: DriveGateway,
    root_folder_id: str,
    max_depth: int = MAX_TREE_DEPTH,
) -> list[DriveFileSnapshot]:
    """Duyệt đệ quy thư mục gốc, trả về các file hỗ trợ kèm đường dẫn tương đối.

    Giới hạn độ sâu và bỏ qua thư mục đã thăm để tránh vòng lặp do thư mục tham chiếu chính nó.
    """
    visited: set[str] = {root_folder_id}
    snapshots: list[DriveFileSnapshot] = []
    _collect(gateway, root_folder_id, "", 0, max_depth, visited, snapshots)
    return snapshots


def _collect(
    gateway: DriveGateway,
    folder_id: str,
    prefix: str,
    depth: int,
    max_depth: int,
    visited: set[str],
    snapshots: list[DriveFileSnapshot],
) -> None:
    for entry in gateway.list_children(folder_id):
        if entry.is_folder:
            _descend_if_allowed(gateway, entry, prefix, depth, max_depth, visited, snapshots)
            continue
        if classify_file(entry.name) is None:
            continue
        snapshots.append(_to_snapshot(entry, prefix))


def _descend_if_allowed(
    gateway: DriveGateway,
    folder: DriveEntry,
    prefix: str,
    depth: int,
    max_depth: int,
    visited: set[str],
    snapshots: list[DriveFileSnapshot],
) -> None:
    if depth >= max_depth or folder.drive_file_id in visited:
        return
    visited.add(folder.drive_file_id)
    child_prefix = _join(prefix, folder.name)
    _collect(gateway, folder.drive_file_id, child_prefix, depth + 1, max_depth, visited, snapshots)


def _to_snapshot(entry: DriveEntry, prefix: str) -> DriveFileSnapshot:
    return DriveFileSnapshot(
        drive_file_id=entry.drive_file_id,
        drive_parent_id=entry.parent_id,
        file_name=entry.name,
        drive_path=_join(prefix, entry.name),
        mime_type=entry.mime_type,
        file_size=entry.size,
        web_view_link=entry.web_view_link,
        modified_time=datetime.fromisoformat(entry.modified_time),
    )


def _join(prefix: str, name: str) -> str:
    return name if not prefix else f"{prefix}{PATH_SEPARATOR}{name}"


def plan_sync(
    existing: Mapping[str, Mapping[str, Any]],
    snapshots: list[DriveFileSnapshot],
) -> SyncPlan:
    """Phân loại từng snapshot thành tạo mới hoặc cập nhật.

    `existing` ánh xạ `drive_file_id` tới các trường đã lưu (`file_name`, `drive_path`,
    `modified_time`). File không đổi thì bỏ qua, nên lần quét lặp lại không ghi gì thêm.
    """
    to_create: list[DriveFileSnapshot] = []
    to_update: list[DriveFileSnapshot] = []
    for snapshot in snapshots:
        stored = existing.get(snapshot.drive_file_id)
        if stored is None:
            to_create.append(snapshot)
        elif _has_changed(stored, snapshot):
            to_update.append(snapshot)
    return SyncPlan(to_create=to_create, to_update=to_update)


def _has_changed(stored: Mapping[str, Any], snapshot: DriveFileSnapshot) -> bool:
    return (
        stored["file_name"] != snapshot.file_name
        or stored["drive_path"] != snapshot.drive_path
        or stored["modified_time"] != snapshot.modified_time
    )
