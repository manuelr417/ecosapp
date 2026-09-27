class TestHealth:
    def test_health_ok(self, demo_client):
        response = demo_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestClientBundle:
    def test_index_serves_built_client(self, demo_client):
        response = demo_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert 'id="root"' in response.text
