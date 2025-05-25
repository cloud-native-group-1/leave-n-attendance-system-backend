from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from fastapi import HTTPException
from datetime import datetime, date
from ..models.leave_request import LeaveRequest, LeaveStatus
from ..models.user import User
from ..models.leave_type import LeaveType
from ..models.leave_quota import LeaveQuota 
from ..models.manager import Manager
from ..schemas.leave import LeaveRequestDetail, LeaveRequestCreate, LeaveRequestOut, LeaveRequestListItem, LeaveTypeBasic, ProxyUserOut, LeaveRequestTeamItem, LeaveRequestApprovalResponse, LeaveRequestRejectionResponse
from uuid import uuid4

ALLOWED_STATUSES = {"pending", "approved", "rejected"}

def generate_request_id():
    id = str(uuid4().hex[:16].upper())
    return id

def calculate_leave_days_excluding_weekends(start_date: date, end_date: date) -> int:
    if start_date > end_date:
        raise ValueError("Invalid date: End_date should be after Start_day") 

    total_days = (end_date - start_date).days + 1
    full_weeks = total_days // 7
    weekend_days = full_weeks * 2

    extra_days = total_days % 7
    start_weekday = start_date.weekday()

    for i in range(extra_days):
        if (start_weekday + i) % 7 >= 5:  # 週六或週日
            weekend_days += 1

    return total_days - weekend_days


def create_leave_request(db: Session, user_id: int, data: LeaveRequestCreate):
    # 計算請假天數（整天制）
    # days_requested = (data.end_date - data.start_date).days + 1
    days_requested = calculate_leave_days_excluding_weekends(data.start_date, data.end_date)
    current_year = datetime.now().year
    if days_requested <= 0:
        raise ValueError("Invalid date: End_date should be after Start_day") 

    # get leave_type
    leave_type = db.query(LeaveType).filter(LeaveType.id == data.leave_type_id).first()
    if not leave_type: 
        raise ValueError("Invalid leave_type_id")

    # check proxy
    proxy_user = db.query(User).filter(User.id == data.proxy_user_id).first()
    if not proxy_user:
        raise ValueError("Invalid leave_type_id or proxy_user_id")

    # check quota per year
    quota = db.query(LeaveQuota).filter_by(
        user_id=user_id,
        leave_type_id=data.leave_type_id,
        year=current_year
    ).first()
    if not quota:
        raise ValueError("No leave quota found for this leave type")
    
    # calculate remaining quota
    approved_requests = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.leave_type_id == data.leave_type_id,
            func.extract('year', LeaveRequest.start_date) == current_year,
            LeaveRequest.status == 'approved'
        )
        .all()
    )

    used_days = sum([r.days_count for r in approved_requests])
    remaining_days = quota.quota - used_days
    if remaining_days < days_requested:
        raise ValueError(f"Not enough leave balance. Remaining: {remaining_days}, Requested: {days_requested}")

    new_request = LeaveRequest(
        request_id = generate_request_id(),
        user_id = user_id,
        leave_type_id = data.leave_type_id,
        start_date = data.start_date,
        end_date = data.end_date,
        days_count = days_requested,
        reason = data.reason,
        proxy_user_id = data.proxy_user_id,
        status="pending",
        created_at=datetime.utcnow()
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    db.refresh(leave_type)
    db.refresh(proxy_user)
    return LeaveRequestOut(
        id = new_request.id,
        request_id = new_request.request_id,
        leave_type = leave_type,
        start_date = new_request.start_date,
        end_date = new_request.end_date,
        days_count = new_request.days_count,
        reason = new_request.reason,
        status = new_request.status,
        proxy_person = proxy_user,
        created_at = new_request.created_at
    )


def get_leave_requests_for_user(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    leave_type_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 10
):
    if status and status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: '{status}'. Must be one of {ALLOWED_STATUSES}")
    
    query = db.query(LeaveRequest).options(
        joinedload(LeaveRequest.leave_type),
        joinedload(LeaveRequest.proxy_user),
        joinedload(LeaveRequest.approver)
    ).filter(LeaveRequest.user_id == user_id)

    if status:
        query = query.filter(LeaveRequest.status == status)

    if start_date:
        query = query.filter(LeaveRequest.start_date >= start_date)

    if end_date:
        query = query.filter(LeaveRequest.end_date <= end_date)
        
    if leave_type_id:
        query = query.filter(LeaveRequest.leave_type_id == leave_type_id)

    total = query.count()
    results = query.order_by(LeaveRequest.start_date.desc()) \
        .offset((page - 1) * per_page).limit(per_page).all()

    items = []

    for req in results:
        items.append(LeaveRequestListItem(
            id=req.id,
            request_id= req.request_id,
            leave_type=LeaveTypeBasic.from_orm(req.leave_type),
            start_date=req.start_date,
            end_date=req.end_date,
            days_count=req.days_count,
            reason=req.reason,
            status=req.status,
            rejection_reason=req.rejection_reason,
            proxy_person=ProxyUserOut.from_orm(req.proxy_user),
            approver=ProxyUserOut.from_orm(req.approver) if req.approver else None,
            approved_at=req.approved_at,
            created_at=req.created_at
        ))

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

def get_team_leave_requests(
    db: Session,
    manager_id: int,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    leave_type_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 10
):
    if status and status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: '{status}'. Must be one of {ALLOWED_STATUSES}")

    # get list of user_id for team member of that manager
    subquery = db.query(Manager.user_id).filter(Manager.manager_id == manager_id)
    team_user_ids = [row[0] for row in subquery.all()]

    if user_id and user_id not in team_user_ids:
        # the target user_id is not the team member
        raise PermissionError("You are not authorized to view this user's leave requests.")

    target_ids = [user_id] if user_id else team_user_ids

    query = db.query(LeaveRequest).options(
        joinedload(LeaveRequest.user),
        joinedload(LeaveRequest.leave_type),
        joinedload(LeaveRequest.proxy_user),
        joinedload(LeaveRequest.approver)
    ).filter(LeaveRequest.user_id.in_(target_ids))

    if status:
        query = query.filter(LeaveRequest.status == status)
    if start_date:
        query = query.filter(LeaveRequest.start_date >= start_date)
    if end_date:
        query = query.filter(LeaveRequest.end_date <= end_date)
    if leave_type_id:
        query = query.filter(LeaveRequest.leave_type_id == leave_type_id)

    total = query.count()
    results = query.order_by(LeaveRequest.start_date.desc()) \
        .offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for req in results:
        items.append(LeaveRequestTeamItem(
            id=req.id,
            request_id= req.request_id,
            leave_type=LeaveTypeBasic.from_orm(req.leave_type),
            start_date=req.start_date,
            end_date=req.end_date,
            days_count=req.days_count,
            reason=req.reason,
            status=req.status,
            rejection_reason=req.rejection_reason,
            proxy_person=ProxyUserOut.from_orm(req.proxy_user),
            approver=ProxyUserOut.from_orm(req.approver) if req.approver else None,
            approved_at=req.approved_at,
            created_at=req.created_at,
            user= ProxyUserOut.from_orm(req.user)
        ))


    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

def get_leave_request_by_id(db: Session, leave_request_id: int) -> LeaveRequestDetail:
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return leave_request

def get_user_id_from_leave_request_by_id(db: Session, leave_request_id: int) -> int:
    leave_request = db.query(LeaveRequest.user_id).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return leave_request

def get_request_id_from_leave_request_by_id(db: Session, id: int) -> int:
    leave_request = db.query(LeaveRequest.request_id).filter(LeaveRequest.id == id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return leave_request

def get_proxy_id_from_leave_request_by_id(db: Session, leave_request_id: int) -> int:
    leave_request = db.query(LeaveRequest.proxy_user_id).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return leave_request

def get_detail_from_leave_request_by_id(db: Session, leave_request_id: int) -> int:
    leave_request = db.query(LeaveRequest.proxy_user_id, LeaveRequest.start_date, LeaveRequest.end_date).filter(LeaveRequest.id == leave_request_id ).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return leave_request

def approve_leave_request(db: Session, leave_request_id: int, approver_id: int) -> LeaveRequestApprovalResponse:
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    

    if leave_request.status != "pending":
        raise ValueError("Can only approve pending leave requests")
    
    approver = db.query(User).filter(User.id == approver_id).first()
    if not approver or not approver.is_manager:
        raise PermissionError("Only managers can approve leave requests")
    
    # Check if the approver is the manager of the request's user
    is_manager = db.query(Manager).filter(
        Manager.manager_id == approver_id,
        Manager.user_id == leave_request.user_id
    ).first()
    
    if not is_manager:
        raise PermissionError("You are not authorized to approve this leave request")
    
    leave_request.status = "approved"
    leave_request.approver_id = approver_id
    leave_request.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(leave_request)
    
    return LeaveRequestApprovalResponse(
        id=leave_request.id,
        request_id=leave_request.request_id,
        status=leave_request.status,
        approver=ProxyUserOut.from_orm(approver),
        approved_at=leave_request.approved_at
    )

def reject_leave_request(db: Session, leave_request_id: int, approver_id: int, rejection_reason: str) -> LeaveRequestRejectionResponse:
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status != "pending":
        raise ValueError("Can only reject pending leave requests")
    
    approver = db.query(User).filter(User.id == approver_id).first()
    if not approver or not approver.is_manager:
        raise PermissionError("Only managers can reject leave requests")
    
    # Check if the approver is the manager of the request's user
    is_manager = db.query(Manager).filter(
        Manager.manager_id == approver_id,
        Manager.user_id == leave_request.user_id
    ).first()
    
    if not is_manager:
        raise PermissionError("You are not authorized to reject this leave request")
    
    leave_request.status = "rejected"
    leave_request.approver_id = approver_id
    leave_request.approved_at = datetime.utcnow()
    leave_request.rejection_reason = rejection_reason
    
    db.commit()
    db.refresh(leave_request)
    
    return LeaveRequestRejectionResponse(
        id=leave_request.id,
        request_id=leave_request.request_id,
        status=leave_request.status,
        approver=ProxyUserOut.from_orm(approver),
        approved_at=leave_request.approved_at,
        rejection_reason=leave_request.rejection_reason
    )