class FakePasswordHasher:
    def __init__(self) -> None:
        self.verify_calls: list[tuple[str, str]] = []

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        self.verify_calls.append((password, hashed_password))
        return hashed_password == f"hashed:{password}"
