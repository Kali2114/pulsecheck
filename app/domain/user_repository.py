from typing import Protocol, runtime_checkable

from app.domain.user import User


@runtime_checkable
class UserRepository(Protocol):
    def add_user(self, user: User) -> User: ...

    def get_by_email(self, email: str) -> User | None: ...


class InMemoryUserRepository:
    def __init__(self):
        self._next_id = 1
        self.users: list[User] = []

    def add_user(self, user: User) -> User:
        user.id = self._next_id
        self._next_id += 1
        self.users.append(user)
        return user

    def get_by_email(self, email: str) -> User | None:
        for user in self.users:
            if user.email == email:
                return user
        return None
