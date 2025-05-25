from sqlalchemy import String, Text, Boolean, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from .base import Base
from .leave_request import LeaveRequest
from .leave_quota import LeaveQuota

class LeaveType(Base):
    __tablename__ = "leave_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    requires_attachment: Mapped[bool] = mapped_column(Boolean, server_default="False", nullable=True)
    color_code: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    leave_requests: Mapped[list["LeaveRequest"]] = relationship("LeaveRequest", back_populates="leave_type")
    leave_quotas: Mapped[list["LeaveQuota"]] = relationship("LeaveQuota", back_populates="leave_type", foreign_keys=[LeaveQuota.leave_type_id])  # 使用 foreign_keys 指定外鍵
