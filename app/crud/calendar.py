from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
from typing import List, Dict
from ..models.leave_request import LeaveRequest, LeaveStatus
from ..models.user import User
from ..models.leave_type import LeaveType
from ..schemas.calendar import DayInfo, MemberOnLeave, TeamCalendarResponse


def get_team_calendar(
    db: Session,
    team_member_ids: List[int],
    year: int,
    month: int
) -> TeamCalendarResponse:
    # Get all approved leave requests for team members in the specified month
    leave_requests = (
        db.query(LeaveRequest)
        .join(User, LeaveRequest.user_id == User.id)
        .join(LeaveType, LeaveRequest.leave_type_id == LeaveType.id)
        .filter(
            LeaveRequest.user_id.in_(team_member_ids),
            LeaveRequest.status == "approved",
            extract('year', LeaveRequest.start_date) == year,
            extract('month', LeaveRequest.start_date) == month
        )
        .all()
    )

    # Create a dictionary to store members on leave for each day
    calendar_data: Dict[date, List[MemberOnLeave]] = {}

    # Process each leave request
    for request in leave_requests:
        current_date = request.start_date
        while current_date <= request.end_date:
            if current_date.month == month:  # Only include dates in the specified month
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
            current_date = date(current_date.year, current_date.month, current_date.day + 1)

    # Convert the dictionary to a list of DayInfo objects
    days = [
        DayInfo(date=day, members_on_leave=members)
        for day, members in sorted(calendar_data.items())
    ]

    return TeamCalendarResponse(
        year=year,
        month=month,
        days=days
    )
