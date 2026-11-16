class TestFrontend:
    def test_root_serves_index_html(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "<title>PulseCheck</title>" in response.text

    def test_static_files_are_served(self, client):
        response = client.get("/static/index.html")

        assert response.status_code == 200
        assert "<title>PulseCheck</title>" in response.text

    def test_root_is_not_in_api_schema(self, client):
        response = client.get("/openapi.json")

        assert "/" not in response.json()["paths"]

    def test_api_routes_still_work(self, client):
        response = client.get("/monitors")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}
