from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from ..models.notification import Notification
from ..schemas.notification import NotificationBase, PaginationMeta, NotificationReadResponse, NotificationReadAllResponse
from fastapi import HTTPException


def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    page: int = 1,
    per_page: int = 10
) -> Dict[str, Any]:
    # Build the base query
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    # Apply unread filter if specified
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    notifications = query.order_by(Notification.created_at.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()
    
    # Convert to response format
    notification_list = [
        NotificationBase(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            related_to=notification.related_to,
            related_id=notification.related_id,
            is_read=notification.is_read,
            created_at=notification.created_at
        )
        for notification in notifications
    ]
    
    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "notifications": notification_list,
        "pagination": PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    }


def mark_notification_as_read(
    db: Session,
    notification_id: int,
    user_id: int
) -> NotificationReadResponse:
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    
    return NotificationReadResponse(
        id=notification.id,
        is_read=notification.is_read
    )


def mark_all_notifications_as_read(
    db: Session,
    user_id: int
) -> NotificationReadAllResponse:
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return NotificationReadAllResponse(
        message="All notifications marked as read",
        count=result
    )

def create_notifications(
        db: Session,
        receiver_id: int,
        title: str,
        message: str,
        leave_request_id: int
):
    new_notification = Notification(
        user_id = receiver_id,
        title = title,
        message = message,
        related_to = "leave_request",
        related_id = leave_request_id,
        is_read = False
    ) 
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
