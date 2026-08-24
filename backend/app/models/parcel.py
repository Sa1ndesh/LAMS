import uuid
from typing import Optional, List, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, ForeignKey, Enum as SQLEnum, CheckConstraint, UniqueConstraint, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import (
    LandTypeEnum,
    ParcelAcquisitionStatusEnum,
    CompensationStatusEnum,
    PossessionStatusEnum,
)

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.geography import State, District
    from app.models.compensation import CompensationRecord


class LandParcel(Base, TimestampMixin):
    __tablename__ = "land_parcels"
    __table_args__ = (
        UniqueConstraint("project_id", "survey_number", name="uq_parcel_project_survey"),
        CheckConstraint("area_hectares >= 0", name="chk_parcel_area_positive"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="chk_parcel_latitude_bounds"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="chk_parcel_longitude_bounds"),
        Index("idx_parcels_project_survey", "project_id", "survey_number"),
        Index("idx_parcels_village_taluk", "village", "taluk"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    parcel_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    survey_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    state_id: Mapped[int] = mapped_column(Integer, ForeignKey("states.id", ondelete="RESTRICT"), nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id", ondelete="RESTRICT"), nullable=False)
    taluk: Mapped[str] = mapped_column(String(100), nullable=False)
    village: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    area_hectares: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    land_type: Mapped[LandTypeEnum] = mapped_column(SQLEnum(LandTypeEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=LandTypeEnum.AGRICULTURAL)

    acquisition_status: Mapped[ParcelAcquisitionStatusEnum] = mapped_column(SQLEnum(ParcelAcquisitionStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=ParcelAcquisitionStatusEnum.PROPOSED)
    compensation_status: Mapped[CompensationStatusEnum] = mapped_column(SQLEnum(CompensationStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=CompensationStatusEnum.PENDING)
    possession_status: Mapped[PossessionStatusEnum] = mapped_column(SQLEnum(PossessionStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False), nullable=False, default=PossessionStatusEnum.NOT_TAKEN)

    latitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    geometry: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="land_parcels")
    state: Mapped["State"] = relationship("State", back_populates="land_parcels")
    district: Mapped["District"] = relationship("District", back_populates="land_parcels")
    owners: Mapped[List["LandOwner"]] = relationship("LandOwner", back_populates="parcel", cascade="all, delete-orphan")
    compensation_records: Mapped[List["CompensationRecord"]] = relationship("CompensationRecord", back_populates="parcel", cascade="all, delete-orphan")


class LandOwner(Base, TimestampMixin):
    __tablename__ = "land_owners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parcel_id: Mapped[str] = mapped_column(String(36), ForeignKey("land_parcels.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)

    parcel: Mapped["LandParcel"] = relationship("LandParcel", back_populates="owners")
