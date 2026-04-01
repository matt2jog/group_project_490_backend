from enum import Enum
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from src.database.base import SQLModelLU

class Client(SQLModelLU, table=True):
  __tablename__ = "client"  # type: ignore
  id: Optional[int] = Field(default=None, primary_key=True)
  payment_information_id : int = Field(foreign_key="payment_information.id")
  client_availability_id : int = Field(default=None, foreign_key="client_availability.id") #TODO should not be NONE, for MVP

class ClientAvailability(SQLModelLU, table=True):
  __tablename__ = "client_availability"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  id_weekly : bool

class FitnessGoalEnum(Enum):
  WEIGHT_LOSS = "weight loss"
  MAINTENENCE = "maintenence"
  MUSCLE_GAIN = "muscle gain"

class FitnessGoals(SQLModelLU, table=True):
  __tablename__ = "fitness_goals"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  client_id : int = Field(foreign_key="client.id")
  goal_enum : FitnessGoalEnum

class ClientWorkoutPlan(SQLModelLU, table=True):
  __tablename__ = "client_workout_plan"  # type: ignore
  id: Optional[int] = Field(default=None, primary_key=True)
  client_id : int = Field(foreign_key="client.id")
  workout_plan_id : int = Field(foreign_key="workout_plan.id")
  start_time : datetime
  end_time : datetime
