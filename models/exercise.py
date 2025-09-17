from models.base import Base
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Exercise(Base):
    __tablename__ = "exercises"

    __table_args__ = (
        UniqueConstraint("user_id", "name"),
    )

    exercise_id : Mapped[int] = mapped_column(Integer, primary_key = True)

    name : Mapped[str] = mapped_column(String, nullable = False)

    description : Mapped[str] = mapped_column(String, nullable = True)

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

    user_id : Mapped[int] = mapped_column(ForeignKey("users.id", ondelete = "CASCADE"), nullable = False)
    user  : Mapped["User"] = relationship(back_populates = "exercises")

    workout_exercises : Mapped[list["WorkoutExercise"]] = relationship(back_populates = "exercise")
     