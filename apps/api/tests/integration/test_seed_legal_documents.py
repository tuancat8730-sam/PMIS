import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.db.seed_real_projects import seed_hcm_project, seed_lam_dong_project
from app.models.legal_document import DocMaturityStatus, LegalDocument, LegalPhaseGroup
from app.models.project import Project

pytestmark = pytest.mark.integration

HCM_LEGAL_DOCUMENT_COUNT = 82
LAM_DONG_LEGAL_DOCUMENT_COUNT = 35
LAM_DONG_CODE = "SGD-LD-TB10-2026"


async def test_seed_creates_lam_dong_legal_index_with_mapped_status(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_lam_dong_project(session_factory)

    # Assert
    async with session_factory() as session:
        project = (
            await session.execute(select(Project).where(Project.code == LAM_DONG_CODE))
        ).scalar_one()
        documents = (
            (
                await session.execute(
                    select(LegalDocument).where(LegalDocument.project_id == project.id)
                )
            )
            .scalars()
            .all()
        )
    by_stt = {document.stt: document for document in documents}
    assert len(documents) == LAM_DONG_LEGAL_DOCUMENT_COUNT
    assert by_stt[3].maturity_status == DocMaturityStatus.MISSING
    assert by_stt[4].maturity_status == DocMaturityStatus.SIGNED_SCAN_PDF
    assert by_stt[1].phase_group == LegalPhaseGroup.BIDDING
    assert by_stt[35].phase_group == LegalPhaseGroup.ACCEPTANCE
    assert str(by_stt[31].issue_date) == "2027-02-08"


async def test_seed_creates_hcm_legal_documents_with_mapped_status(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        documents = (await session.execute(select(LegalDocument))).scalars().all()
    by_stt = {document.stt: document for document in documents}
    assert len(documents) == HCM_LEGAL_DOCUMENT_COUNT
    assert by_stt[1].maturity_status == DocMaturityStatus.MISSING
    assert by_stt[29].maturity_status == DocMaturityStatus.SIGNED_SCAN_PDF
    assert by_stt[22].maturity_status == DocMaturityStatus.DRAFT_DOCX
    assert by_stt[59].maturity_status == DocMaturityStatus.DISCREPANCY_FOUND
    assert by_stt[67].phase_group == LegalPhaseGroup.CONTRACT_KICKOFF
    assert str(by_stt[1].issue_date) == "2025-08-20"
    assert by_stt[49].issue_date is None


async def test_running_seed_twice_does_not_duplicate_legal_documents(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory
    await seed_hcm_project(session_factory)

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        document_count = await session.scalar(select(func.count()).select_from(LegalDocument))
    assert document_count == HCM_LEGAL_DOCUMENT_COUNT
