import pytest

from app.core.drive_upload_targets import UploadKind, target_folder_path

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("kind", "folder"),
    [
        (UploadKind.WEEKLY_REPORT, "Báo cáo tuần (pmis)"),
        (UploadKind.HANDOVER_MINUTES, "Biên bản bàn giao (pmis)"),
        (UploadKind.CONTRACT, "Hợp đồng (pmis)"),
        (UploadKind.FIELD_PHOTO, "Ảnh hiện trường (pmis)"),
    ],
)
def test_each_upload_kind_targets_its_pmis_storage_folder(kind: UploadKind, folder: str) -> None:
    # Arrange
    # Act
    path = target_folder_path(kind)

    # Assert
    assert path == (folder,)


def test_every_upload_kind_has_a_target_folder() -> None:
    # Arrange
    # Act / Assert
    for kind in UploadKind:
        assert target_folder_path(kind)
