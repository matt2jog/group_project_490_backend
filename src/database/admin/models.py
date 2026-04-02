from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from src.database.base import SQLModelLU

class Admin(SQLModelLU, table=True):
    __tablename__ = "admin"  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
