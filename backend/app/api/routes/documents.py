import os
import logging
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.audit import AuditLog
from app.models.enums import UserRoleEnum, DocumentCategoryEnum
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.storage import save_uploaded_file, delete_physical_file

logger = logging.getLogger("lams.api.documents")
router = APIRouter(tags=["Documents"])


def to_document_response(doc: Document) -> DocumentResponse:
    cat_str = doc.category.value if hasattr(doc.category, "value") else str(doc.category)
    return DocumentResponse(
        id=doc.id,
        project_id=doc.project_id,
        document_name=doc.document_name,
        category=cat_str,
        file_reference=doc.file_reference or doc.stored_file_name or "document.pdf",
        stored_file_name=doc.stored_file_name,
        file_path=doc.file_path,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        description=doc.description,
        version=doc.version or "1.0",
        uploaded_by=doc.uploaded_by,
        upload_date=doc.upload_date,
        status=doc.status,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/projects/{project_id}/documents", response_model=DocumentListResponse)
async def list_project_documents(
    project_id: str,
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List official documents for a project with optional search and category filter."""
    stmt = select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())

    if search:
        s_term = f"%{search.strip()}%"
        stmt = stmt.where(Document.document_name.ilike(s_term) | Document.description.ilike(s_term))

    if category and category.upper() != "ALL":
        stmt = stmt.where(Document.category == category)

    res = await session.execute(stmt)
    docs = res.scalars().all()

    items = [to_document_response(d) for d in docs]
    return DocumentListResponse(items=items, total=len(items))


@router.post("/projects/{project_id}/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    project_id: str,
    file: UploadFile = File(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    version: Optional[str] = Form("1.0"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.STATE_AUTHORITY,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
            UserRoleEnum.FIELD_OFFICER,
            UserRoleEnum.PROJECT_IMPLEMENTING_AGENCY,
        )
    ),
):
    """Upload physical document file with validation, security storage, and audit logging."""
    # 1. Verify project exists
    proj_res = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    # 2. Save physical file via Storage Service
    contents = await file.read()
    stored_name, full_path, ext, size_bytes = save_uploaded_file(project_id, category, file, contents)

    mime_type = file.content_type or f"application/{ext.lstrip('.')}"

    # 3. Create Document DB Record
    doc = Document(
        project_id=project_id,
        document_name=file.filename or "uploaded_document.pdf",
        category=category,
        file_reference=stored_name,
        stored_file_name=stored_name,
        file_path=full_path,
        mime_type=mime_type,
        file_size=size_bytes,
        description=description,
        version=version or "1.0",
        uploaded_by=current_user.name,
        upload_date=date.today(),
        status="Verified",
    )
    session.add(doc)
    await session.flush()

    # 4. Audit Log Entry
    audit = AuditLog(
        user_id=current_user.id,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="DOCUMENT_UPLOADED",
        new_value={
            "document_name": doc.document_name,
            "category": category,
            "file_size": size_bytes,
            "stored_file_name": stored_name,
        },
    )
    session.add(audit)
    await session.commit()
    await session.refresh(doc)

    return to_document_response(doc)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document_detail(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve document metadata by ID."""
    res = await session.execute(select(Document).where(Document.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return to_document_response(doc)


@router.get("/documents/{document_id}/download")
async def download_document_file(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Download physical document file."""
    res = await session.execute(select(Document).where(Document.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical document file missing on server storage.")

    # Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="DOCUMENT_DOWNLOADED",
    )
    session.add(audit)
    await session.commit()

    return FileResponse(
        path=doc.file_path,
        filename=doc.document_name,
        media_type=doc.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.document_name}"'},
    )


@router.get("/documents/{document_id}/preview")
async def preview_document_file(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Stream PDF or image document inline for browser preview."""
    res = await session.execute(select(Document).where(Document.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical document file missing on server storage.")

    mime = doc.mime_type or "application/pdf"
    disposition = "inline" if ("pdf" in mime or "image" in mime) else "attachment"

    return FileResponse(
        path=doc.file_path,
        filename=doc.document_name,
        media_type=mime,
        headers={"Content-Disposition": f'{disposition}; filename="{doc.document_name}"'},
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_file(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.STATE_AUTHORITY,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """Delete document metadata, physical file, and record audit log. (Viewer role forbidden)."""
    res = await session.execute(select(Document).where(Document.id == document_id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    old_info = {
        "document_name": doc.document_name,
        "category": str(doc.category),
        "file_path": doc.file_path,
    }

    # Delete physical file gracefully
    if doc.file_path:
        delete_physical_file(doc.file_path)

    # Create Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="DOCUMENT_DELETED",
        old_value=old_info,
    )
    session.add(audit)

    await session.delete(doc)
    await session.commit()
    return None
