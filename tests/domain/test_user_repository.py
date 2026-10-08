from app.domain.user_repository import InMemoryUserRepository, UserRepository
from tests.domain.utils import create_user


class TestUserRepository:
    def setup_method(self):
        self.user_repository = InMemoryUserRepository()
        self.user = create_user()

    def test_add_user(self):
        received_user = self.user_repository.add_user(self.user)
        another_user = create_user(email="another_email@example.com")
        received_another_user = self.user_repository.add_user(another_user)

        assert received_user.id == 1
        assert received_another_user.id == 2

    def test_get_user_by_email(self):
        self.user_repository.add_user(self.user)
        received_user = self.user_repository.get_by_email(self.user.email)

        assert received_user.id == self.user.id
        assert received_user.email == self.user.email
        assert received_user.hashed_password == self.user.hashed_password

    def test_get_user_by_email_return_none_for_unknown_email(self):
        received_user = self.user_repository.get_by_email(
            "non_existent_email@example.com"
        )

        assert received_user is None

    def test_in_memory_repository_satisfies_user_repository_protocol(self):
        assert isinstance(self.user_repository, UserRepository)
