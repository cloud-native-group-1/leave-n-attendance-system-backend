from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
import logging
import sys
import json
import datetime
from sqlalchemy.engine.row import Row

from .routes import auth
from .routes import user 
from .routes import leave_balance
from .routes import leave
from .routes import calendar
from .routes import notification
from .routes import leave_type
from .routes import leave_attachment


# 配置更好的日誌記錄系統
class CustomFormatter(logging.Formatter):
    """自定義格式化程式，提供有顏色的日誌"""

    green = "\033[32m"
    cyan = "\033[36m"
    white = "\033[37m"
    yellow = "\033[33m"
    red = "\033[31m"
    bold_red = "\033[31;1m"
    reset = "\033[0m"
    
    time_format = "%Y-%m-%d %H:%M:%S"
    
    FORMATS = {
        logging.DEBUG: f"{green}%(asctime)s{reset} | {cyan}DEBUG{reset}    | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        logging.INFO: f"{green}%(asctime)s{reset} | {white}INFO{reset}     | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        logging.WARNING: f"{green}%(asctime)s{reset} | {yellow}WARNING{reset}  | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        logging.ERROR: f"{green}%(asctime)s{reset} | {red}ERROR{reset}    | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        logging.CRITICAL: f"{green}%(asctime)s{reset} | {bold_red}CRITICAL{reset} | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self.time_format)
        return formatter.format(record)


# 安全的 JSON 序列化函數
def safe_json_serialize(obj):
    """將對象安全地轉換為 JSON 可序列化格式"""
    if isinstance(obj, Row):
        return {key: value for key, value in obj._mapping.items()}
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "_asdict"):  # 支援 namedtuple
        return obj._asdict()
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    else:
        return str(obj)
        

# 將對象轉換為可讀字串的函數
def object_to_string(obj):
    """將對象轉換為可讀的字符串格式"""
    try:
        return json.dumps(obj, default=safe_json_serialize)
    except:
        if hasattr(obj, "__dict__"):
            return str(obj.__dict__)
        return str(obj)

# 配置根日誌記錄器
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 移除任何現有的處理器
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 添加到控制台的處理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)

# 添加函數到 builtins
__builtins__["object_to_dict"] = object_to_string
__builtins__["safe_json"] = lambda obj: json.dumps(obj, default=safe_json_serialize)

# 配置 FastAPI 的日誌記錄
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO)

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
    # Add your production domain when you deploy
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,     # Important for cookies
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(leave.router)
app.include_router(leave_balance.router)
app.include_router(calendar.router)
app.include_router(notification.router)
app.include_router(leave_type.router)
app.include_router(leave_attachment.router)


# Create database tables
@app.on_event("startup")
def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Leave and Attendance Management System"}
