import os
from sqlmodel import create_engine, Session
from src import config

DATABASE_URL = config.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)

# dependency that FastAPI can inject

def get_session():
    with Session(engine) as session:
        yield session
