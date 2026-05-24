# /app/db/database.py
import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Missing required environment variable: DATABASE_URL")

DATABASE_URL_ADMIN = os.getenv("DATABASE_URL_ADMIN")
if not DATABASE_URL_ADMIN:
    raise RuntimeError("Missing required environment variable: DATABASE_URL_ADMIN")

_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

engine = create_engine(
    DATABASE_URL,
    echo=_ECHO,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
)
engine_admin = create_engine(
    DATABASE_URL_ADMIN,
    echo=_ECHO,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
)


def get_session():
    with Session(engine) as session:
        yield session


def get_session_admin():
    with Session(engine_admin) as session:
        yield session
