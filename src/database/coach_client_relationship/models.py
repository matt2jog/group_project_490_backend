from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from src.database.base import SQLModelLU

class ClientCoachRequest(SQLModelLU, table=True):
  __tablename__ = "client_coach_request"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  is_accepted : Optional[bool]
  client_id : int = Field(foreign_key="client.id")
  coach_id : int = Field(foreign_key="coach.id")
  created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)  

class ClientCoachRelationship(SQLModelLU, table=True):
  __tablename__ = "client_coach_relationship"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  request_id : int = Field(foreign_key="client_coach_request.id")
  create_at : datetime
  is_active : bool
  coach_blocked : bool
  client_blocked: bool

class Chat(SQLModelLU, table=True):
  __tablename__ = "chat"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  client_coach_relationship_id : int = Field(foreign_key="client_coach_relationship.id")

class ChatMessage(SQLModelLU, table=True):
  __tablename__ = "chat_message"  # type: ignore
  id : Optional[int] = Field(default=None, primary_key=True)
  chat_id : int = Field(foreign_key="chat.id")
  from_account_id : int = Field(foreign_key="account.id")
  is_read : bool
