from fastapi import FastAPI, Depends, HTTPException, status, Security, Path
from schemas import RegistrationModel, RegisterUserOut, LoginModel, LoginUserOut, ExerciseCreation, ExerciseCreationResponse, AllExercisesRetrievalResponse, WorkoutRequest, WorkoutResponse, WorkoutExerciseRequest, WorkoutExerciseResponse
from database import get_db
from auth import passlib_hash_password, verify_password, create_jwt, decode_jwt, validate_jwt
from models.user import User
from models.exercise import Exercise
from models.workout import Workout
from models.workout_exercise import WorkoutExercise
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
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

# CRUD operations for Exercises:-
# 1. CREATE
@app.post("/exercises", response_model = ExerciseCreationResponse, openapi_extra={"security": [{"bearerAuth": []}]})
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
            detail = "A database integrity error occurred."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred."
        )

    return new_exercise

# 2. READ all exercises for a user
@app.get("/exercises", response_model = list[AllExercisesRetrievalResponse], openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def get_all_exercises_for_user(user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = select(Exercise).where(Exercise.user_id == user_id)
    all_exercises = db.scalars(statement).all()

    return all_exercises

#3 READ exercise by exercise_id
@app.get("/exercises/{exercise_id}", response_model = AllExercisesRetrievalResponse, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def get_single_exercise(exercise_id : int = Path(..., title = "ID of exercise to retrieve."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = select(Exercise).where(and_(Exercise.exercise_id == exercise_id , Exercise.user_id == user_id))
    requested_exercise = db.scalars(statement).one_or_none()

    if not requested_exercise:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Exercise not found or does not belong to this user."
        )
    
    return requested_exercise

#4 Update exercise
@app.put("/exercises/{exercise_id}", response_model = AllExercisesRetrievalResponse, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def edit_exercise(exercise_details : ExerciseCreation, exercise_id : int = Path(..., title = "ID of the exercise to be edited."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = select(Exercise).where(and_(Exercise.exercise_id == exercise_id, Exercise.user_id == user_id))
    requested_exercise = db.scalars(statement).one_or_none()

    if not requested_exercise:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Exercise not found or does not belong to this user."
        )
    
    requested_exercise.name = exercise_details.name.lower()
    requested_exercise.description = exercise_details.description

    try:
        db.add(requested_exercise)
        db.commit()
        db.refresh(requested_exercise)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "A database integrity error occurred.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "A database error occurred."
        )

    return requested_exercise

#5 Delete exercise
@app.delete("/exercises/{exercise_id}", openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def delete_exercise(*, exercise_id : int = Path(..., title = "ID of the exercise to be deleted."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])
    
    statement = select(Exercise).where(and_(Exercise.exercise_id == exercise_id, Exercise.user_id == user_id))
    exercise_to_be_deleted = db.scalars(statement).one_or_none()

    if not exercise_to_be_deleted:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Exercise not found or does not belong to the user."
        )

    try:
        db.delete(exercise_to_be_deleted)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "A database integrity error occurred.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "A database error occurred."
        )
    
    return status.HTTP_204_NO_CONTENT

@app.post("/workouts", response_model = WorkoutResponse, openapi_extra = {"security": [{"bearerAuth" : []}]})
async def create_workout(workout_data : WorkoutRequest, user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    new_workout = Workout(
        name = workout_data.name,
        description = workout_data.description,
        date = workout_data.date,
        start_time = workout_data.start_time, 
        end_time = workout_data.end_time,
        user_id = user_id
    )

    try:
        db.add(new_workout)
        db.commit()
        db.refresh(new_workout)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "A database integrity error occurred."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred."
        )
    
    return new_workout

@app.get("/workouts", response_model = list[WorkoutResponse], openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def get_all_workouts_for_user(user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = select(Workout).where(Workout.user_id == user_id)
    all_workouts = db.scalars(statement).all()

    return all_workouts

@app.get("/workouts/{workout_id}", response_model = WorkoutResponse, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def get_single_workout(workout_id : int = Path(..., title = "ID of workout to retrieve."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = select(Workout).where(and_(Workout.workout_id == workout_id , Workout.user_id == user_id))
    requested_workout = db.scalars(statement).one_or_none()

    if not requested_workout:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Workout not found or does not belong to this user."
        )
    
    return requested_workout

@app.put("/workouts/{workout_id}", response_model = WorkoutResponse, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def edit_workout(workout_details : WorkoutRequest, workout_id : int = Path(..., title = "ID of the exercise to be edited."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = select(Workout).where(and_(Workout.workout_id == workout_id, Workout.user_id == user_id))
    requested_workout = db.scalars(statement).one_or_none()

    if not requested_workout:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Exercise not found or does not belong to this user."
        )

    requested_workout.name = workout_details.name
    requested_workout.description = workout_details.description
    requested_workout.date = workout_details.date
    requested_workout.start_time = workout_details.start_time
    requested_workout.end_time = workout_details.end_time

    try:
        db.add(requested_workout)
        db.commit()
        db.refresh(requested_workout)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "A database integrity error occurred.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "A database error occurred."
        )

    return requested_workout

@app.delete("/workouts/{workout_id}", openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def delete_workout(*, workout_id : int = Path(..., title = "ID of the workout to be deleted."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])
    
    statement = select(Workout).where(and_(Workout.workout_id == workout_id, Workout.user_id == user_id))
    workout_to_be_deleted = db.scalars(statement).one_or_none()

    if not workout_to_be_deleted:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Exercise not found or does not belong to the user."
        )

    try:
        db.delete(workout_to_be_deleted)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "A database integrity error occurred.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "A database error occurred."
        )
    
    return status.HTTP_204_NO_CONTENT

#Create Workout Exercise
@app.post("/workoutexercises", response_model = WorkoutExerciseResponse, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def create_workoutexercise(workout_exercise_data : WorkoutExerciseRequest, user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    query = select(
        and_(
            select(Exercise).where(Exercise.exercise_id == workout_exercise_data.exercise_id, Exercise.user_id == user_id).exists(),
            select(Workout).where(Workout.workout_id == workout_exercise_data.workout_id, Workout.user_id == user_id).exists()
        )
    )

    result = db.scalars(query).one_or_none()

    if not result:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Resource not found or unauthorized access."
        )

    new_workout_exercise = WorkoutExercise(**workout_exercise_data.model_dump())

    try:
        db.add(new_workout_exercise)
        db.commit()
        db.refresh(new_workout_exercise)
        return new_workout_exercise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "An entry with the given workout, exercise, and set number already exists.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "A database error occurred."
        )
