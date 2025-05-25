# Leave and attendance backend system
## Overview
This project provides the backend for the **Leave and Attendance Management System**. The system is built using **FastAPI** and is designed to manage employee attendance, leave requests, and provide an API interface for frontend applications to interact with.

The backend is modular, scalable, and follows clean architecture principles to separate concerns effectively. It is containerized using **Docker** and deployed on **Google Cloud Platform (GCP)** using **Google App Engine (GAE)**.

## Tech Stack
- **FastAPI**: Python web framework for building APIs.
- **SQLAlchemy**: ORM for database operations.
- **PostgreSQL**: Relational database to store leave, attendance, and user data.
- **Uvicorn**: ASGI (Asynchronize Service Gateway Interface) server to run the FastAPI application.
- **Pydantic**: Data validation for API requests.
- **Docker**: Containerization for easier deployment.
- **Google Cloud Platform (GCP)**: For deployment (App Engine).
- **Alembic**: For database migrations.

## Prerequisites
Before you begin, ensure you have the following installed on your system:
- **Python 3.11**
- **Docker**
- **PostgreSQL** (or Cloud SQL for GCP database management)
- **Google Cloud SDK** (for deployment to GCP)
- **Git** (to clone the repository)

## Setting Up the Development Environment

- Clone the repository to your local machine:

```bash
git clone https://github.com/your-username/leave-attendance-backend.git
cd leave-attendance-backend
```

- Set up the Virtual Environment
```
python -m venv venv
source venv/bin/activate # mac/linux
venv\Scripts\activate # windows
```

- Install Dependencies
```
pip install -r requirement.txt
```

- Create Environment Variables -> 連上GCP上的DB
Create a `.env` file in the root directory of the project to store environment-specific variables like the database URL and secret keys.
```
DATABASE_URL=postgresql://username:password@localhost:5432/yourdatabase
JWT_SECRET=your-secret-key
```

- Run the Application Locally
```
uvicorn app.main:app --reload
```


- Run Unit-Tests (have not been written yet, but you can add them in the tests folder)


- Run Docker Container
To run the application in a Docker container, you need to build the Docker image and then run it. Here’s how you can do that:
- Build the Docker image:
```bash
docker-compose up --build
```
After this, you will create two containers: one for the FastAPI application and another for PostgreSQL. 
The FastAPI application will be accessible at `http://localhost:8000`.


- Run Database Migrations (You can currently skip this step, as the database is already created in the docker-compose file)
```
alembic init migrations
```
Configure alembic.ini to use your DATABASE_URL: Update the sqlalchemy.url in alembic.ini to point to your database.
After each change in the models, you need to create a new migration script and apply it to the database:
```
alembic upgrade head
```

## Folder Structure (Temporary)

``` 
leave-attendance-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # Entry point of FastAPI app
│   ├── database.py                  # Database connection
│   ├── models/                      # Database models
│   │   ├── user.py
│   │   ├── leave.py
│   │   └── attendance.py
│   ├── schemas/                     # Pydantic models (data validation)
│   │   ├── user.py
│   │   ├── leave.py
│   │   └── attendance.py
│   ├── crud/                        # CRUD operations for interacting with DB
│   │   ├── user.py
│   │   ├── leave.py
│   │   └── attendance.py
│   ├── routes/                      # API route definitions
│   │   ├── auth.py
│   │   ├── leave.py
│   │   └── attendance.py
│   ├── tests/                       # Unit tests
│   ├── config.py                    # Configuration (DB, JWT, etc.)
│   └── .env                         # Environment variables -> remember to add this in your local
├── alembic.ini                      # Alembic configuration
├── migrations/                      # Database migrations -> after running alembic init migrations, it will create this folder
│   ├── versions/                    # Migration scripts
│   ├── env.py                       # Alembic environment file -> remember to modify database URL in this file
└── requirements.txt                 # Project dependencies
```

## How to run the unit test:
```
	export $(cat app/.env | grep -v ^# | xargs) && pytest --cov=app --cov-report=term-missing
```
## TODO

- 下載 postgresql: https://www.postgresql.org/download/
- 連上GCP上的DB
- ER-D圖
- 假資料生成操作