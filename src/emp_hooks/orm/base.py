from typing import Self

from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session


class DBModel(DeclarativeBase):
    @classmethod
    def create_all(cls, engine: Engine):
        cls.metadata.create_all(engine)

    def get_or_create(self, session: Session) -> Self:
        instance = session.query(self.__class__).filter_by(**self.to_dict()).first()
        if instance:
            return instance
        session.add(self)
        return self

    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in self.__table__.c}
