class TestAuth:

    def test_register_returns_created_user(self, client):
        response = client.post(
            "/auth/register",
            json={
                "email": "User@eXample.com ",
                "password": "test_password",
            },
        )
        data = response.json()

        assert response.status_code == 201
        assert data["email"] == "user@example.com"
        assert set(response.json().keys()) == {"id", "email"}
        assert isinstance(data["id"], int)

    def test_register_existing_email_returns_409(self, client):
        payload = {"email": "existing@example.com", "password": "testpass"}
        response = client.post("/auth/register", json=payload)
        bad_response = client.post("/auth/register", json=payload)

        assert response.status_code == 201
        assert bad_response.status_code == 409
        assert bad_response.json() == {
            "detail": "Email existing@example.com already registered"
        }

    def test_register_with_7_character_password_returns_422(self, client):
        payload = {"email": "user@example.com", "password": "badpass"}
        response = client.post("/auth/register", json=payload)

        assert response.status_code == 422

    def test_register_with_8_character_password_returns_201(self, client):
        payload = {"email": "user@example.com", "password": "password"}
        response = client.post("/auth/register", json=payload)

        assert response.status_code == 201

    def test_register_with_password_over_72_bytes_returns_422(self, client):
        payload = {"email": "user@example.com", "password": "a" * 73}
        response = client.post("/auth/register", json=payload)

        assert response.status_code == 422
