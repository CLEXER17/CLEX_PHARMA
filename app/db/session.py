from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.settings import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    settings.database_url_sync,
    connect_args={"check_same_thread": False}
    if settings.database_url_sync.startswith("sqlite")
    else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app.db import models  # noqa: F401

    Base.metadata.create_all(engine)
