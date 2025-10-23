from fastapi import FastAPI, Depends, HTTPException, status, Security, Path
from schemas import RegistrationModel, RegisterUserOut, LoginModel, LoginUserOut, PRResponse, ExerciseCreation, ExerciseCreationResponse, AllExercisesRetrievalResponse, WorkoutRequest, WorkoutResponse, WorkoutExerciseRequest, WorkoutExerciseResponse
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
from sqlalchemy.sql import func


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

    by_id_stmt = select(Exercise).where(Exercise.exercise_id == exercise_id)
    exercise_obj = db.scalars(by_id_stmt).one_or_none()

    if not exercise_obj:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Exercise not found."
        )

    if exercise_obj.user_id != user_id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Forbidden: you do not have permission to access this exercise."
        )

    return exercise_obj

#4 Update exercise
@app.put("/exercises/{exercise_id}", response_model = AllExercisesRetrievalResponse, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def edit_exercise(exercise_details : ExerciseCreation, exercise_id : int = Path(..., title = "ID of the exercise to be edited."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])
    by_id_stmt = select(Exercise).where(Exercise.exercise_id == exercise_id)
    requested_exercise = db.scalars(by_id_stmt).one_or_none()

    if not requested_exercise:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Exercise not found."
        )

    if requested_exercise.user_id != user_id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Forbidden: you do not have permission to modify this exercise."
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
@app.delete("/exercises/{exercise_id}", status_code = status.HTTP_204_NO_CONTENT, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def delete_exercise(*, exercise_id : int = Path(..., title = "ID of the exercise to be deleted."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])
    by_id_stmt = select(Exercise).where(Exercise.exercise_id == exercise_id)
    exercise_to_be_deleted = db.scalars(by_id_stmt).one_or_none()

    if not exercise_to_be_deleted:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Exercise not found."
        )

    if exercise_to_be_deleted.user_id != user_id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Forbidden: you do not have permission to delete this exercise."
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
    
    return None

@app.post("/workouts", response_model = WorkoutResponse, openapi_extra = {"security": [{"bearerAuth" : []}]})
async def create_workout(workout_data : WorkoutRequest, user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])

    new_workout = Workout(
        name = workout_data.name,
        description = workout_data.description,
        date = workout_data.date,
        start_time = workout_data.start_time, 
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
    # First check existence
    by_id_stmt = select(Workout).where(Workout.workout_id == workout_id)
    requested_workout = db.scalars(by_id_stmt).one_or_none()

    if not requested_workout:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Workout not found."
        )

    if requested_workout.user_id != user_id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Forbidden: you do not have permission to access this workout."
        )

    return requested_workout

@app.put("/workouts/{workout_id}", response_model = WorkoutResponse, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def edit_workout(workout_details : WorkoutRequest, workout_id : int = Path(..., title = "ID of the exercise to be edited."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])
    by_id_stmt = select(Workout).where(Workout.workout_id == workout_id)
    requested_workout = db.scalars(by_id_stmt).one_or_none()

    if not requested_workout:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Workout not found."
        )

    if requested_workout.user_id != user_id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Forbidden: you do not have permission to modify this workout."
        )

    requested_workout.name = workout_details.name
    requested_workout.description = workout_details.description
    requested_workout.date = workout_details.date
    requested_workout.start_time = workout_details.start_time

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

@app.delete("/workouts/{workout_id}", status_code = status.HTTP_204_NO_CONTENT, openapi_extra = {"security" : [{"bearerAuth" : []}]})
async def delete_workout(*, workout_id : int = Path(..., title = "ID of the workout to be deleted."), user : dict = Security(validate_jwt), db : Session = Depends(get_db)):
    user_id = int(user["sub"])
    by_id_stmt = select(Workout).where(Workout.workout_id == workout_id)
    workout_to_be_deleted = db.scalars(by_id_stmt).one_or_none()

    if not workout_to_be_deleted:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Workout not found."
        )

    if workout_to_be_deleted.user_id != user_id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Forbidden: you do not have permission to delete this workout."
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
    # Ensure referenced Workout exists first (prioritize missing workout)
    workout_obj = db.scalars(select(Workout).where(Workout.workout_id == workout_exercise_data.workout_id)).one_or_none()
    if not workout_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found.")
    if workout_obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: you cannot add sets to this workout.")

    # Ensure referenced Exercise exists
    exercise_obj = db.scalars(select(Exercise).where(Exercise.exercise_id == workout_exercise_data.exercise_id)).one_or_none()
    if not exercise_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found.")
    if exercise_obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: you cannot use this exercise.")

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

# get all sets from a workout
@app.get("/workouts/{workout_id}/sets", response_model = list[WorkoutExerciseResponse], openapi_extra={"security": [{"bearerAuth": []}]})
async def get_all_sets_from_workout(workout_id: int = Path(..., title="ID of the workout to retrieve sets for."), user: dict = Security(validate_jwt), db: Session = Depends(get_db)):
    user_id = int(user["sub"])

    workout = db.scalars(select(Workout).where(Workout.workout_id == workout_id)).one_or_none()
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found.")
    if workout.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: you do not have permission to access sets for this workout.")

    sets_stmt = select(WorkoutExercise).where(WorkoutExercise.workout_id == workout_id)
    sets = db.scalars(sets_stmt).all()

    return sets
    
    return None
@app.get("/workouts/{workout_id}/sets/{exercise_id}/{set_number}", response_model = WorkoutExerciseResponse, openapi_extra={"security": [{"bearerAuth": []}]})
async def get_single_set_from_workout(workout_id: int = Path(..., title="Workout ID"), exercise_id: int = Path(..., title="Exercise ID"), set_number: int = Path(..., title="Set number"), user: dict = Security(validate_jwt), db: Session = Depends(get_db)):
    user_id = int(user["sub"])
    # find set by composite key
    stmt = select(WorkoutExercise).where(and_(WorkoutExercise.workout_id == workout_id, WorkoutExercise.exercise_id == exercise_id, WorkoutExercise.set_number == set_number))
    requested_set = db.scalars(stmt).one_or_none()
    if not requested_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found.")

    if requested_set.workout.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: you do not have permission to access this set.")

    return requested_set


@app.put("/workouts/{workout_id}/sets/{exercise_id}/{set_number}", response_model = WorkoutExerciseResponse, openapi_extra={"security": [{"bearerAuth": []}]})
async def edit_set_from_workout(workout_id: int = Path(..., title="Workout ID"), exercise_id: int = Path(..., title="Exercise ID"), set_number: int = Path(..., title="Set number"), set_details: WorkoutExerciseRequest = None, user: dict = Security(validate_jwt), db: Session = Depends(get_db)):
    user_id = int(user["sub"])
    stmt = select(WorkoutExercise).where(and_(WorkoutExercise.workout_id == workout_id, WorkoutExercise.exercise_id == exercise_id, WorkoutExercise.set_number == set_number))
    requested_set = db.scalars(stmt).one_or_none()
    if not requested_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found.")
    if requested_set.workout.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: you do not have permission to modify this set.")

    # Update fields - allow updating weight and reps (and set_number only if consistent)
    # If client wants to change identifying keys (exercise_id or set_number), safe approach is to reject or require delete+create.
    requested_set.weight = set_details.weight
    requested_set.reps = set_details.reps

    try:
        db.add(requested_set)
        db.commit()
        db.refresh(requested_set)
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

    return requested_set


@app.delete("/workouts/{workout_id}/sets/{exercise_id}/{set_number}", status_code=status.HTTP_204_NO_CONTENT, openapi_extra={"security": [{"bearerAuth": []}]})
async def delete_set_from_workout(workout_id: int = Path(..., title="Workout ID"), exercise_id: int = Path(..., title="Exercise ID"), set_number: int = Path(..., title="Set number"), user: dict = Security(validate_jwt), db: Session = Depends(get_db)):
    user_id = int(user["sub"])

    stmt = select(WorkoutExercise).where(and_(WorkoutExercise.workout_id == workout_id, WorkoutExercise.exercise_id == exercise_id, WorkoutExercise.set_number == set_number))
    set_to_delete = db.scalars(stmt).one_or_none()

    if not set_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found.")
    if set_to_delete.workout.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: you do not have permission to delete this set.")

    try:
        db.delete(set_to_delete)
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

    return None


@app.get("/prs", response_model = list[PRResponse], openapi_extra={"security": [{"bearerAuth": []}]})
async def return_prs(user: dict = Security(validate_jwt), db: Session = Depends(get_db)):
    user_id = int(user["sub"])

    statement = (
        select(Exercise.name, func.max(WorkoutExercise.weight).label("weight"))
        .join(Exercise)
        .join(Workout)
        .where(Workout.user_id == user_id)
        .group_by(Exercise.exercise_id, Exercise.name)
    )

    results = db.execute(statement).all()

    return [PRResponse.model_validate(row, from_attributes = True) for row in results]


