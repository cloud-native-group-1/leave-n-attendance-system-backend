from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging
from ..crud import calendar as calendar_crud
from ..crud import user as user_crud
from ..schemas.calendar import TeamCalendarResponse
from ..utils.dependencies import get_current_user
from ..models.user import User
from ..database import get_db

# Get logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/calendar",
    tags=["calendar"]
)


@router.get("/team", response_model=TeamCalendarResponse)
def get_team_calendar(
    year: Optional[int] = Query(..., description="Year (e.g., 2023)"),
    month: Optional[int] = Query(..., description="Month (1-12)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get team calendar showing approved leave requests for team members.
    """
    client_ip = request.client.host
    logger.info(f"User {current_user.email} (ID: {current_user.id}) requesting team calendar from {client_ip}")
    
    try:
        # Validate month
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12")
        
        # Get team members
        team_members = user_crud.get_team_members(db, current_user.id)
        team_member_ids = [member.id for member in team_members]
        
        # Get calendar data
        calendar_data = calendar_crud.get_team_calendar(
            db=db,
            team_member_ids=team_member_ids,
            year=year,
            month=month
        )
        
        logger.info(f"Successfully returned team calendar for {year}-{month}")
        return calendar_data
        
    except ValueError as e:
        logger.error(f"ValueError in team calendar: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in team calendar: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
