from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date

class Client(SQLModel, table=True):
  __tablename__ = "client"
  id: int = Field(primary_key=True)
  payment_information_id : int = Field(foreign_key="payment_information.id")
  client_availability_id : int = Field(foreign_key="client_availability.id")
  last_update : datetime

class PaymentInformation(SQLModel, table=True):
  __tablename__ = "payment_information"
  id : int = Field(primary_key=True)
  ccnum : str
  cv : str
  exp_date : date
  last_updated : datetime
