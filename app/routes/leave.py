from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import logging
from ..crud import user as user_crud
from ..crud import leave as leave_crud
from ..crud import notification as notification_crud
from ..schemas.user import UserOut, TeamListResponse
from ..schemas.leave import LeaveRequestDetail, LeaveRequestOut, LeaveRequestCreate, LeaveRequestListResponse, LeaveRequestTeamListResponse, LeaveRequestApprovalResponse, LeaveRequestRejectionRequest, LeaveRequestRejectionResponse
from ..utils.dependencies import get_current_user
from ..models.user import User
from ..database import get_db

# 取得模組的日誌記錄器
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/leave-requests",
    tags=["leave-requests"]
)

@router.post("", response_model=LeaveRequestOut, status_code=status.HTTP_201_CREATED)
def request_leave(
    payload: LeaveRequestCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Create a new leave request for current user
    """
    try: 
        result = leave_crud.create_leave_request(db, current_user.id, payload)
        # get manager id
        manager_id = user_crud.get_manager_id(db, current_user.id)
        if manager_id != None:
            # then push a notification to his manager
            title = "有一筆新假單需要您的審核"
            message = str(current_user.last_name) + str(current_user.first_name) + "的假單需要您的審核"
            leave_request_id = result.id
            notification_crud.create_notifications(db, manager_id, title, message, leave_request_id, 'pending')
            logger.info(f"Successfully send notification to manager whose use_id is: {manager_id}")
        else:
            logger.warning(f"Cannot find the manager of current user whose user_id: {current_user.id}")

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=LeaveRequestListResponse)
def list_my_leave_requests(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected)"),
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    leave_type_id: Optional[int] = Query(None, description="Filter by leave type ID"),
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    per_page: Optional[int] = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of leave requests for the current user.
    """
    client_ip = request.client.host
    logger.info(f"User {current_user.email} (ID: {current_user.id}) requesting leave list from {client_ip}")
    logger.info(f"RAW Request parameters: {dict(request.query_params)}")
    logger.debug(f"Processed parameters: status={status}, start_date={start_date}, end_date={end_date}, leave_type_id={leave_type_id}, page={page}, per_page={per_page}")
    
    # 設定默認值
    try:
        # 確保參數類型正確
        actual_page = 1
        if page is not None:
            try:
                actual_page = int(page)
                if actual_page < 1:
                    actual_page = 1
            except (ValueError, TypeError):
                logger.warning(f"Invalid page parameter: {page}, using default: 1")
                actual_page = 1
                
        actual_per_page = 10
        if per_page is not None:
            try:
                actual_per_page = int(per_page)
                if actual_per_page < 1:
                    actual_per_page = 10
                elif actual_per_page > 100:
                    actual_per_page = 100
            except (ValueError, TypeError):
                logger.warning(f"Invalid per_page parameter: {per_page}, using default: 10")
                actual_per_page = 10
        
        # 處理日期參數
        actual_start_date = None
        if start_date is not None:
            if not isinstance(start_date, date):
                logger.warning(f"Invalid start_date format: {start_date}")
            actual_start_date = start_date
        
        actual_end_date = None
        if end_date is not None:
            if not isinstance(end_date, date):
                logger.warning(f"Invalid end_date format: {end_date}")
            actual_end_date = end_date
        
        # 處理狀態參數
        actual_status = None
        if status is not None:
            if status not in ["pending", "approved", "rejected"]:
                logger.warning(f"Invalid status value: {status}, must be one of pending, approved, rejected")
            else:
                actual_status = status
                
        # 處理 leave_type_id 參數
        actual_leave_type_id = None
        if leave_type_id is not None:
            try:
                actual_leave_type_id = int(leave_type_id)
                if actual_leave_type_id < 1:
                    logger.warning(f"Invalid leave_type_id: {leave_type_id}, must be a positive integer")
                    actual_leave_type_id = None
            except (ValueError, TypeError):
                logger.warning(f"Invalid leave_type_id parameter: {leave_type_id}")

        logger.debug(f"Final parameters: status={actual_status}, start_date={actual_start_date}, end_date={actual_end_date}, leave_type_id={actual_leave_type_id}, page={actual_page}, per_page={actual_per_page}")
        
        # 使用安全的參數呼叫 CRUD 方法
        result = leave_crud.get_leave_requests_for_user(
            db=db,
            user_id=current_user.id,
            status=actual_status,
            start_date=actual_start_date,
            end_date=actual_end_date,
            leave_type_id=actual_leave_type_id,
            page=actual_page,
            per_page=actual_per_page,
        )
        
        logger.debug(f"Found {result['total']} leave requests for user {current_user.id}")
        
    except ValueError as e:
        logger.error(f"ValueError in leave request listing: {str(e)}")
        # 返回一個安全的默認結果，而不是拋出 400 錯誤
        # 這將避免前端遇到 Bad Request
        return {
            "leave_requests": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "per_page": 10,
                "total_pages": 0
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in leave request listing: {str(e)}", exc_info=True)
        # 也返回一個安全的默認結果
        return {
            "leave_requests": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "per_page": 10,
                "total_pages": 0
            }
        }

    response = {
        "leave_requests": result["items"],
        "pagination": {
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
            "total_pages": result["total_pages"]
        }
    }
    
    logger.info(f"Successfully returned leave list for user {current_user.email} (ID: {current_user.id})")
    return response

@router.get("/team", response_model=LeaveRequestTeamListResponse)
def list_team_leave_requests(
    request: Request,
    user_id: Optional[int] = Query(None, description="Target user ID (deprecated, use employee_id instead)"),
    employee_id: Optional[int] = Query(None, description="Target employee ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected)"),
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    leave_type_id: Optional[int] = Query(None, description="Filter by leave type ID"),
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    per_page: Optional[int] = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)    
): 
    """
    Get list of leave requests of team members.
    """
    client_ip = request.client.host
    logger.info(f"Manager {current_user.email} (ID: {current_user.id}) requesting team leave list from {client_ip}")
    logger.info(f"RAW Request parameters: {dict(request.query_params)}")
    
    if not current_user.is_manager:
        logger.warning(f"Non-manager user {current_user.email} (ID: {current_user.id}) attempted to access team leave list")
        # 也返回安全的默認結果
        return {
            "leave_requests": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "per_page": 10,
                "total_pages": 0
            }
        }
    
    try:
        # Prioritize employee_id over user_id if both are provided
        target_id = employee_id if employee_id is not None else user_id
        
        # 確保參數類型正確
        actual_user_id = None
        if target_id is not None:
            try:
                actual_user_id = int(target_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid user/employee ID parameter: {target_id}")
        
        actual_page = 1
        if page is not None:
            try:
                actual_page = int(page)
                if actual_page < 1:
                    actual_page = 1
            except (ValueError, TypeError):
                logger.warning(f"Invalid page parameter: {page}, using default: 1")
                actual_page = 1
                
        actual_per_page = 10
        if per_page is not None:
            try:
                actual_per_page = int(per_page)
                if actual_per_page < 1:
                    actual_per_page = 10
                elif actual_per_page > 100:
                    actual_per_page = 100
            except (ValueError, TypeError):
                logger.warning(f"Invalid per_page parameter: {per_page}, using default: 10")
                actual_per_page = 10
        
        # 處理日期參數
        actual_start_date = None
        if start_date is not None:
            if not isinstance(start_date, date):
                logger.warning(f"Invalid start_date format: {start_date}")
            else:
                actual_start_date = start_date
        
        actual_end_date = None
        if end_date is not None:
            if not isinstance(end_date, date):
                logger.warning(f"Invalid end_date format: {end_date}")
            else:
                actual_end_date = end_date
        
        # 處理狀態參數
        actual_status = None
        if status is not None:
            if status not in ["pending", "approved", "rejected"]:
                logger.warning(f"Invalid status value: {status}, must be one of pending, approved, rejected")
            else:
                actual_status = status

        # 處理 leave_type_id 參數
        actual_leave_type_id = None
        if leave_type_id is not None:
            try:
                actual_leave_type_id = int(leave_type_id)
                if actual_leave_type_id < 1:
                    logger.warning(f"Invalid leave_type_id: {leave_type_id}, must be a positive integer")
                    actual_leave_type_id = None
            except (ValueError, TypeError):
                logger.warning(f"Invalid leave_type_id parameter: {leave_type_id}")

        logger.debug(f"Final parameters: user_id={actual_user_id}, status={actual_status}, start_date={actual_start_date}, end_date={actual_end_date}, leave_type_id={actual_leave_type_id}, page={actual_page}, per_page={actual_per_page}")
            
        result = leave_crud.get_team_leave_requests(
            db=db,
            manager_id=current_user.id,
            user_id=actual_user_id,
            status=actual_status,
            start_date=actual_start_date,
            end_date=actual_end_date,
            leave_type_id=actual_leave_type_id,
            page=actual_page,
            per_page=actual_per_page
        )
        
        logger.debug(f"Found {result['total']} team leave requests for manager {current_user.id}")
        
    except ValueError as e:
        logger.error(f"ValueError in team leave request listing: {str(e)}")
        # 返回一個安全的默認結果
        return {
            "leave_requests": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "per_page": 10,
                "total_pages": 0
            }
        }
    except PermissionError as e:
        logger.error(f"PermissionError in team leave request listing: {str(e)}")
        # 返回一個安全的默認結果
        return {
            "leave_requests": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "per_page": 10,
                "total_pages": 0
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in team leave request listing: {str(e)}", exc_info=True)
        # 也返回一個安全的默認結果
        return {
            "leave_requests": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "per_page": 10,
                "total_pages": 0
            }
        }
    
    response = {
        "leave_requests": result["items"],
        "pagination": {
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
            "total_pages": result["total_pages"]
        }
    }
    
    logger.info(f"Successfully returned team leave list for manager {current_user.email} (ID: {current_user.id})")
    return response


@router.get("/pending", response_model=LeaveRequestTeamListResponse)
def list_pending_leave_requests(
    user_id: Optional[int] = Query(None, description="Target user ID (deprecated, use employee_id instead)"),
    employee_id: Optional[int] = Query(None, description="Target employee ID"),
    leave_type_id: Optional[int] = Query(None, description="Filter by leave type ID"),
    page: Optional[int] = Query(1, ge = 1),
    per_page: Optional[int] = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user:  User = Depends(get_current_user)    
): 
    """
    Get list of pending leave requests of team members.
    """
    if not current_user.is_manager:
        raise HTTPException(status_code=403, detail="Access restricted to managers.")
    
    try:
        # Prioritize employee_id over user_id if both are provided
        target_id = employee_id if employee_id is not None else user_id
        
        result = leave_crud.get_team_leave_requests(
            db=db,
            manager_id=current_user.id,
            user_id=target_id,
            status="pending",
            leave_type_id=leave_type_id,
            page=page,
            per_page=per_page
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    return {
        "leave_requests": result["items"],
        "pagination": {
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
            "total_pages": result["total_pages"]
        }
    }

@router.get("/{leave_request_id}", response_model=LeaveRequestDetail)
def get_leave_request_details(
    leave_request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific leave request by ID.
    """
    client_ip = request.client.host
    logger.info(f"User {current_user.email} (ID: {current_user.id}) requesting leave details for ID {leave_request_id} from {client_ip}")
    
    try:
        result = leave_crud.get_leave_request_by_id(db, leave_request_id)
        logger.info(f"Successfully returned leave details for ID {leave_request_id}")
        return result
    except HTTPException as e:
        logger.error(f"HTTP error in leave request details: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in leave request details: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.patch("/{leave_request_id}/approve", response_model=LeaveRequestApprovalResponse)
def approve_leave_request(
    leave_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a leave request. Only managers can approve leave requests for their team members.
    """
    
    try:
        result = leave_crud.approve_leave_request(db, leave_request_id, current_user.id)

        # push a notification to the user of leave request
        applicant_id = leave_crud.get_user_id_from_leave_request_by_id(db, leave_request_id)[0]
        l_id = leave_crud.get_request_id_from_leave_request_by_id(db, leave_request_id)[0]
        title = "您的假單已被主管批准!"
        message = "您的假單(id: " + str(l_id) + ")已被批准!" 
        leave_request_id = leave_request_id 
        notification_crud.create_notifications(db, applicant_id, title, message, leave_request_id, 'approval')
        logger.info(f"Successfully send notification to applicant whose use_id is: {applicant_id}")

        # push a notification to proxy user of the leave request
        # proxy_user_id = leave_crud.get_proxy_id_from_leave_request_by_id(db, leave_request_id)[0]
        detail = leave_crud.get_detail_from_leave_request_by_id(db, leave_request_id)
        proxy_user_id = detail[0]
        start_date = detail[1]
        end_date = detail[2]
        (applicant_first_name, applicant_last_name) = user_crud.get_user_name_by_id(db, applicant_id)

        title = "您已被指派為假單的職務代理人"
        message = "您已被指派於" + str(start_date) + "至" + str(end_date) + "擔任" + str(applicant_last_name) + str(applicant_first_name) + "的職務代理人。"
        notification_crud.create_notifications(db, proxy_user_id, title, message, leave_request_id, 'proxy')
        logger.info(f"Successfully send notification to proxy user whose use_id is: {proxy_user_id}")

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.patch("/{leave_request_id}/reject", response_model=LeaveRequestRejectionResponse)
def reject_leave_request(
    leave_request_id: int,
    rejection_data: LeaveRequestRejectionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject a leave request. Only managers can reject leave requests for their team members.
    """
    client_ip = request.client.host
    logger.info(f"Manager {current_user.email} (ID: {current_user.id}) attempting to reject leave request {leave_request_id} from {client_ip}")
    
    try:
        result = leave_crud.reject_leave_request(
            db, 
            leave_request_id, 
            current_user.id,
            rejection_data.rejection_reason
        )
        logger.info(f"Successfully rejected leave request {leave_request_id} by manager {current_user.email}")

        # push a notification to the user of leave request
        applicant_id = leave_crud.get_user_id_from_leave_request_by_id(db, leave_request_id)[0]
        l_id = leave_crud.get_request_id_from_leave_request_by_id(db, leave_request_id)[0]
        title = "您的假單已被否決"
        message = "您的假單(id: " + str(l_id) + ")已被否決" 
        leave_request_id = leave_request_id 
        notification_crud.create_notifications(db, applicant_id, title, message, leave_request_id, 'rejection')
        logger.info(f"Successfully send notification to applicant whose use_id is: {applicant_id}")

        return result
    except ValueError as e:
        logger.error(f"ValueError in leave request rejection: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.error(f"PermissionError in leave request rejection: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in leave request rejection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")



