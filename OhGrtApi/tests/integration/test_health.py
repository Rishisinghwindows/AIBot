"""
Integration tests for health check endpoints.
"""

import pytest


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_basic_health_check(self, client):
        """Test basic health check returns healthy."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe."""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness_probe(self, client, test_db):
        """Test Kubernetes readiness probe."""
        response = client.get("/health/ready")

        # May return 200 or 503 depending on database connectivity
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "database" in data


@pytest.mark.integration
class TestOpenAPIEndpoints:
    """Tests for OpenAPI documentation endpoints."""

    def test_openapi_json(self, client):
        """Test OpenAPI JSON endpoint."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    def test_docs_endpoint(self, client):
        """Test Swagger UI endpoint."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "text/html" in response.headers.get("content-type", "")

    def test_redoc_endpoint(self, client):
        """Test ReDoc endpoint."""
        response = client.get("/redoc")

        assert response.status_code == 200
