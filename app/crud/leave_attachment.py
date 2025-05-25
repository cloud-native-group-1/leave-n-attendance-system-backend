from sqlalchemy.orm import Session
from ..models.leave_request_attachment import LeaveAttachment

def create_leave_attachment(
    db: Session,
    leave_request_id: int,
    file_name: str,
    file_path: str,
    file_type: str,
    file_size: int,
) -> LeaveAttachment:
    attachment = LeaveAttachment(
        leave_request_id=leave_request_id,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment
