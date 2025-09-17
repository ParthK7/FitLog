from fastapi import FastAPI, Depends, HTTPException, status, Security
from schemas import RegistrationModel, RegisterUserOut, LoginModel, LoginUserOut, ExerciseCreation, ExerciseCreationResponse
from database import get_db
from auth import passlib_hash_password, verify_password, create_jwt, decode_jwt, validate_jwt
from models.user import User
from models.exercise import Exercise
from models.workout import Workout
from models.workout_exercise import WorkoutExercise
from sqlalchemy.orm import Session
from sqlalchemy import select, or_ 
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import timedelta
from fastapi.openapi.utils import get_openapi


app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="Exercise API with JWT authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"bearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
async def first_function():
    return {"message" : "Hello!"}

@app.post("/register", response_model = RegisterUserOut)
async def register_user(userdata : RegistrationModel, db : Session = Depends(get_db)):
    statement = select(User).where(or_(User.email == userdata.email, User.username == userdata.username))
    existing_user = db.scalars(statement).first()

    if existing_user:
        if existing_user.email == userdata.email:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "A user with this email already exists."
            )
        
        if existing_user.username == userdata.username:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST, 
                detail = "A user with this username already exists."
            )
    
    hashed_password = passlib_hash_password(userdata.password)
    new_user = User(email = userdata.email, hashed_password = hashed_password, username = userdata.username)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "A database integrity error occurred"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred."
        )

    return new_user

@app.post("/login", response_model = LoginUserOut)
async def login_user(user : LoginModel, db : Session = Depends(get_db)):
    statement = select(User).where(or_(User.email == user.username_or_email, User.username == user.username_or_email))
    existing_user = db.scalars(statement).one_or_none()

    if not existing_user:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "No user with the given emailID or username found. Register the user and then continue to login."
        )
    
    entered_password = user.password
    stored_password = existing_user.hashed_password

    if not verify_password(entered_password, stored_password):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Incorrect password for given credentials."
        )
    
    active_time = timedelta(minutes = 15)
    jwt_token = create_jwt(
        payload = {"sub" : str(existing_user.id), "username" : existing_user.username},
        expires_delta = active_time
    )

    return {
        "id" : existing_user.id,
        "username" : existing_user.username,
        "email": existing_user.email,
        "jwt_token" : jwt_token,
        "message" : "Login Successful."
    }

@app.post("/create_exercise", response_model = ExerciseCreationResponse, openapi_extra={"security": [{"bearerAuth": []}]})
async def create_exercise(exercise_data : ExerciseCreation, user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = select(Exercise).where(Exercise.name == exercise_data.name.lower(), Exercise.user_id == user_id)
    existing_exercise = db.scalars(statement).one_or_none()

    if existing_exercise:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "An exercise with this name already exists. You might want to edit it to make changes."
        )

    new_exercise = Exercise(name = exercise_data.name.lower(), description = exercise_data.description, user_id = user_id)

    try:
        db.add(new_exercise)
        db.commit()
        db.refresh(new_exercise)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "A database integrity error occurred"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred."
        )

    return new_exercise
    
    
