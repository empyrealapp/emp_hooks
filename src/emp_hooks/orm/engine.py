import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def get_engine(db_uri: str | None = None) -> Engine:
    if db_uri is None:
        db_uri = f"sqlite:///{os.getenv("DEPLOYMENT_FILESYSTEM_PATH", ".")}/db.sqlite"
    assert db_uri is not None
    engine = create_engine(db_uri)
    return engine


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine)


def load_session(db_uri: str | None = None) -> Session:
    engine = get_engine(db_uri)
    session_factory = get_session_factory(engine)
    return session_factory()
