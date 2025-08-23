from config import JWT_SECRET_KEY
import bcrypt

from datetime import datetime, timedelta, timezone
from jose import jwt


#bcrypt password hashing and checking functions
def passlib_hash_password(password : str) -> str:
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def verify_password(password : str, hashed_password : str) -> bool:
    password_bytes = password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


#JWT token functions
print(JWT_SECRET_KEY)


