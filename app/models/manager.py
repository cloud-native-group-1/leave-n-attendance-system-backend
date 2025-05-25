from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Manager(Base):
    __tablename__ = 'managers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)  # 員工ID
    manager_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)  # 上司ID

    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='manager_relations')
    manager: Mapped["User"] = relationship('User', foreign_keys=[manager_id], back_populates='subordinate_relations')
