from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from ..crud import user as user_crud
from ..schemas.user import UserOut, TeamListResponse
from ..utils.dependencies import get_current_user
from ..models.user import User
from ..database import get_db
import logging
import json

# 取得模組的日誌記錄器
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

@router.get("/me", response_model=UserOut)
def get_my_profile(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client_ip = request.client.host
    logger.info(f"User {current_user.email} (ID: {current_user.id}) requesting profile from {client_ip}")
    
    user_id = current_user.id
    department_id = current_user.department_id

    # Get manager with department in a single query
    logger.debug(f"Getting manager for user {user_id}")
    manager_id = user_crud.get_manager_id(db, user_id)
    logger.debug(f"Manager ID for user {user_id}: {manager_id}")
    
    # 處理 manager
    manager_dict = None
    if manager_id is not None:
        # Use the optimized get_manager function that preloads department
        manager = user_crud.get_manager(db, manager_id)
        if manager and manager.department:
            manager_dict = {
                "id": manager.id,
                "first_name": manager.first_name,
                "last_name": manager.last_name,
                "email": manager.email,
                "department": {
                    "id": manager.department.id,
                    "name": manager.department.name
                },
                "position": manager.position
            }
        logger.debug(f"Manager info: {manager_dict}")

    # 處理 department - user should already have department loaded from get_current_user
    department_dict = None
    if department_id is not None and current_user.department:
        department_dict = {
            "id": current_user.department.id,
            "name": current_user.department.name
        }
    elif department_id is not None:
        # Fallback to separate query if needed
        department = user_crud.get_department(db, department_id)
        if department:
            department_dict = {
                "id": department.id,
                "name": department.name
            }
    logger.debug(f"Department for user {user_id}: {department_dict}")
    
    # 構建結果
    result = {
        "id": user_id,
        "employee_id": current_user.employee_id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "department": department_dict,
        "position": current_user.position,
        "manager": manager_dict,
        "hire_date": str(current_user.hire_date),
        "is_manager": current_user.is_manager
    }
    
    logger.debug(f"User profile data prepared")
    logger.info(f"Successfully returned profile for user {current_user.email} (ID: {user_id})")
    return result

@router.get("/team", response_model=TeamListResponse)
def get_teammate(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get teammate of the user
    """
    client_ip = request.client.host
    logger.info(f"User {current_user.email} (ID: {current_user.id}) requesting team list from {client_ip}")
    
    manager_id = user_crud.get_manager_id(db, current_user.id)

    # This already uses joinedload for department in the CRUD function
    members = user_crud.get_team_members(db, manager_id, current_user.id)
    
    # 記錄團隊成員信息，但避免記錄敏感信息
    member_count = len(members) if members else 0
    logger.debug(f"Found {member_count} team members for manager {current_user.id}")
    if members:
        member_ids = [str(m.id) for m in members]
        logger.debug(f"Team member IDs: {', '.join(member_ids)}")
    
    logger.info(f"Successfully returned team list with {member_count} members for manager {current_user.email}")
    return {"team_members": members}


@router.get("/subordinates", response_model=TeamListResponse)
def get_subordinates(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get subordinates of the manager
    """
    client_ip = request.client.host
    logger.info(f"User {current_user.email} (ID: {current_user.id}) requesting list of subordinates from {client_ip}")
    
    if not current_user.is_manager:
        logger.warning(f"Non-manager user {current_user.email} (ID: {current_user.id}) attempted to access team list")
        raise HTTPException(status_code=403, detail="Only managers can access this resource.")
    
    # This already uses joinedload for department in the CRUD function
    members = user_crud.get_team_members(db, current_user.id, current_user.id)
    
    # 記錄團隊成員信息，但避免記錄敏感信息
    member_count = len(members) if members else 0
    logger.debug(f"Found {member_count} team members for manager {current_user.id}")
    if members:
        member_ids = [str(m.id) for m in members]
        logger.debug(f"Team member IDs: {', '.join(member_ids)}")
    
    logger.info(f"Successfully returned team list with {member_count} members for manager {current_user.email}")
    
    # Transform members to include department_name
    team_members = [
        {
            "id": member.id,
            "employee_id": member.employee_id,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "position": member.position,
            "email": member.email,
            "department": {
                "id": member.department.id,
                "name": member.department.name
            }
        }
        for member in members
    ]
    
    return {"team_members": team_members}

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client_ip = request.client.host
    logger.info(f"User {current_user.email} (ID: {current_user.id}) requesting user profile for ID: {user_id} from {client_ip}")
    
    # This uses joinedload to preload department in a single query
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    department_id = user.department_id
    
    # 處理 manager - get manager with department in one query
    manager_id = user_crud.get_manager_id(db, user_id)
    manager_dict = None
    if manager_id is not None:
        manager = user_crud.get_manager(db, manager_id)
        if manager and manager.department:
            manager_dict = {
                "id": manager.id,
                "first_name": manager.first_name,
                "last_name": manager.last_name,
                "email": manager.email,
                "department": {
                    "id": manager.department.id,
                    "name": manager.department.name
                },
                "position": manager.position
            }
    
    # 處理 department - should already be loaded from the get_user_by_id call
    department_dict = None
    if department_id is not None and user.department:
        department_dict = {
            "id": user.department.id,
            "name": user.department.name
        }
    elif department_id is not None:
        # Fallback to separate query if needed
        department = user_crud.get_department(db, department_id)
        if department:
            department_dict = {
                "id": department.id,
                "name": department.name
            }
    
    # 構建結果
    result = {
        "id": user_id,
        "employee_id": user.employee_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "department": department_dict,
        "position": user.position,
        "manager": manager_dict,
        "hire_date": str(user.hire_date),
        "is_manager": user.is_manager
    }
    
    logger.info(f"Successfully returned profile for user ID: {user_id}")
    return result