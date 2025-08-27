from config import JWT_SECRET_KEY
import bcrypt

from datetime import datetime, timedelta, timezone
from jose import jwt, exceptions


#bcrypt password hashing and checking functions
def passlib_hash_password(password : str) -> str:
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def verify_password(password : str, hashed_password : str) -> bool:
    password_bytes = password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


#JWT token functions
def create_jwt(payload : dict, expires_delta : timedelta | None = None) -> str:
    to_encode = payload.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp" : expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm = "HS256")
    return encoded_jwt

def decode_jwt(token : str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithm = "HS256")
        return payload
    except exceptions.JWTError as e:
        print("Error :", e)
        return None
    except exceptions.ExpiredSignatureError:
        print("Error : Token has expired.")
        return None
    except Exception as e:
        print("Error : An unexpected error occured ->", e)
        return None
