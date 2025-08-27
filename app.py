from fastapi import FastAPI, Depends, HTTPException, status
from schemas import RegistrationModel
from database import get_db
from auth import *
from models.user import User
from sqlalchemy.orm import Session
from sqlalchemy import select, or_ 

app = FastAPI()

@app.get("/")
async def first_function():
    return {"message" : "Hello!"}

@app.post("/register")
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
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}


