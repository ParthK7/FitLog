from pydantic import BaseModel, EmailStr

class LoginModel(BaseModel):
    username : str
    password : str

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