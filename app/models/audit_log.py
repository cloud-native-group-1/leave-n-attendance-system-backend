from sqlalchemy import String, Integer, JSON, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., create, update, delete
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., leave_request
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)  # ID of the affected entity
    details: Mapped[dict] = mapped_column(JSON, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
