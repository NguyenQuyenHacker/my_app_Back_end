# /app/db/database.py
from sqlmodel import create_engine, Session   

DATABASE_URL = "postgresql://fastapi_user:123456@localhost:5432/banking_db"

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session