from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import leave_attachment as leave_attachment_crud
from ..models.leave_request import LeaveRequest
from ..models.leave_request_attachment import LeaveAttachment
from ..utils.gcs import upload_file_to_gcs
from ..utils.dependencies import get_current_user
from ..schemas.leave_attachment import LeaveAttachmentOut, LeaveAttachmentResult, LeaveAttachmentListResult
from ..models.user import User

router = APIRouter(
    prefix="/api/leave-requests",
    tags=["leave-attachments"]
)

BUCKET_NAME = "leave_system_attachments_test"  # 改成你的 Bucket 名稱

@router.post("/{leave_request_id}/attachments", response_model=LeaveAttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    leave_request_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 檢查請假單是否存在
    leave_request = db.query(LeaveRequest).filter_by(id=leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # 權限檢查（只能上傳自己請假的附件）
    if leave_request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload attachment for this leave request")
    
    # 確保檔案指標從頭開始
    file.file.seek(0)
    print(f"Uploading file: {file.filename} to GCS bucket: {BUCKET_NAME}")
    file_url = upload_file_to_gcs(file, BUCKET_NAME)

    # 讀取檔案內容以取得大小
    file.file.seek(0)
    content = await file.read()
    file_size = len(content)
    print(f"File size: {file_size} bytes")

    # 建立資料庫紀錄
    print(f"Creating leave attachment record in database for file: {file.filename}")
    attachment = leave_attachment_crud.create_leave_attachment(
        db=db,
        leave_request_id=leave_request_id,
        file_name=file.filename,
        file_path=file_url,
        file_type=file.content_type,
        file_size=file_size
    )
    if not attachment:
        raise HTTPException(status_code=500, detail="Failed to save attachment to database")
    print(f"Attachment record created with ID: {attachment.id}")

    return {
        "id": attachment.id,
        "leave_request_id": leave_request_id,
        "file_name": attachment.file_name,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,
        "uploaded_at": attachment.uploaded_at.isoformat()
    }
@router.get("/{leave_request_id}/attachments", response_model=LeaveAttachmentListResult, status_code=status.HTTP_200_OK)
def get_attachments_for_leave_request(
    leave_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 查詢該請假申請的附件
    leave_request = db.query(LeaveRequest).filter_by(id=leave_request_id).first()
    print(f"Fetching attachments for leave request ID: {leave_request_id}")
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # 查詢該請假申請下的所有附件
    attachments = db.query(LeaveAttachment).filter_by(leave_request_id=leave_request_id).all()

    # 將附件轉換為回應格式
    attachment_results = []
    for attachment in attachments:
        attachment_results.append({
            "id": attachment.id,
            "leave_request_id": leave_request_id,
            "file_name": attachment.file_name,
            "file_type": attachment.file_type,
            "file_size": attachment.file_size,
            "file_path": attachment.file_path,
            "uploaded_at": attachment.uploaded_at.isoformat()
        })
    
    return {
        "attachments": attachment_results,
        "total_count": len(attachment_results)
    }