from pydantic import BaseModel, EmailStr

class LoginModel(BaseModel):
    username : str
    password : str

class RegistrationModel(BaseModel):
    username : str
    password : str
    email : EmailStr