from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime

from ..models.leave_request import LeaveRequest
from ..models.leave_quota import LeaveQuota
from ..models.leave_type import  LeaveType
from ..models.user import User
from ..schemas.leave_balance import LeaveBalanceResponse, LeaveBalanceItem, LeaveTypeInfo, LeaveRequestSummary


def get_leave_balances(db: Session, user_id: int) -> LeaveBalanceResponse:
    year = datetime.now().year
    
    # 查出該使用者的所有假別配額，并预载 leave_type 数据
    quotas = (
        db.query(LeaveQuota)
        .options(joinedload(LeaveQuota.leave_type))
        .filter(LeaveQuota.user_id == user_id, LeaveQuota.year == year)
        .all()
    )

    balances = []
    print(quotas)

    for quota_entry in quotas:
        leave_type = quota_entry.leave_type

        # 使用更高效的查询計算已使用天數
        used_days = db.query(func.sum(LeaveRequest.days_count)).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.leave_type_id == leave_type.id,
            func.extract('year', LeaveRequest.start_date) == year,
            LeaveRequest.status == 'approved'
        ).scalar() or 0

        # 获取请假记录明细
        approved_requests = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.user_id == user_id,
                LeaveRequest.leave_type_id == leave_type.id,
                func.extract('year', LeaveRequest.start_date) == year,
                LeaveRequest.status == 'approved'
            )
            .all()
        )

        remaining_days = quota_entry.quota - used_days

        balances.append(LeaveBalanceItem(
            leave_type=LeaveTypeInfo.from_orm(leave_type),
            quota=quota_entry.quota,
            used_days=used_days,
            remaining_days=remaining_days,
            leave_requests=[LeaveRequestSummary.from_orm(r) for r in approved_requests]
        ))

    return LeaveBalanceResponse(year=year, balances=balances)
