from datetime import date
from models.user import User
from models.department import Department
from models.manager import Manager
from sqlalchemy.orm import Session
from utils.auth import get_password_hash
from database import SessionLocal



def generate_demo_departments(db: Session):
    # 定義部門資料
    departments = [
        {"name": "產品部", "description": "負責產品規劃與市場分析"},
        {"name": "產品研發部", "description": "負責產品研發與技術支持"},
        {"name": "產品設計部", "description": "負責市場推廣與品牌建設"},
    ]

    # 插入部門資料到資料庫
    print("Creating demo departments...")
    for dept in departments:
        department = Department(
            name=dept["name"],
            description=dept["description"]
        )
        db.add(department)

    db.commit()  # 儲存資料
    print("create demo departments successfully.")

def create_demo_users(db: Session):
    # 定義每個層級的人員資料
    manager_data = [
        {"employee_id": "EMP001", "first_name": "張", "last_name": "三", "email": "zhang.san@company.com", "position": "高層主管", "hire_date": date(2015, 1, 1), "is_manager": True, "department_name": "產品部"},
        {"employee_id": "EMP002", "first_name": "李", "last_name": "四", "email": "li.si@company.com", "position": "中階主管", "hire_date": date(2016, 2, 15), "is_manager": True, "department_name": "產品研發部"},
        {"employee_id": "EMP003", "first_name": "王", "last_name": "四", "email": "wang.wu@company.com", "position": "中階主管", "hire_date": date(2017, 4, 10), "is_manager": True, "department_name": "產品設計部"},
    ]

    junior_data = [
        {"employee_id": "EMP004", "first_name": "周", "last_name": "五", "email": "zhou.liu@company.com", "position": "初階員工", "hire_date": date(2020, 3, 20), "department_name": "產品研發部", "manager_id": "EMP002"},
        {"employee_id": "EMP005", "first_name": "吳", "last_name": "五", "email": "wu.qi@company.com", "position": "初階員工", "hire_date": date(2021, 6, 5), "department_name": "產品研發部", "manager_id": "EMP002"},
        {"employee_id": "EMP006", "first_name": "鄭", "last_name": "五", "email": "zheng.ba@company.com", "position": "初階員工", "hire_date": date(2021, 7, 15), "department_name": "產品設計部", "manager_id": "EMP003"},
        {"employee_id": "EMP007", "first_name": "曾", "last_name": "五", "email": "zeng.jiu@company.com", "position": "初階員工", "hire_date": date(2022, 1, 10), "department_name": "產品設計部", "manager_id": "EMP003"},
    ]

    # 依照資料插入資料庫
    # 高層主管與中階主管資料
    print("Creating managers...")
    for manager in manager_data:
        department = db.query(Department).filter(Department.name == manager["department_name"]).first()
        if not department:
            raise ValueError(f"Department '{manager['department_name']}' not found")
        password = get_password_hash("test") 
        user = User(
            employee_id=manager["employee_id"],
            first_name=manager["first_name"],
            last_name=manager["last_name"],
            email=manager["email"],
            department_id=department.id,
            position=manager["position"],
            hire_date=manager["hire_date"],
            is_manager=manager["is_manager"],
            password_hash=password,
        )
        db.add(user)
    
    # 初階員工資料
    print("Creating junior employees...")
    for junior in junior_data:
        department = db.query(Department).filter(Department.name == manager["department_name"]).first()
        if not department:
            raise ValueError(f"Department '{manager['department_name']}' not found")
        password = get_password_hash("test") 
        user = User(
            employee_id=junior["employee_id"],
            first_name=junior["first_name"],
            last_name=junior["last_name"],
            email=junior["email"],
            department_id=department.id,
            position=junior["position"],
            hire_date=junior["hire_date"],
            is_manager=False,
            password_hash=password,
        )
        db.add(user)
    
    db.commit()  # 儲存資料
    print("create demo users successfully.")
def create_manager_relations(db: Session):
    # 定義管理者關係
    manager_relations = [
        {"user_id": "EMP002", "manager_id": "EMP001"},  # 中階主管屬於高層主管
        {"user_id": "EMP003", "manager_id": "EMP001"},  # 中階主管屬於高層主管
        {"user_id": "EMP004", "manager_id": "EMP002"},  # 初階員工屬於中階主管
        {"user_id": "EMP005", "manager_id": "EMP002"},  # 初階員工屬於中階主管
        {"user_id": "EMP006", "manager_id": "EMP003"},  # 初階員工屬於中階主管
        {"user_id": "EMP007", "manager_id": "EMP003"},  # 初階員工屬於中階主管
    ]

    print("Creating manager relations...")
    for relation in manager_relations:
        user = db.query(User).filter(User.employee_id == relation["user_id"]).first()
        manager = db.query(User).filter(User.employee_id == relation["manager_id"]).first()
        if not user or not manager:
            raise ValueError(f"User or manager not found for relation {relation}")
        
        manager_relation = Manager(user_id=user.id, manager_id=manager.id)
        db.add(manager_relation)

    db.commit()  # 儲存資料
    print("create demo manager relations successfully.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        generate_demo_departments(db)
        create_demo_users(db)
        create_manager_relations(db)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
    print("Demo data generation completed.")