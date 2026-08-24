import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.geography import State, District
    from app.models.audit import AuditLog


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    state_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("states.id", ondelete="SET NULL"), nullable=True)
    district_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("districts.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    state: Mapped[Optional["State"]] = relationship("State", back_populates="users")
    district: Mapped[Optional["District"]] = relationship("District", back_populates="users")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")
