from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./troopsite.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _upgrade_sqlite_schema_if_needed()


def _upgrade_sqlite_schema_if_needed() -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(members)"))
        }
        if columns and "age" not in columns:
            connection.execute(text("ALTER TABLE members ADD COLUMN age INTEGER"))
        if columns and "grade" not in columns:
            connection.execute(text("ALTER TABLE members ADD COLUMN grade VARCHAR(5)"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
