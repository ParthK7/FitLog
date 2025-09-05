from fastapi import FastAPI, Depends, HTTPException, status
from schemas import RegistrationModel, RegisterUserOut, LoginModel, LoginUserOut
from database import get_db
from auth import *
from models.user import User
from sqlalchemy.orm import Session
from sqlalchemy import select, or_ 

app = FastAPI()

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
            detail = "A database integrity error occured"
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
        "message" : "Login Successfull"
    }





