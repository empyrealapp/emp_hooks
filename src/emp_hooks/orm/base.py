from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase


class DBModel(DeclarativeBase):
    @classmethod
    def create_all(cls, engine: Engine):
        cls.metadata.create_all(engine)
