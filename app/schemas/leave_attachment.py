from pydantic import BaseModel
from datetime import datetime
from typing import List

class LeaveAttachmentOut(BaseModel):
    id: int
    leave_request_id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: datetime

    class Config:
        orm_mode = True

class LeaveAttachmentResult(BaseModel):
    id: int
    leave_request_id: int
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    uploaded_at: datetime

    class Config:
        orm_mode = True

class LeaveAttachmentListResult(BaseModel):
    attachments: List[LeaveAttachmentResult]
    total_count: int

    class Config:
        orm_mode = True