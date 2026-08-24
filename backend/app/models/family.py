import uuid
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Enum as SQLEnum, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import SocialCategoryEnum, RRStatusEnum

if TYPE_CHECKING:
    from app.models.project import Project


class AffectedFamily(Base, TimestampMixin):
    __tablename__ = "affected_families"
    __table_args__ = (
        Index("idx_families_project_rr", "project_id", "rr_status"),
        Index("idx_families_village_category", "village", "category"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    family_reference_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    village: Mapped[str] = mapped_column(String(100), nullable=False)

    category: Mapped[SocialCategoryEnum] = mapped_column(SQLEnum(SocialCategoryEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=SocialCategoryEnum.GENERAL)
    is_affected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_displaced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rr_status: Mapped[RRStatusEnum] = mapped_column(SQLEnum(RRStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=RRStatusEnum.IDENTIFIED, index=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="affected_families")
    rehabilitation_records: Mapped[List["RehabilitationRecord"]] = relationship("RehabilitationRecord", back_populates="family", cascade="all, delete-orphan")


class RehabilitationRecord(Base, TimestampMixin):
    __tablename__ = "rehabilitation_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("affected_families.id", ondelete="CASCADE"), nullable=False, index=True)

    housing_assistance_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    employment_assistance_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    compensation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    resettlement_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")

    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="rehabilitation_records")
    family: Mapped["AffectedFamily"] = relationship("AffectedFamily", back_populates="rehabilitation_records")
