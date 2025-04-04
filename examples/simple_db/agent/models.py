from emp_hooks.orm import DBModel, Mapped, mapped_column


class User(DBModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)


class Teacher(DBModel):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)


class Homework(DBModel):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)


class ETC(DBModel):
    __tablename__ = "etc"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
