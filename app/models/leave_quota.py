from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base



class LeaveQuota(Base):
    __tablename__ = 'leave_quotas'
    __table_args__ = (
        UniqueConstraint('user_id', 'leave_type_id', 'year', name='uq_user_leave_year'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    leave_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('leave_types.id'), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quota: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="leave_quotas")
    leave_type: Mapped["LeaveType"] = relationship("LeaveType", back_populates="leave_quotas")  # 確保與 LeaveType 的 back_populates 一致
