from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.leave_type import LeaveType as LeaveTypeSchema
from app.crud import leave_type

router = APIRouter(
    prefix="/api/leave-types",
    tags=["leave_types"],
    responses={404: {"description": "Not found"}}
)


@router.get("", response_model=List[LeaveTypeSchema])
def get_leave_types(db: Session = Depends(get_db)):
    """
    Get all leave types
    """
    return leave_type.get_leave_types(db) 
