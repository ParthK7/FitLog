from .base import Base
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.sql import func 
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(Integer, primary_key = True)

    username : Mapped[str] = mapped_column(String, unique = True, index = True)

    hashed_password : Mapped[str] = mapped_column(String)

    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        nullable = False
    )

    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        onupdate = func.now(),
        nullable = False
    )

    email : Mapped[str] = mapped_column(String, unique = True)