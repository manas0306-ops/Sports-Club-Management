import os
import warnings
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

def connect():
    url = make_url(os.getenv("DATABASE_URL") or "sqlite:///club.db")
    if url.drivername in ("postgres", "postgresql"):
        url = url.set(drivername="postgresql+psycopg")
    if url.get_backend_name() == "postgresql":
        try:
            engine = create_engine(url, connect_args={"connect_timeout": 3}, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return engine
        except Exception as exc:
            warnings.warn(f"PostgreSQL unavailable ({type(exc).__name__}); using local club.db")
            url = make_url("sqlite:///club.db")
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 20})
    @event.listens_for(engine, "connect")
    def configure(db, _):
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=20000")
    return engine

engine = connect()
Session = sessionmaker(engine, expire_on_commit=False)
