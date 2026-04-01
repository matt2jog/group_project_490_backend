from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

from src.database.base import SQLModelLU

class Account(SQLModelLU, table=True):
  __tablename__ = "account" # type: ignore
  id: Optional[int] = Field(default=None, primary_key=True)
  name: Optional[str] = None
  email: str

  # auth, ONE of these needs to be here
  hashed_password: Optional[str] = None
  gcp_user_id: Optional[str] = None
  
  # demo
  gender: Optional[str] = None
  bio: Optional[str] = None
  age: Optional[int] = None

  pfp_url: Optional[str] = None # pull from public supa bucket (private signing is too much rn)

  # role relations
  client_id: Optional[int] = Field(default=None, foreign_key="client.id") # all roles are clients by default
  coach_id: Optional[int] = Field(default=None, foreign_key="coach.id")
  admin_id: Optional[int] = Field(default=None, foreign_key="admin.id")

  created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)