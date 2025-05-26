from pydantic import BaseModel
from typing import List, Optional

class UserLogin(BaseModel):
    email: str 
    password: str

class DepartmentOut(BaseModel):
    id: int
    name: str

class ManagerOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    department: DepartmentOut
    position: str

class UserLoginOut(BaseModel):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: DepartmentOut
    position: str
    is_manager: bool

class UserOut(UserLoginOut):
    manager: Optional[ManagerOut] = None
    hire_date: str


class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegister(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str 
    password: str
    department_id: int
    postiion: str
    manager_id: int
    is_manager: bool
    annual_leave_quota: int
    sick_leave_quota: int
    personal_leav_quota: int
    public_holiday_quota: int

class TeamMemberOut(BaseModel):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    position: str
    email: str
    department: DepartmentOut

class TeamListResponse(BaseModel):
    team_members: List[TeamMemberOut]
  