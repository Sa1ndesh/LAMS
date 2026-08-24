from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.parcel import LandParcel


class State(Base, TimestampMixin):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)

    districts: Mapped[List["District"]] = relationship("District", back_populates="state", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship("User", back_populates="state")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="state")
    land_parcels: Mapped[List["LandParcel"]] = relationship("LandParcel", back_populates="state")


class District(Base, TimestampMixin):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("state_id", "code", name="uq_district_state_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(Integer, ForeignKey("states.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)

    state: Mapped["State"] = relationship("State", back_populates="districts")
    users: Mapped[List["User"]] = relationship("User", back_populates="district")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="district")
    land_parcels: Mapped[List["LandParcel"]] = relationship("LandParcel", back_populates="district")

