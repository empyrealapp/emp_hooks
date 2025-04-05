from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import DBModel

T = TypeVar("T", bound=DBModel)


class DBService(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get(self, id: Any) -> T | None:
        return self.session.get(self.model, id)

    def get_all(self) -> list[T]:
        stmt = select(self.model)
        return list(self.session.scalars(stmt))

    def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        return instance

    def get_or_create(self, **kwargs) -> T:
        instance = self.session.query(self.model).filter_by(**kwargs).first()
        if instance:
            return instance
        return self.create(**kwargs)

    def update(self, id: Any, **kwargs) -> T | None:
        instance = self.get(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
        return instance

    def delete(self, id: Any) -> bool:
        instance = self.get(id)
        if instance:
            self.session.delete(instance)
            return True
        return False

    def filter_by(self, **kwargs) -> list[T]:
        return list(self.session.query(self.model).filter_by(**kwargs))
