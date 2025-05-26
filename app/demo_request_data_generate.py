from models.leave_request import LeaveRequest
from models.leave_type import LeaveType
from models.leave_request_attachment import LeaveAttachment
from models.leave_quota import LeaveQuota
from models.user import User
from models.manager import Manager
from models.notification import Notification
from sqlalchemy.orm import Session
from utils.auth import get_password_hash
from database import SessionLocal
import random
from datetime import timedelta, date


leave_types = [
    {"name": "事假"},
    {"name": "病假"},
    {"name": "特休假"},
    {"name": "公假"},
]
query_users = [
    # {"employee_id": "EMP001"},
    {"employee_id": "EMP002"},
    {"employee_id": "EMP003"},
    {"employee_id": "EMP004"},
    {"employee_id": "EMP005"},
    {"employee_id": "EMP006"},
    {"employee_id": "EMP007"},
]

def generate_demo_leave_type(db: Session):
    # 定義請假類型資料
    leave_types = [
        {"name": "事假", "description": "因私事需要請假", "requires_attachment": False, "color_code": "#FF5733"},
        {"name": "病假", "description": "因健康問題需要請假", "requires_attachment": False, "color_code": "#33FF57"},
        {"name": "特休假", "description": "每年享有的帶薪休假", "requires_attachment": False, "color_code": "#3357FF"},
        {"name": "公假", "description": "因公事需要請假", "requires_attachment": True, "color_code": "#FF33A1"},
    ]

    # 插入請假類型資料到資料庫
    print("Creating demo leave types...")
    for leave_type in leave_types:
        new_leave_type = LeaveType(
            name=leave_type["name"],
            description=leave_type["description"],
            requires_attachment=leave_type["requires_attachment"],
            color_code=leave_type["color_code"],
        )
        db.add(new_leave_type)

    db.commit()  # 儲存資料
    print("create demo leave types successfully.")

def generate_demo_leave_quotas(db: Session):
    plus = 0
    for user in query_users:
        user = db.query(User).filter(User.employee_id == user["employee_id"]).first()
        if user.id == 41:
            plus = 14        
        elif user.id == 42 or user.id == 43:  # 中階主管有額外的特休假
            plus = 7 
        
        for leave_type in leave_types:
            # 假設每個員工每年有20天的特休假
            leave_type_id = db.query(LeaveType).filter(LeaveType.name == leave_type["name"]).first()
            if leave_type["name"] == "特休假":
                days_count = 7 + plus
            elif leave_type["name"] == "事假":
                days_count = 14
            elif leave_type["name"] == "病假":
                days_count = 30
            elif leave_type["name"] == "公假":
                days_count = 365

            # 創建請假配額
            leave_quota = LeaveQuota(
                user_id=user.id,
                leave_type_id=leave_type_id.id,
                year=2025,
                quota=days_count,
            )
            db.add(leave_quota)

    db.commit()  # 儲存資料
    print("Create demo leave quotas successfully.")



def generate_leave_requests_for_supervisors(db: Session):
 
    for user in query_users:
        
        # 查找當前使用者和其主管和代理人
        curr_user = db.query(User).filter(User.employee_id == user["employee_id"]).first()
        manager = db.query(Manager).filter(Manager.user_id == curr_user.id).first()
        proxy_users = db.query(Manager).filter(Manager.manager_id == manager.manager_id).all()
        while 1:
            proxy = random.choice(proxy_users)
            if proxy.user_id != curr_user.id:  # 確保代理人不是自己
                break
        
        
        print(f"{curr_user.first_name}{curr_user.last_name} make leave requests to manager {manager.manager_id} and proxy {proxy.user_id}")
        for i in range(10):  # 為每位主管生成20筆請假資料
            # 隨機生成請假時間
            start_date = random_date(date(2024, 5, 1), date(2024, 12, 20))
            end_date = start_date + timedelta(days=random.randint(1, 5))  # 假設請假天數為1到5天之間
            approved_at = start_date - timedelta(days=random.randint(3, 7))  # 假設批准時間在請假開始前3到7天之間

            # 隨機決定請假狀態
            if i < 9:  # 前9筆是 approved
                status = "approved"
                approver_id = manager.manager_id  
            else:  # 最後1筆是 rejected
                status = "rejected"
                approver_id = manager.manager_id  
                rejection_reason = "無法批准，業務需要過多"

            # 隨機選擇一個請假類型
            leave_type = random.choice(leave_types)

            # 隨機生成請假原因
            if leave_type["name"] == "公假":
                reason = "因公事需要處理"
            elif leave_type["name"] == "病假":
                reason = "因健康問題需要休息"
            elif leave_type["name"] == "特休假":
                reason = "享受年度特休假"
            else:  # 事假
                reason = "因私事需要處理"
            
            leave_type_id = db.query(LeaveType).filter(LeaveType.name == leave_type["name"]).first()


            # 生成請假請求
            leave_request = LeaveRequest(
                request_id=f"REQ{curr_user.id}_{i+1}",
                user_id=curr_user.id,
                leave_type_id=leave_type_id.id,
                proxy_user_id=proxy.user_id,  
                start_date=start_date,
                end_date=end_date,
                start_half_day=False,
                end_half_day=False,
                reason=reason,
                status=status,
                days_count=(end_date - start_date).days,
                approver_id=approver_id,
                approved_at=approved_at if status == "approved" or status == "rejected" else None,
                rejection_reason=rejection_reason if status == "rejected" else None
            )
            db.add(leave_request)
        # break

    db.commit()  # 儲存資料
    print("create demo leave requests for users successfully.")

def random_date(start_date, end_date):
    """生成隨機日期在指定範圍內"""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_demo_notification(db: Session):
    # 這裡可以添加生成通知的邏輯
    for user in query_users:
        user = db.query(User).filter(User.employee_id == user["employee_id"]).first()
        leave_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id == user.id).all()
        for leave_request in leave_requests:
            print(f"Creating notifications for leave request {leave_request.request_id} of user {user.first_name} {user.last_name}")
            receivers = [leave_request.approver_id, user.id, leave_request.proxy_user_id]
            approve_title = [
                "有一筆新假單需要您的審核",
                "您的假單已被主管批准!",
                "您已被指派為假單的職務代理人",
            ]
            approve_messages = [
                f"您有新的請假申請 {leave_request.request_id} 待審核。",
                f"您的假單 (id:{leave_request.request_id}) 已被批准!",
                f"您已被指派於{leave_request.start_date}至{leave_request.end_date}擔任{user.first_name}{user.last_name}的職務代理人。"
            ]
            reject_title = [
                "有一筆新假單需要您的審核",
                "您的假單已被否決!",
            ]
            reject_messages = [
                f"您有新的請假申請 {leave_request.request_id} 待審核。",
                f"您的假單 (id:{leave_request.request_id}) 已被否決!",
            ]
            if leave_request.status == "approved":
                # create three notifications for each approved leave request
                # 1. manager receive request
                # 2. proxy receive request result
                # 3. user receive request result
                for i in range(3):
                    notification = Notification(
                        user_id=receivers[i], # 收到這筆通知的人
                        title=approve_title[i],
                        message= approve_messages[i],
                        related_id=leave_request.id,  # 關聯的請假申請ID
                        is_read=True,
                    )
                    db.add(notification)
            elif leave_request.status == "rejected":
                # create two notifications for each rejected leave request
                # 1. manager receive request
                # 2. user receive request result
                for i in range(2):
                    notification = Notification(
                        user_id=receivers[i],  # 收到這筆通知的人
                        title=reject_title[i],
                        message= reject_messages[i],
                        related_id=leave_request.id,  # 關聯的請假申請ID
                        is_read=True,
                    )
                    db.add(notification)
        print(f"Notification for {user.first_name} {user.last_name} leave requests created successfully.")
        # break
    db.commit()  # 儲存資料
    print("create demo notifications successfully.")


def update_leave_requests_for_user(db: Session, user_id: int):
    # 設定新的日期範圍
    new_start_date = date(2025, 1, 1)
    new_end_date = date(2025, 5, 27)

    # 查詢該用戶的所有請假請求
    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id == user_id).all()
    print(f"Updating leave requests for user {user_id}, found {len(leave_requests)} requests.")
    holidays = 0 # 用於計算特休假天數 id: 100
    sick_days = 0  # 用於計算病假天數 id: 101
    events = 0 # 用於計算事假天數 id: 102


    for leave_request in leave_requests:
        # 隨機生成新的 start_date 和 end_date
        start_date = random_date(new_start_date, new_end_date)
        end_date = start_date + timedelta(days=random.randint(1, 3))  # 假設請假天數為 1 到 5 天之間
        # 計算新的 days_count
        days_count = (end_date - start_date).days + 1.0

        if leave_request.leave_type_id == 100:
            holidays += days_count  # 特休假
        elif leave_request.leave_type_id == 101:
            sick_days += days_count
        elif leave_request.leave_type_id == 102:
            events += days_count
        # 設定新的 approved_at，為 start_date 前 1 到 7 天內的一個時間
        approved_at = start_date - timedelta(days=random.randint(1, 7))

        # 更新請假請求的字段
        leave_request.start_date = start_date
        leave_request.end_date = end_date
        leave_request.days_count = days_count
        leave_request.approved_at = approved_at

        db.add(leave_request)
    print(f"Updated leave requests for user {user_id}: holidays={holidays}, sick_days={sick_days}, events={events}")
    db.commit()  # 提交更改

def count_leave_quotas(db: Session, user_id: int):
    # 查詢該用戶的所有請假配額
    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id == user_id).all()
    holidays = 0 # 用於計算特休假天數 id: 100
    sick_days = 0  # 用於計算病假天數 id: 101
    events = 0 # 用於計算事假天數 id: 102
    for leave_request in leave_requests:
        days_count = leave_request.days_count  # 計算請假天數 
        if leave_request.leave_type_id == 100:
            holidays += days_count  # 特休假
        elif leave_request.leave_type_id == 101:
            sick_days += days_count
        elif leave_request.leave_type_id == 102:
            events += days_count
    print(f"User {user_id} leave quotas: holidays={holidays}, sick_days={sick_days}, events={events}")

def update_notification_read_status(db: Session, user_id: int):
    # 查詢該用戶的所有通知
    notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
    print(f"Updating read status for {len(notifications)} notifications for user {user_id}.")
    
    for notification in notifications:
        if notification.title == "您的假單已被主管批准!":
            notification.is_read = False
            db.add(notification)
    
    db.commit()  # 提交更改
    print(f"Updated read status for user {user_id} notifications successfully.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        # generate_demo_leave_type(db)
        # generate_demo_leave_quotas(db)
        # generate_leave_requests_for_supervisors(db)
        # generate_demo_notification(db)
        for i in range(42, 48):
            # update_leave_requests_for_user(db, i)  # 假設要更新的用戶ID為1
            # count_leave_quotas(db, i)
            update_notification_read_status(db, i)       
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
    print("Demo data generation completed.")