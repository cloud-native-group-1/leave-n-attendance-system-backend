from pydantic import BaseModel, Field
from typing import Optional


class LeaveTypeBase(BaseModel):
    """Base schema for leave type"""
    name: str = Field(..., description="Name of the leave type")
    color_code: str = Field(..., description="Color code for UI representation")


class LeaveTypeCreate(LeaveTypeBase):
    """Schema for creating a leave type"""
    pass


class LeaveTypeUpdate(BaseModel):
    """Schema for updating a leave type"""
    name: Optional[str] = Field(None, description="Name of the leave type")
    color_code: Optional[str] = Field(None, description="Color code for UI representation")


class LeaveType(LeaveTypeBase):
    """Schema for a leave type response"""
    id: int = Field(..., description="Unique identifier for the leave type")

    class Config:
        orm_mode = True 