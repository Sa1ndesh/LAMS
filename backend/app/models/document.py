import uuid
from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Date, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import DocumentCategoryEnum

if TYPE_CHECKING:
    from app.models.project import Project


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_docs_project_category", "project_id", "category"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[DocumentCategoryEnum] = mapped_column(SQLEnum(DocumentCategoryEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, index=True)
    file_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Verified")

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
