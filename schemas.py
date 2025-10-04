from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional

class RegistrationModel(BaseModel):
    username : str
    password : str
    email : EmailStr

class RegisterUserOut(BaseModel):
    id : int 
    username : str
    email : str

    class Config:
        from_attributes = True

class LoginModel(BaseModel):
    username_or_email : str
    password : str

class LoginUserOut(BaseModel):
    id : int
    username : str
    email : str
    jwt_token : str
    message : str


class ExerciseCreation(BaseModel):
    name : str
    description : str

class ExerciseCreationResponse(BaseModel):
    exercise_id : int
    name : str
    description : str
    user_id : int
    created_at : datetime
    updated_at : datetime

    class Config: 
        from_attributes = True

class AllExercisesRetrievalResponse(BaseModel):
    exercise_id : int
    name : str
    description : str
    created_at : datetime
    updated_at : datetime

    class Config:
        from_attributes = True

class WorkoutRequest(BaseModel):
    name : str
    description : Optional[str] = None
    date : date #YYYY-MM-DD
    start_time : datetime #YYYY-MM-DD HH:MI:SS
    end_time : Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkoutResponse(BaseModel):
    workout_id : int
    name : str
    description : Optional[str] = None
    date : date
    start_time : datetime
    end_time : Optional[datetime] = None
    created_at : datetime
    updated_at : datetime
    user_id : int

    class Config: 
        from_attributes = True

class WorkoutExerciseRequest(BaseModel):
    workout_id : int
    exercise_id : int
    set_number : int
    weight : int
    reps : int 

class WorkoutExerciseResponse(BaseModel):
    workout_id : int
    exercise_id : int
    set_number : int
    weight : int
    reps : int
    created_at : datetime
    updated_at : datetime