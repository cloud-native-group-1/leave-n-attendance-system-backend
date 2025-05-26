from faker import Faker
from sqlalchemy.orm import Session
from models.user import User
from models.leave_quota import LeaveQuota
from models.leave_request import LeaveRequest, LeaveStatus
from models.leave_type import LeaveType
from models.department import Department
from models.notification import Notification
from models.leave_request_attachment import LeaveAttachment
from models.audit_log import AuditLog
from models.manager import Manager
import random
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from utils.auth import get_password_hash
from typing import Dict

from database import SessionLocal

fake = Faker()

user_names = []

def generate_fake_departments(db: Session, num_departments: int = 5):
    print("Clearing existing departments...")
    db.query(Department).delete()  # 清空 leave_quota 表格資料
    db.commit()  # 提交刪除操作

    print("Generating fake departments...")
    for _ in range(num_departments):
        department = Department(
            name=fake.company(),  # 生成公司名稱作為部門名稱
            description=fake.text(max_nb_chars=200),  # 隨機生成一個描述
            # created_at 和 updated_at 在資料庫層級會自動填充，因此不需要在這裡設置
        )
        db.add(department)
    db.commit()

def generate_fake_users(db: Session, num_users: int = 20):
    # print("Clearing existing users...")
    # db.query(User).delete()  # 清空 leave_quota 表格資料
    # db.commit()  # 提交刪除操作

    print("Generating fake users...")
    departments = db.query(Department).all()
    if not departments:
        raise ValueError("Departments must be generated before users.")
    
    for _ in range(num_users):
        department = fake.random_element(elements=departments)  # 隨機選擇部門
        password = get_password_hash('test')  # 隨機生成密碼
        user = User(
            employee_id=f"EMP{fake.unique.random_number(digits=5)}",  # 確保生成唯一的員工ID
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            department_id=department.id,  # 部門 ID
            position=fake.job(),
            hire_date=fake.date_this_decade(),
            is_manager=fake.boolean(),  # 隨機決定是否為經理
            password_hash=password,  # 密碼哈希
        )
        db.add(user)
    
    db.commit()

def reset_manager_relations(db: Session):
    print("Clearing existing manager relations...")
    db.query(Manager).delete()  # 清空 leave_quota 表格資料
    db.commit()  # 提交刪除操作

    print("Generating fake manager relations...")
    users = db.query(User).all()
    managers = [user for user in users if user.is_manager]  # 過濾出經理的使用者
    available_subordinates = [user for user in users if not user.is_manager]  # 過濾出非經理的使用者
    if not available_subordinates:
        raise ValueError("No available users to assign as subordinates.")
    if not managers:
        raise ValueError("No managers available to assign subordinates.")
    print(f"Managers: {[m.id for m in managers]}")
    for manager in managers:
        print("available_subordinates", [u.id for u in available_subordinates])
        if len(available_subordinates) == 0:
            print("No available subordinates left to assign.")
            break

        if len(available_subordinates) > 5:
            subordinate_num = fake.random_int(1, 5)
        else:
            subordinate_num = fake.random_int(1, len(available_subordinates))
        
        subordinates = fake.random_elements(elements=available_subordinates, length=subordinate_num, unique=True)
        for subordinate in subordinates:
            manager_entry = Manager(user_id=subordinate.id, manager_id=manager.id)
            db.add(manager_entry)
            print(f"Removed {subordinate.id} from available subordinates")
            available_subordinates.remove(subordinate)  # 從可用的下屬中移除已經分配的下屬

    db.commit()

def reset_proxy_relations(db: Session):
    print("Reset proxy relation in leave request")
    leave_requests = db.query(LeaveRequest).order_by(LeaveRequest.id).all()
    if not leave_requests:
        raise ValueError("No leave requests available to assign proxy.")
    manager_relations = db.query(Manager).all()
    if not manager_relations:
        raise ValueError("No manager relations available to assign proxy.")
    
    user_id = []
    teams = {}
    for relation in manager_relations:
        if relation.manager_id not in teams:
            teams[relation.manager_id] = []
        teams[relation.manager_id].append(relation.user_id)
    print("teams: ", teams)
    for i in range(21):
        curr_user = leave_requests[i].user_id
        curr_approver = leave_requests[i].approver_id
        print("curr_user: ", curr_user)
        print("curr_approver: ", curr_approver)
        print("teams[curr_approver]: ", teams[curr_approver])
        while 1:
            proxy = fake.random_element(elements=teams[curr_approver])
            if proxy != curr_user:
                leave_requests[i].proxy_user_id = proxy
                print(f"Leave request {leave_requests[i].id} proxy user set to {proxy}")
                db.add(leave_requests[i])
                break

    db.commit()
         
        




def generate_fake_leave_types(db: Session, num_leave_types: int = 5):
    print("Generating fake leave types...")
    for _ in range(num_leave_types):
        leave_type = LeaveType(
            name=fake.word(),  # 隨機生成名稱
            description=fake.sentence() if fake.boolean() else None,  # 隨機生成描述，或設定為 None
            requires_attachment=fake.boolean(),  # 隨機生成是否需要附件
            color_code=fake.hex_color(),  # 使用 Hex 顏色碼來生成
        )
        db.add(leave_type)
    db.commit()


def generate_fake_leave_quotas(db: Session, num_quotas: int = 30):
    # print("Clearing existing leave quotas...")
    # db.query(LeaveQuota).delete()  # 清空 leave_quota 表格資料
    # db.commit()  # 提交刪除操作

    print("Generating fake leave quotas...")
    users = db.query(User).all()
    leave_types = db.query(LeaveType).all()
    existing_quotas = set()  # 用來追蹤已經存在的 (user_id, leave_type_id, year) 組合

    leave_quotas_to_add = []  # 儲存所有將要插入的假資料

    for _ in range(num_quotas):
        user_id = fake.random_element(elements=users).id
        leave_type_id = fake.random_element(elements=leave_types).id
        year = 2025  # 隨機選擇一個合理的年度

        # 確保不會插入重複的 user_id, leave_type_id, year 組合
        if (user_id, leave_type_id, year) in existing_quotas:
            continue  # 跳過重複的資料
        existing_quotas.add((user_id, leave_type_id, year))

        leave_quota = LeaveQuota(
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year,
            quota=fake.random_int(min=10, max=30),
        )
        leave_quotas_to_add.append(leave_quota)

    # 一次性插入所有資料，提高性能
    db.add_all(leave_quotas_to_add)
    try:
        db.commit()  # 提交新增操作
    except IntegrityError as e:
        db.rollback()
        print(f"Error inserting leave quotas: {e}")

def generate_fake_leave_requests(db: Session, num_requests: int = 20):
    print("Clearing existing leave requests...")
    db.query(LeaveRequest).delete()  # 清空 leave_quota 表格資料
    db.commit()  # 提交刪除操作
    
    print("Generating fake leave requests...")
    users = db.query(User).all()
    leave_types = db.query(LeaveType).all()

    if not users or not leave_types:
        raise ValueError("請先建立使用者與假期類型資料")

    for _ in range(num_requests):
        # 隨機選擇狀態，可能是 Pending、Approved 或 Rejected
        status = random.choice(['Pending', 'Approved', 'Rejected'])
        print(f"Generating leave request with status: {status}, type: {type(status)}")
        user = fake.random_element(elements=users)
        leave_type = fake.random_element(elements=leave_types)

        # 確保 start_date < end_date
        start_date = fake.date_between(start_date='-30d', end_date='today')
        end_date = start_date + timedelta(days=random.randint(1, 5))

        # 隨機選擇代理使用者 (proxy_user_id)，這裡假設選擇一個不同的員工作為代理
        proxy_user = fake.random_element(elements=[u for u in users if u.id != user.id])

        leave_request = LeaveRequest(
            request_id=f"REQ{datetime.now().strftime('%Y%m%d')}{fake.unique.random_int(min=1000, max=9999)}",
            user_id=user.id,
            leave_type_id=leave_type.id,
            proxy_user_id=proxy_user.id,  # 這裡使用隨機選擇的代理使用者 ID
            start_date=start_date,
            end_date=end_date,
            reason=fake.text(),
            status=status,
            days_count=(end_date - start_date).days,
            # 根據 status 設置 approved_at 和 rejection_reason
            approver_id=fake.random_element(elements=users).id if status == "Approved" else None,
            approved_at=datetime.now() if status == "Approved" else None,
            rejection_reason=fake.sentence() if status == "Rejected" else None,
        )

        db.add(leave_request)

    db.commit()

def generate_fake_notifications(db: Session, num_notifications: int = 20):
    print("Clearing existing notifications...")
    db.query(Notification).delete()  # 清空表格資料
    db.commit()  # 提交刪除操作
    
    print("Generating fake notifications...")
    leave_requests = db.query(LeaveRequest).all()
    
    if not leave_requests:
        raise ValueError("Please generate users data first.")

    for _ in range(num_notifications):
        # 隨機選擇一個請假請求
        leave_request = fake.random_element(elements=leave_requests, unique=True)
        user = leave_request.user_id
        related_id = leave_request.id

        # 隨機生成相關欄位
        related_to = fake.word()  # 有50%的機率讓 related_to 為 None
        is_read = fake.boolean()  # 隨機生成是否已讀的布林值

        notification = Notification(
            user_id=user,
            title=fake.sentence(),  # 隨機生成通知標題
            message=fake.text(),  # 隨機生成通知內容
            related_to=related_to,
            related_id=related_id,
            is_read=is_read,
        )
        db.add(notification)

    db.commit()

def generate_fake_leave_request_attachments(db: Session, num_attachments: int = 20):
    print("Clearing existing leave request attachments...")
    db.query(LeaveAttachment).delete()  # 清空 leave_attachments 表格資料
    db.commit()  # 提交刪除操作
    
    print("Generating fake leave request attachments...")

    # 確保存在請假請求資料
    leave_requests = db.query(LeaveRequest).all()
    if not leave_requests:
        raise ValueError("cannot generate attachments without leave requests")

    file_extensions = ['pdf', 'jpg', 'png', 'docx']

    for _ in range(num_attachments):
        lr = fake.random_element(elements=leave_requests)  # 隨機選擇一個請假請求
        ext = fake.random_element(elements=file_extensions)  # 隨機選擇檔案擴展名

        attachment = LeaveAttachment(
            leave_request_id=lr.id,  # 使用隨機選擇的請假請求 ID
            file_name=f"{fake.word()}.{ext}",  # 隨機生成檔案名稱與擴展名
            file_path=f"/fake/path/to/{fake.word()}.{ext}",  # 隨機生成檔案路徑
            file_type=ext,  # 檔案的 MIME 類型
            file_size=random.randint(100, 2048),  # 隨機生成檔案大小，單位：KB
            # uploaded_at 欄位會由資料庫自動處理，無需在這裡設定
        )

        db.add(attachment)

    db.commit()

def generate_fake_audit_logs(db: Session, num_logs: int = 20):
    print("Clearing existing audit logs...")
    db.query(AuditLog).delete()  # 清空 audit_logs 表格資料
    db.commit()  # 提交刪除操作

    print("Generating fake audit logs...")
    users = db.query(User).all()
    
    if not users:
        raise ValueError("請先建立使用者資料")

    for _ in range(num_logs):
        user = fake.random_element(elements=users)
        action = fake.random_element(elements=["create", "update", "delete"])
        entity_type = fake.random_element(elements=["leave_request", "user", "department"])
        entity_id = fake.random_int(min=1, max=1000)  # 隨機生成一個整數
        details: Dict[str, str] = {
            "field": fake.word(),
            "old_value": fake.word(),
            "new_value": fake.word()
        }  # 隨機生成變更細節

        audit_log = AuditLog(
            user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,  # 記得 details 是 JSON 格式
            ip_address=fake.ipv4(),  # 隨機生成 IP 地址
        )
        db.add(audit_log)

    db.commit()

def init_db():
    """Initialize the database with fake data."""
    db = SessionLocal()
    try:
        # generate_fake_departments(db)
        # generate_fake_users(db)
        # reset_manager_relations(db)
        reset_proxy_relations(db)
        # generate_fake_leave_types(db)
        # generate_fake_leave_quotas(db)
        # generate_fake_leave_requests(db)
        # generate_fake_notifications(db)
        # generate_fake_leave_request_attachments(db)
        # generate_fake_audit_logs(db)
        print("Fake data generation completed successfully.")
        
    # except Exception as e:
    #     print(f"Error generating fake data: {e}")
    #     db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()