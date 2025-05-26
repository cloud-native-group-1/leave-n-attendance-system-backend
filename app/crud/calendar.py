from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract
from datetime import date, timedelta
from typing import List, Dict, Optional
from ..models.leave_request import LeaveRequest, LeaveStatus
from ..models.user import User
from ..models.leave_type import LeaveType
from ..schemas.calendar import DayInfo, MemberOnLeave, TeamCalendarResponse


def get_team_calendar(
    db: Session,
    team_member_ids: List[int],
    year: Optional[int],
    month: Optional[int]
) -> TeamCalendarResponse:
    # Build base query for all approved leave requests for team members
    query = db.query(LeaveRequest)
    query = query.join(User, LeaveRequest.user_id == User.id)
    query = query.join(LeaveType, LeaveRequest.leave_type_id == LeaveType.id)
    query = query.filter(
        LeaveRequest.user_id.in_(team_member_ids),
        LeaveRequest.status == "approved"
    )
    if year is not None:
        query = query.filter(extract('year', LeaveRequest.start_date) == year)
    if month is not None:
        query = query.filter(extract('month', LeaveRequest.start_date) == month)
    leave_requests = query.all()

    # Create a dictionary to store members on leave for each day
    calendar_data: Dict[date, List[MemberOnLeave]] = {}

    # Process each leave request
    for request in leave_requests:
        current_date = request.start_date
        while current_date <= request.end_date:
            # Only include dates in the specified month if month is provided
            if (month is None or current_date.month == month) and (year is None or current_date.year == year):
                if current_date not in calendar_data:
                    calendar_data[current_date] = []
                calendar_data[current_date].append(
                    MemberOnLeave(
                        id=request.user.id,
                        first_name=request.user.first_name,
                        last_name=request.user.last_name,
                        leave_type=request.leave_type.name
                    )
                )
            current_date += timedelta(days=1)

    # Convert the dictionary to a list of DayInfo objects
    days = [
        DayInfo(date=day, members_on_leave=members)
        for day, members in sorted(calendar_data.items())
    ]

    return TeamCalendarResponse(
        year=year if year is not None else 0,
        month=month if month is not None else 0,
        days=days
    )
