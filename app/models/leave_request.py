from sqlalchemy import String, Text, Boolean, Date, DECIMAL, Enum, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from typing import Optional
from enum import Enum as PyEnum
from .base import Base


class LeaveStatus(PyEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    leave_type_id: Mapped[int] = mapped_column(ForeignKey("leave_types.id"), nullable=False)
    proxy_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, server_default="1")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_half_day: Mapped[bool] = mapped_column(Boolean, server_default="False", nullable=False)
    end_half_day: Mapped[bool] = mapped_column(Boolean, server_default="False", nullable=False)
    days_count: Mapped[float] = mapped_column(DECIMAL(5, 1), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    # status: Mapped[LeaveStatus] = mapped_column(Enum(LeaveStatus), server_default="Pending", nullable=False)
    status: Mapped[str] = mapped_column(Text, server_default="Pending", nullable=False)
    approver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column()
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="leave_requests", foreign_keys=[user_id])
    proxy_user: Mapped["User"] = relationship("User", back_populates="proxy_requests", foreign_keys=[proxy_user_id])
    approver: Mapped["User"] = relationship("User", back_populates="approvals", foreign_keys=[approver_id])
    leave_type: Mapped["LeaveType"] = relationship("LeaveType", back_populates="leave_requests")
    attachments: Mapped[list["LeaveAttachment"]] = relationship("LeaveAttachment", back_populates="leave_request", cascade="all, delete-orphan")
