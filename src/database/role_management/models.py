from sqlmodel import SQLModel, Field
from typing import Optional
from src.database.base import SQLModelLU
from datetime import datetime
from src.database.client.models import Client
from src.database.coach.models import Coach
from src.database.admin.models import Admin

class Roles(SQLModelLU, table=True):
  __tablename__ = "roles"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  name : str

class RolePromotionResolution(SQLModelLU, table=True):
  __tablename__ = "role_promotion_resolution" # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  admin_id : int = Field(foreign_key="admin.id")
  client_id : int = Field(foreign_key="client.id")
  role_id : int = Field(foreign_key="roles.id")
  is_approved : bool

class CoachRequest(SQLModelLU, table=True):
  __tablename__ = "coach_request"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  coach_id : int = Field(foreign_key="coach.id")
  created_on : datetime = datetime.utcnow()
  role_promotion_resolution_id : Optional[int] = Field(default=None, foreign_key="role_promotion_resolution.id")
