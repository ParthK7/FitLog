from pydantic import BaseModel, EmailStr
from datetime import datetime

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

