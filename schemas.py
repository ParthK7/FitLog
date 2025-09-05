from pydantic import BaseModel, EmailStr

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

