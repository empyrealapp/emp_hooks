import random

from emp_hooks.orm import get_engine, get_session_factory, select

from .models import Teacher, User

engine = get_engine()
session_factory = get_session_factory(engine)

with session_factory.begin() as session:
    random_id = random.randint(0, 1000000)
    session.add(User(name=f"John {random_id}"))
    session.add(Teacher(name=f"Teacher {random_id}"))
    session.commit()

users = session.execute(select(User)).scalars().all()
print("USERS:")
print("------")
for user in users:
    print(user.name)

print("\nTEACHERS:")
print("--------")
teachers = session.execute(select(Teacher)).scalars().all()
for teacher in teachers:
    print(teacher.name)
