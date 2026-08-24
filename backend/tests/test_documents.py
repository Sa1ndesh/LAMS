import os
import io
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.models.audit import AuditLog
from app.models.project import Project


@pytest.mark.asyncio
async def test_list_documents_api(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/projects/{project_id}/documents."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    assert proj_res.status_code == 200
    projects = proj_res.json()["items"]
    assert len(projects) > 0
    project_id = projects[0]["id"]

    # Ensure at least one document exists
    pdf_bytes = b"%PDF-1.4 sample content for test list"
    files = {"file": ("List_Test_Order.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data={"category": "PROPOSAL", "description": "List test doc"},
        headers=admin_token_headers,
    )

    res = await async_client.get(f"/api/projects/{project_id}/documents", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_upload_valid_pdf_api(async_client: AsyncClient, admin_token_headers: dict):
    """Test POST /api/projects/{project_id}/documents/upload with PDF and Audit Log verification."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    pdf_bytes = b"%PDF-1.4 sample content for test"
    files = {"file": ("Test_Gazette_Order.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "category": "NOTIFICATIONS",
        "description": "Test gazette order notification",
        "version": "1.0",
    }

    res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    assert res.status_code == 201
    doc = res.json()
    assert doc["document_name"] == "Test_Gazette_Order.pdf"
    assert doc["category"] == "NOTIFICATIONS"
    assert doc["file_size"] == len(pdf_bytes)
    assert doc["mime_type"] == "application/pdf"
    assert doc["file_path"] is not None
    assert os.path.exists(doc["file_path"])

    # Check Audit Log in DB
    async with AsyncSessionLocal() as session:
        audit_res = await session.execute(
            select(AuditLog).where(AuditLog.entity_id == doc["id"], AuditLog.action == "DOCUMENT_UPLOADED")
        )
        audit_entry = audit_res.scalar_one_or_none()
        assert audit_entry is not None
        assert audit_entry.entity_type == "DOCUMENT"


@pytest.mark.asyncio
async def test_upload_valid_docx_api(async_client: AsyncClient, admin_token_headers: dict):
    """Test POST /api/projects/{project_id}/documents/upload with DOCX."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    docx_bytes = b"PK\x03\x04 dummy docx archive content"
    files = {
        "file": (
            "DPR_Proposal.docx",
            io.BytesIO(docx_bytes),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    data = {"category": "PROPOSAL", "description": "Project proposal document"}

    res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    assert res.status_code == 201
    doc = res.json()
    assert doc["document_name"] == "DPR_Proposal.docx"


@pytest.mark.asyncio
async def test_upload_valid_image_api(async_client: AsyncClient, admin_token_headers: dict):
    """Test POST /api/projects/{project_id}/documents/upload with PNG image."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR sample image content"
    files = {"file": ("Land_Map_Survey.png", io.BytesIO(png_bytes), "image/png")}
    data = {"category": "SURVEY", "description": "Cadastral survey map image", "version": "1.1"}

    res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    assert res.status_code == 201
    doc = res.json()
    assert doc["document_name"] == "Land_Map_Survey.png"
    assert doc["category"] == "SURVEY"


@pytest.mark.asyncio
async def test_reject_empty_file(async_client: AsyncClient, admin_token_headers: dict):
    """Test rejecting empty 0-byte file."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    files = {"file": ("Empty_Document.pdf", io.BytesIO(b""), "application/pdf")}
    data = {"category": "PROPOSAL"}

    res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reject_invalid_extension(async_client: AsyncClient, admin_token_headers: dict):
    """Test rejecting dangerous file extension (.exe)."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    exe_bytes = b"MZ executable header dummy content"
    files = {"file": ("malicious_script.exe", io.BytesIO(exe_bytes), "application/octet-stream")}
    data = {"category": "PROPOSAL"}

    res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    assert res.status_code == 400
    assert "not allowed" in res.json()["detail"]


@pytest.mark.asyncio
async def test_reject_oversized_file(async_client: AsyncClient, admin_token_headers: dict):
    """Test rejecting file > 10 MB."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    large_bytes = b"0" * (11 * 1024 * 1024)  # 11 MB
    files = {"file": ("Large_File.pdf", io.BytesIO(large_bytes), "application/pdf")}
    data = {"category": "PROPOSAL"}

    res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    assert res.status_code == 413
    assert "exceeds maximum limit" in res.json()["detail"]


@pytest.mark.asyncio
async def test_unauthenticated_upload(async_client: AsyncClient):
    """Test unauthenticated upload attempt returns 401."""
    files = {"file": ("Unauth_File.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}
    data = {"category": "PROPOSAL"}

    res = await async_client.post(
        "/api/projects/proj-123/documents/upload",
        files=files,
        data=data,
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_download_and_preview_document(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/documents/{id}, GET /api/documents/{id}/download, and GET /api/documents/{id}/preview."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    pdf_bytes = b"%PDF-1.4 Downloadable content test"
    files = {"file": ("Award_Notice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"category": "AWARD"}

    up_res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    assert up_res.status_code == 201
    doc_id = up_res.json()["id"]

    det_res = await async_client.get(f"/api/documents/{doc_id}", headers=admin_token_headers)
    assert det_res.status_code == 200
    assert det_res.json()["document_name"] == "Award_Notice.pdf"

    dl_res = await async_client.get(f"/api/documents/{doc_id}/download", headers=admin_token_headers)
    assert dl_res.status_code == 200
    assert dl_res.content == pdf_bytes
    assert "attachment" in dl_res.headers["content-disposition"]

    prev_res = await async_client.get(f"/api/documents/{doc_id}/preview", headers=admin_token_headers)
    assert prev_res.status_code == 200
    assert "inline" in prev_res.headers["content-disposition"]


@pytest.mark.asyncio
async def test_missing_physical_file_handling(async_client: AsyncClient, admin_token_headers: dict):
    """Test downloading document when physical file is missing returns 404."""
    async with AsyncSessionLocal() as session:
        proj = (await session.execute(select(Project))).scalars().first()
        fake_doc = Document(
            project_id=proj.id,
            document_name="Nonexistent_File.pdf",
            category="PROPOSAL",
            file_reference="fake.pdf",
            file_path="C:\\nonexistent\\path\\fake.pdf",
            mime_type="application/pdf",
            uploaded_by="Test System",
        )
        session.add(fake_doc)
        await session.commit()
        await session.refresh(fake_doc)
        fake_doc_id = fake_doc.id

    res = await async_client.get(f"/api/documents/{fake_doc_id}/download", headers=admin_token_headers)
    assert res.status_code == 404
    assert "missing" in res.json()["detail"]


@pytest.mark.asyncio
async def test_delete_document_api(async_client: AsyncClient, admin_token_headers: dict):
    """Test DELETE /api/documents/{id}."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    pdf_bytes = b"%PDF-1.4 To be deleted content"
    files = {"file": ("Temporary_Doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"category": "PROPOSAL"}

    up_res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files=files,
        data=data,
        headers=admin_token_headers,
    )
    doc_data = up_res.json()
    doc_id = doc_data["id"]
    file_path = doc_data["file_path"]

    assert os.path.exists(file_path)

    del_res = await async_client.delete(f"/api/documents/{doc_id}", headers=admin_token_headers)
    assert del_res.status_code == 204

    assert not os.path.exists(file_path)

    det_res = await async_client.get(f"/api/documents/{doc_id}", headers=admin_token_headers)
    assert det_res.status_code == 404

    # Verify Audit Log
    async with AsyncSessionLocal() as session:
        audit_res = await session.execute(
            select(AuditLog).where(AuditLog.entity_id == doc_id, AuditLog.action == "DOCUMENT_DELETED")
        )
        audit_entry = audit_res.scalar_one_or_none()
        assert audit_entry is not None
