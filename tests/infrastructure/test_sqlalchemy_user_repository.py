import re

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.exceptions import EmailAlreadyRegistered, UserNotFound
from app.domain.user_repository import UserRepository
from app.infrastructure.user_repository import SQLAlchemyUserRepository
from tests.domain.utils import create_user


class TestSQLAlchemyUserRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db_session = db_session
        self.repository = SQLAlchemyUserRepository(db_session)
        self.user = create_user()

    def test_add_user(self):
        added_user = self.repository.add_user(self.user)
        self.db_session.expire_all()
        received = self.repository.get_by_email(self.user.email)

        assert received is not None
        assert received.id == added_user.id
        assert received.email == added_user.email
        assert received.hashed_password == added_user.hashed_password

    def test_add_user_with_existing_email_raises(self):
        self.repository.add_user(self.user)
        other_user = create_user()
        with pytest.raises(
            EmailAlreadyRegistered,
            match=rf"Email {re.escape(other_user.email)} already registered",
        ):
            self.repository.add_user(other_user)

        received = self.repository.get_by_email(self.user.email)
        assert received is not None
        assert received.id == self.user.id

    def test_add_user_without_password_raises(self):
        without_password = create_user(hashed_password=None)
        with pytest.raises(IntegrityError):
            self.repository.add_user(without_password)

    def test_get_by_email(self):
        added_user = self.repository.add_user(self.user)
        self.db_session.expire_all()
        received = self.repository.get_by_email(self.user.email)

        assert added_user.id == received.id
        assert added_user.email == received.email
        assert added_user.hashed_password == received.hashed_password

    def test_get_by_email_returns_none_for_unknown_email(self):
        received_user = self.repository.get_by_email("non_existent_email@example.com")

        assert received_user is None

    def test_get_by_id(self):
        added_user = self.repository.add_user(self.user)
        self.db_session.expire_all()
        received_user = self.repository.get_by_id(added_user.id)

        assert added_user.id == received_user.id
        assert added_user.email == received_user.email
        assert added_user.hashed_password == received_user.hashed_password

    def test_get_by_id_raises_for_unknown_id(self):
        with pytest.raises(UserNotFound):
            self.repository.get_by_id(99)

    def test_sqlalchemy_repository_satisfies_user_repository_protocol(self):
        assert isinstance(self.repository, UserRepository)
