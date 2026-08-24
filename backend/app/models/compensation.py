import uuid
from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Date, ForeignKey, Enum as SQLEnum, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import PaymentStatusEnum

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.parcel import LandParcel


class CompensationRecord(Base, TimestampMixin):
    __tablename__ = "compensation_records"
    __table_args__ = (
        CheckConstraint("assessed_amount_inr >= 0", name="chk_comp_assessed_positive"),
        CheckConstraint("approved_amount_inr >= 0", name="chk_comp_approved_positive"),
        CheckConstraint("disbursed_amount_inr >= 0", name="chk_comp_disbursed_positive"),
        CheckConstraint("disbursed_amount_inr <= approved_amount_inr", name="chk_comp_disbursed_le_approved"),
        Index("idx_comp_project_status", "project_id", "payment_status"),
        Index("idx_comp_parcel_status", "parcel_id", "payment_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    parcel_id: Mapped[str] = mapped_column(String(36), ForeignKey("land_parcels.id", ondelete="CASCADE"), nullable=False, index=True)

    assessed_amount_inr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    approved_amount_inr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    disbursed_amount_inr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    payment_status: Mapped[PaymentStatusEnum] = mapped_column(SQLEnum(PaymentStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=PaymentStatusEnum.ASSESSED, index=True)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="compensation_records")
    parcel: Mapped["LandParcel"] = relationship("LandParcel", back_populates="compensation_records")

    @property
    def pending_amount_inr(self) -> float:
        """Calculated pending amount (approved - disbursed)."""
        return max(0.0, self.approved_amount_inr - self.disbursed_amount_inr)
