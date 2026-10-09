from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.exceptions import EmailAlreadyRegistered
from app.domain.user import User
from app.infrastructure.models import UserModel


class SQLAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_user(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            hashed_password=user.hashed_password,
        )
        try:
            with self.session.begin_nested():
                self.session.add(model)
                self.session.flush()
        except IntegrityError as exc:
            constraint_name = exc.orig.diag.constraint_name

            if constraint_name == "uq_users_email":
                raise EmailAlreadyRegistered("Email already registered.") from None

            raise

        user.id = model.id
        return user

    def get_by_email(self, email: str) -> User | None:
        statement = select(UserModel).where(UserModel.email == email)
        result = self.session.execute(statement).scalars().first()
        if result is None:
            return None
        return self._to_domain(result)

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
        )
