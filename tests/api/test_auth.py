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

    def test_login_returns_access_token_for_valid_credentials(
        self, registered_user, token_service, client, now
    ):
        payload = {
            "username": registered_user["email"],
            "password": registered_user["password"],
        }
        response = client.post("/auth/login", data=payload)
        data = response.json()
        assert response.status_code == 200
        assert set(data.keys()) == {"access_token", "token_type"}
        assert data["token_type"] == "bearer"

        decoded_user_id = token_service.decode_access_token(
            data["access_token"],
            now=now,
        )

        assert decoded_user_id == registered_user["id"]

    def test_login_with_wrong_password_returns_401(self, client, registered_user):
        payload = {"username": registered_user["email"], "password": "wrong_password"}
        response = client.post("/auth/login", data=payload)

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid credentials"}
        assert response.headers["www-authenticate"] == "Bearer"

    def test_login_with_unknown_email_returns_401(self, client, registered_user):
        payload = {
            "username": "another@example.com",
            "password": registered_user["password"],
        }
        response = client.post("/auth/login", data=payload)

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid credentials"}
        assert response.headers["www-authenticate"] == "Bearer"

    def test_login_normalized_email_success(self, client, registered_user):
        payload = {
            "username": f" {registered_user['email'].upper()} ",
            "password": registered_user["password"],
        }
        response = client.post("/auth/login", data=payload)

        assert response.status_code == 200
