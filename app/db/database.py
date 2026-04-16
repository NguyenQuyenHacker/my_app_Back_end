# /app/db/database.py
from sqlmodel import create_engine, Session   

DATABASE_URL = "postgresql://fastapi_user:123456@localhost:5432/banking_db"
DATABASE_URL_LANGGRAPH = "postgresql+psycopg://fastapi_user:123456@localhost:5433/banking_db"
DATABASE_URL_ADMIN = "postgresql+psycopg://fastapi_user:123456@localhost:5434/banking_db"

engine = create_engine(DATABASE_URL, echo=True)
engine_admin = create_engine(DATABASE_URL_ADMIN, echo=True)
engine_langgraph = create_engine(DATABASE_URL_LANGGRAPH, echo=True)

def get_session():
    with Session(engine) as session:
        yield session


def get_session_admin():
    with Session(engine_admin) as session:
        yield session

def get_session_langgraph():
    with Session(engine_langgraph) as session:
        yield session
