from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Default to SQLite for local dev, overridable via env vars for Postgres
    DATABASE_URL: str = "sqlite:///./local.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# SQLite specific argument required for thread safety
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Handle DB disconnects gracefully
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency generator for database sessions.
    Ensures the session is closed after the request is processed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()