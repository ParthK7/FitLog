from models.base import Base
from sqlalchemy.sql import func
from sqlalchemy import Integer, DateTime, String, PrimaryKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    __table_args__ = (
        PrimaryKeyConstraint("workout_id", "exercise_id", "set_number"),
    )

    # session_id : Mapped[int] = mapped_column(Integer)

    set_number : Mapped[int] = mapped_column(Integer, nullable = False)

    weight : Mapped[int] = mapped_column(Integer, nullable = False)

    reps : Mapped[int] = mapped_column(Integer, nullable = False)

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

    workout_id : Mapped[int] = mapped_column(ForeignKey("workouts.workout_id", ondelete = "CASCADE"), nullable = False)

    exercise_id : Mapped[int] = mapped_column(ForeignKey("exercises.exercise_id"), nullable = False)

    workout : Mapped["Workout"] = relationship(back_populates = "workout_exercises")

    exercise : Mapped["Exercise"] = relationship(back_populates = "workout_exercises")


