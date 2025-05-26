from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from ..schemas.user import UserLogin, Token
from ..crud import user as user_crud
from ..utils.auth import create_access_token
from ..utils.dependencies import login_form_schema
from ..database import get_db
from pydantic import BaseModel
import logging

# 取得模組的日誌記錄器
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: LoginRequest = Body(...),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host
    logger.info(f"Login attempt from {client_ip} with username: {login_data.username}")
    
    # authenticate_user already loads user in a single query
    current_user = user_crud.authenticate_user(db, login_data.username, login_data.password)
    if not current_user:
        logger.warning(f"Failed login attempt for {login_data.username} from {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = current_user.id
    # Use the optimized get_user_by_id function to get user with department in a single query
    user_with_department = user_crud.get_user_by_id(db, user_id)
    department = user_with_department.department if user_with_department and hasattr(user_with_department, 'department') else None
    
    # 記錄用戶詳細信息，使用安全序列化
    logger.debug(f"User details: ID: {user_id}, Email: {current_user.email}, Department: {department}")
    
    user = {
        "id": user_id,
        "employee_id": current_user.employee_id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "department": {
            "id": department.id,
            "name": department.name
        } if department else None,
        "position": current_user.position,
        "is_manager": current_user.is_manager        
    }
    
    token = create_access_token(data={"sub": str(user['id'])})
    logger.debug(f"Generated token for user {user_id}: {token[:10]}...")
    
    cookie_response = JSONResponse(
        content={"access_token": token, "token_type": "bearer"}
    )
    cookie_response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,              # Changed to False for development (http)
        samesite="Lax",            # Changed to Lax for cross-domain requests in development
        max_age=3600,             # 1 hour
        path="/"
    )
    logger.info(f"User {current_user.email} (ID: {user_id}) successfully logged in from {client_ip}")
    return cookie_response

@router.post("/logout")
def logout(request: Request):
    client_ip = request.client.host
    logger.info(f"Logout request from {client_ip}")
    
    response = JSONResponse(content={"message": "Logged out successfully"})
    
    # Clear the HTTP-only cookie by setting it to expire immediately
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,              # Changed to False for development
        samesite="Lax",            # Changed to Lax for development
        path="/"
    )
    
    logger.info(f"User logged out from {client_ip}")
    return response

# Fix missing function that was previously used
def object_to_dict(obj):
    if obj is None:
        return None
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)