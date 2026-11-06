import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

def make_database_url():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5438")
    name = os.getenv("DB_NAME", "sleep_tracker")
    user = os.getenv("DB_USER", "sleep_user")
    password = os.getenv("DB_PASSWORD", "1234")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

DATABASE_URL = os.getenv("DATABASE_URL", make_database_url())
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

class Base(DeclarativeBase):
    pass

def get_db():
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
