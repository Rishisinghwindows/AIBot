"""
Integration tests for authentication endpoints.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
class TestGoogleAuthEndpoint:
    """Tests for Google authentication endpoint."""

    def test_google_auth_missing_token(self, client):
        """Test Google auth with missing token."""
        response = client.post("/auth/google", json={})
        assert response.status_code == 422  # Validation error

    def test_google_auth_invalid_token(self, client):
        """Test Google auth with invalid Firebase token."""
        with patch("app.auth.router.verify_firebase_token") as mock_verify:
            mock_verify.return_value = None

            response = client.post(
                "/auth/google",
                json={"firebase_id_token": "invalid-token"},
            )

            assert response.status_code == 401

    def test_google_auth_success(self, client, test_db, mock_firebase_admin):
        """Test successful Google authentication."""
        with patch("app.auth.router.verify_firebase_token") as mock_verify:
            mock_verify.return_value = {
                "uid": "new-firebase-uid",
                "email": "newuser@example.com",
                "name": "New User",
                "picture": "https://example.com/photo.jpg",
            }

            response = client.post(
                "/auth/google",
                json={
                    "firebase_id_token": "valid-firebase-token",
                    "device_info": "Test Device",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "expires_in" in data
            assert data["token_type"] == "bearer"


@pytest.mark.integration
class TestRefreshTokenEndpoint:
    """Tests for token refresh endpoint."""

    def test_refresh_missing_token(self, client):
        """Test refresh with missing token."""
        response = client.post("/auth/refresh", json={})
        assert response.status_code == 422

    def test_refresh_invalid_token(self, client, test_db):
        """Test refresh with invalid token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    def test_refresh_valid_token(self, client, test_db, test_user_with_refresh_token, test_settings):
        """Test successful token refresh."""
        user, refresh_token = test_user_with_refresh_token

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.integration
class TestMeEndpoint:
    """Tests for /auth/me endpoint."""

    def test_me_without_auth(self, client, security_headers):
        """Test /auth/me without authentication."""
        response = client.get("/auth/me", headers=security_headers)
        assert response.status_code == 401

    def test_me_with_auth(self, client, test_user, auth_headers):
        """Test /auth/me with valid authentication."""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["display_name"] == test_user.display_name

    def test_me_with_expired_token(self, client, test_user, test_settings, security_headers):
        """Test /auth/me with expired token."""
        from app.auth.jwt_handler import JWTHandler
        from app.config import Settings

        # Create expired token
        expired_settings = Settings(
            jwt_secret_key=test_settings.jwt_secret_key,
            jwt_access_token_expire_minutes=-1,
        )
        jwt_handler = JWTHandler(expired_settings)
        expired_token = jwt_handler.create_access_token(
            user_id=str(test_user.id),
            email=test_user.email,
        )

        headers = {**security_headers, "Authorization": f"Bearer {expired_token}"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == 401


@pytest.mark.integration
class TestLogoutEndpoint:
    """Tests for logout endpoint."""

    def test_logout_without_auth(self, client, security_headers):
        """Test logout without authentication."""
        response = client.post("/auth/logout", headers=security_headers)
        assert response.status_code == 401

    def test_logout_with_auth(self, client, test_user_with_refresh_token, test_settings, security_headers):
        """Test successful logout."""
        user, refresh_token = test_user_with_refresh_token

        from app.auth.jwt_handler import JWTHandler

        jwt_handler = JWTHandler(test_settings)
        access_token = jwt_handler.create_access_token(
            user_id=str(user.id),
            email=user.email,
        )

        headers = {**security_headers, "Authorization": f"Bearer {access_token}"}
        response = client.post("/auth/logout", headers=headers)

        assert response.status_code == 200


@pytest.mark.integration
class TestProvidersEndpoint:
    """Tests for providers endpoint."""

    def test_list_providers_without_auth(self, client, security_headers):
        """Test listing providers without authentication."""
        response = client.get("/auth/providers", headers=security_headers)
        assert response.status_code == 401

    def test_list_providers_with_auth(self, client, auth_headers):
        """Test listing providers with authentication."""
        response = client.get("/auth/providers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
