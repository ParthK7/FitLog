# 🏋️‍♂️ FitLog

A backend application built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Alembic**. It provides user authentication, exercise and workout management, and personal record tracking.

---

## 🚀 Features
- **User Authentication**
  - Registration and login using hashed passwords (bcrypt)
  - JWT-based authentication and authorization
- **Exercise Management**
  - CRUD endpoints to create, read, update, and delete exercises
  - Exercises are linked to individual users
- **Workout Management**
  - Create and manage workouts
  - Link workouts with multiple exercises (many-to-many relationship)
- **Personal Record (PR) Endpoint**
  - Query that joins exercises, workouts, and workout-exercises tables to display `(exercise_name, weight)` for a specific user.

---

## 🧱 Tech Stack
- **FastAPI** – Web framework for building APIs  
- **Uvicorn** – ASGI server to run FastAPI  
- **PostgreSQL (Docker)** – Database  
- **SQLAlchemy** – ORM for database modeling  
- **Alembic** – Database migrations  
- **python-jose** – JWT encoding and decoding  
- **bcrypt** – Password hashing  
- **python-dotenv** – Environment variable management

## ⚙️ Environment Setup

### Prerequisites

You need **Python 3.8+** and a running **PostgreSQL** instance.

### Installation

1.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv venv
    # For Linux/Mac
    source venv/bin/activate
    # For Windows
    venv\Scripts\activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary python-dotenv python-jose[cryptography] bcrypt
    ```
    *(You should also create a `requirements.txt` file by running `pip freeze > requirements.txt`)*

### Environment Variables

Create a **`.env`** file in the project root (and ensure it is added to `.gitignore`):

-----

## 🗄️ Project Structure

```
fitness-tracker-api/
│
├── app/
│   ├── main.py (or app.py)
│   ├── config.py             # Load environment variables
│   ├── database.py           # DB engine, session, and dependency
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── exercise.py
│   │   ├── workout.py
│   │   └── workoutexercise.py
│   ├── schemas/              # Pydantic schemas for request/response validation
│   ├── routes/               # FastAPI routers (API endpoints)
│   └── utils/                # Helper functions (e.g., password hashing, JWT)
│
├── alembic/                  # Alembic migration environment
│   ├── versions/
│   └── env.py
│
├── .env
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

-----

## 🔧 Database Connection (`app/database.py`)

The `database.py` module will handle the SQLAlchemy setup:

  - Import **`DATABASE_URL`** from `app/config.py`.
  - Create a SQLAlchemy **`Engine`** (connection factory).
  - Create a **`SessionLocal`** (session factory).
  - Define a **`get_db()`** dependency for FastAPI routes to manage DB sessions safely.

-----

## 🧩 Migrations (Alembic)

1.  **Initialize Alembic:**

    ```bash
    alembic init alembic
    ```

2.  **Configuration:**

      - In `alembic.ini`, leave `sqlalchemy.url =` blank.
      - In `alembic/env.py`, update to load `DATABASE_URL` from `.env`, import `Base` and models, and set:
        ```python
        target_metadata = Base.metadata
        ```

3.  **Generate Migration Script:**

    ```bash
    alembic revision --autogenerate -m "Create users table"
    ```

4.  **Apply Migrations:**

    ```bash
    alembic upgrade head
    ```

-----

## 🧠 Authentication

Authentication uses secure practices for password management and token generation:

  - **Password Hashing:** `bcrypt.hashpw()`
  - **Password Verification:** `bcrypt.checkpw()`
  - **JWT Encoding/Decoding:** via `python-jose`

### JWT Example

```python
def jwt_encode(payload: dict):
    # Uses SECRET_KEY and ALGORITHM from .env
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def jwt_decode(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

-----

## 🔒 Routes Overview

| Endpoint | Method | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `/register` | `POST` | Register a new user | ❌ |
| `/login` | `POST` | Login user and get JWT token | ❌ |
| `/exercises/` | `CRUD` | Manage exercises (Create, Read, Update, Delete) | ✅ |
| `/workouts/` | `CRUD` | Manage workouts (Create, Read, Update, Delete) | ✅ |
| `/pr/` | `GET` | Get user’s personal records | ✅ |

-----

## ▶️ Running the Server

Start the FastAPI application:

```bash
uvicorn app.main:app --reload
```

API will be available at:

  - **Base URL:** `http://localhost:8000`
  - **Interactive Docs (Swagger UI):** `http://localhost:8000/docs`

-----

## 🧾 Notes

  - **Alembic:** Use Alembic only when modifying schema (not for runtime CRUD changes).
  - **DB Sessions:** Always use **`get_db()`** dependency to safely handle DB sessions.
  - **Security:** **`.env`** should never be committed to version control.

-----


```
