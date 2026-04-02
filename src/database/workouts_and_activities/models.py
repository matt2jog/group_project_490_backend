from sqlmodel import Field
from typing import Optional
from enum import Enum
from src.database.base import SQLModelLU

class WorkoutType(Enum):
    REPETITION_BASED = "rep"
    DURATION_BASED = "duration"


class Equiptment(SQLModelLU):
    __tablename__ = "equiptment" # type: ignore
    
    id: int
    name: str
    description: str

class WorkoutEquiptment(SQLModelLU):
    __tablename__ = "workout_equiptment" # type: ignore
    
    id: int
    workout_id: int = Field(foreign_key="workout.id")
    equiptment_id: int = Field(foreign_key="equiptment.id")
    is_required: bool = Field(default=True)
    is_recomended: bool = Field(default=True)

class Workout(SQLModelLU):
    __tablename__ = "workout" # type: ignore
    
    id: int
    name: str
    description: str
    instructions: str
    workout_type: WorkoutType # str-based enum

class WorkoutActivity(SQLModelLU):
    __tablename__ = "workout_activity" # type: ignore


class WorkoutPlan(SQLModelLU):
    __tablename__ = "workout_plan" # type: ignore

class WorkoutPlanActivity(SQLModelLU):
    __tablename__ = "workout_plan_activity" # type: ignore

class Availability(SQLModelLU):
    __tablename__ = "activity" # type: ignore
