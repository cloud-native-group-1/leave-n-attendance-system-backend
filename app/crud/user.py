from sqlalchemy.orm import Session
from sqlalchemy import select
from ..utils.auth import verify_password
from typing import List
from ..models.user import User
from ..models.department import Department
from ..models.manager import Manager
from sqlalchemy.orm import joinedload

def get_user_by_email(db: Session, email: str):
    res = db.query(User).filter(User.email == email).first()
    return res

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash): 
        return None
    return user
    

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_name_by_id(db: Session, user_id: int):
    return db.query(User.first_name, User.last_name).filter(User.id == user_id).first()


def get_team_members(db: Session, manager_id: int, current_user_id: int) -> List[User]:
    # get all user_id of team members whose manager is current user
    team_member_ids = db.scalars(
        select(Manager.user_id).where(Manager.manager_id == manager_id)
    ).all()

    if not team_member_ids and manager_id != current_user_id:
        # if there is no manager above current user, then return profile of current user
        team_member_ids = []
        print("higheset manger")
        team_member_ids.append(current_user_id)
        print(str(team_member_ids))
        
    # get user profile based on team_member_ids list including department
    # Use joinedload to explicitly load the department relationship
    return db.query(User).options(joinedload(User.department)).filter(User.id.in_(team_member_ids)).all()

def get_manager_id(db: Session, user_id: int):
    # get manager_id firstly:
    stmt = select(Manager.manager_id).where(Manager.user_id == user_id)
    result = db.execute(stmt).first()
    if result:
        return result.manager_id
    return None

def get_manager(db: Session, manager_id: int):
    # then get manager name
    stmt = select(User.id, User.first_name, User.last_name).where(User.id == manager_id)
    return db.execute(stmt).first()

def get_department(db: Session, department_id: int):
    stmt = select(Department.id, Department.name).where(Department.id == department_id)
    return db.execute(stmt).first()