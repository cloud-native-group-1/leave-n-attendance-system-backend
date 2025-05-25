from sqlalchemy.orm import Session
from app.models.leave_type import LeaveType
from typing import List, Optional


def get_leave_types(db: Session) -> List[LeaveType]:
    """
    Get all leave types
    """
    return db.query(LeaveType).all()


def get_leave_type(db: Session, leave_type_id: int) -> Optional[LeaveType]:
    """
    Get a leave type by ID
    """
    return db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()


def get_leave_type_by_name(db: Session, name: str) -> Optional[LeaveType]:
    """
    Get a leave type by name
    """
    return db.query(LeaveType).filter(LeaveType.name == name).first()


def create_leave_type(db: Session, name: str, color_code: str) -> LeaveType:
    """
    Create a new leave type
    """
    db_leave_type = LeaveType(name=name, color_code=color_code)
    db.add(db_leave_type)
    db.commit()
    db.refresh(db_leave_type)
    return db_leave_type


def update_leave_type(
    db: Session, leave_type_id: int, name: Optional[str] = None, color_code: Optional[str] = None
) -> Optional[LeaveType]:
    """
    Update a leave type
    """
    db_leave_type = get_leave_type(db, leave_type_id)
    if not db_leave_type:
        return None
    
    if name is not None:
        db_leave_type.name = name
    if color_code is not None:
        db_leave_type.color_code = color_code
    
    db.commit()
    db.refresh(db_leave_type)
    return db_leave_type


def delete_leave_type(db: Session, leave_type_id: int) -> bool:
    """
    Delete a leave type
    """
    db_leave_type = get_leave_type(db, leave_type_id)
    if not db_leave_type:
        return False
    
    db.delete(db_leave_type)
    db.commit()
    return True 