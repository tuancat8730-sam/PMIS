from datetime import UTC, datetime

import pytest

from app.core.drive_tree import plan_sync, walk_tree
from app.integrations.drive_gateway import DriveEntry
from tests.fakes.fake_drive_gateway import FakeDriveGateway

pytestmark = pytest.mark.unit

ROOT = "root-folder"
FOLDER_MIME = "application/vnd.google-apps.folder"


def _file(
    file_id: str,
    name: str,
    parent: str,
    modified: str = "2026-10-01T00:00:00Z",
) -> DriveEntry:
    return DriveEntry(
        drive_file_id=file_id,
        parent_id=parent,
        name=name,
        mime_type="application/pdf",
        size=100,
        web_view_link=f"https://drive.example/{file_id}",
        modified_time=modified,
        is_folder=False,
    )


def _folder(folder_id: str, name: str, parent: str) -> DriveEntry:
    return DriveEntry(
        drive_file_id=folder_id,
        parent_id=parent,
        name=name,
        mime_type=FOLDER_MIME,
        size=None,
        web_view_link=None,
        modified_time="2026-10-01T00:00:00Z",
        is_folder=True,
    )


def test_walk_returns_files_with_slash_joined_paths_and_skips_folder_entries() -> None:
    # Arrange
    gateway = FakeDriveGateway(
        {
            ROOT: [_folder("f1", "5.Nghiem thu", ROOT), _file("a", "tong_hop.pdf", ROOT)],
            "f1": [_file("b", "bien_ban.docx", "f1")],
        }
    )

    # Act
    entries = walk_tree(gateway, ROOT)

    # Assert
    assert sorted((entry.drive_file_id, entry.drive_path) for entry in entries) == [
        ("a", "tong_hop.pdf"),
        ("b", "5.Nghiem thu/bien_ban.docx"),
    ]


def test_walk_stops_descending_at_max_depth() -> None:
    # Arrange
    gateway = FakeDriveGateway(
        {
            ROOT: [_folder("deep", "sau", ROOT)],
            "deep": [_file("x", "x.pdf", "deep")],
        }
    )

    # Act
    entries = walk_tree(gateway, ROOT, max_depth=0)

    # Assert
    assert entries == []


def test_walk_does_not_revisit_folders_when_a_cycle_exists() -> None:
    # Arrange
    gateway = FakeDriveGateway(
        {
            ROOT: [_folder("f1", "a", ROOT)],
            "f1": [_folder(ROOT, "quay_lai", "f1"), _file("c", "c.pdf", "f1")],
        }
    )

    # Act
    entries = walk_tree(gateway, ROOT)

    # Assert
    assert [entry.drive_file_id for entry in entries] == ["c"]


def test_walk_drops_unsupported_file_types() -> None:
    # Arrange
    gateway = FakeDriveGateway(
        {ROOT: [_file("t", "ghi_chu.txt", ROOT), _file("p", "ok.pdf", ROOT)]}
    )

    # Act
    entries = walk_tree(gateway, ROOT)

    # Assert
    assert [entry.drive_file_id for entry in entries] == ["p"]


def test_plan_creates_new_files_and_leaves_unchanged_ones_alone() -> None:
    # Arrange
    unchanged = _file("a", "tong_hop.pdf", ROOT)
    walked = [
        walk_entry
        for walk_entry in walk_tree(
            FakeDriveGateway({ROOT: [unchanged, _file("b", "moi.pdf", ROOT)]}), ROOT
        )
    ]
    existing = {
        "a": {
            "file_name": "tong_hop.pdf",
            "drive_path": "tong_hop.pdf",
            "modified_time": datetime(2026, 10, 1, tzinfo=UTC),
        }
    }

    # Act
    plan = plan_sync(existing, walked)

    # Assert
    assert [entry.drive_file_id for entry in plan.to_create] == ["b"]
    assert plan.to_update == []


def test_plan_updates_renamed_file_without_creating_duplicate() -> None:
    # Arrange
    existing = {
        "a": {
            "file_name": "cu.pdf",
            "drive_path": "cu.pdf",
            "modified_time": datetime(2026, 9, 1, tzinfo=UTC),
        }
    }
    renamed = walk_tree(
        FakeDriveGateway({ROOT: [_file("a", "moi.pdf", ROOT, modified="2026-10-05T00:00:00Z")]}),
        ROOT,
    )

    # Act
    plan = plan_sync(existing, renamed)

    # Assert
    assert plan.to_create == []
    assert [entry.drive_file_id for entry in plan.to_update] == ["a"]
