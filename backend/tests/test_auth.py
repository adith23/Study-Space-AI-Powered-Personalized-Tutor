"""
Authentication unit and integration tests.

Covers: AUTH-UNIT-001 through AUTH-UNIT-012
        AUTH-INT-001 through AUTH-INT-012

See qa_testing_plan.md Sections 6.1 and 7.1.
"""

from datetime import datetime, timedelta

import pytest
from jose import jwt

from app.core.security import (ALGORITHM, SECRET_KEY, create_access_token,
                               create_refresh_token, get_password_hash,
                               security, verify_password)
from app.models.user_model import User

# ==========================================================================
# UNIT TESTS — AUTH-UNIT
# ==========================================================================


class TestPasswordHashing:
    """AUTH-UNIT-001, 002, 003: Password hashing and verification."""

    def test_verify_password_correct(self):
        """AUTH-UNIT-001: verify_password returns True for the correct password."""
        password = "SuperSecretPassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """AUTH-UNIT-002: verify_password returns False for a wrong password."""
        hashed = get_password_hash("CorrectPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_password_hash_is_bcrypt(self):
        """AUTH-UNIT-003: get_password_hash produces a valid bcrypt hash."""
        hashed = get_password_hash("AnyPassword123")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) == 60  # bcrypt hashes are always 60 chars


class TestAccessToken:
    """AUTH-UNIT-004, 005: Access token creation and claims."""

    def test_access_token_has_correct_claims(self):
        """AUTH-UNIT-004: create_access_token includes sub, user_id, type, exp."""
        data = {"sub": "student@test.com", "user_id": "42"}
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "student@test.com"
        assert payload["user_id"] == "42"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_access_token_respects_custom_expiry(self):
        """AUTH-UNIT-005: create_access_token respects custom expires_delta."""
        data = {"sub": "student@test.com", "user_id": "1"}
        delta = timedelta(minutes=5)
        before = datetime.utcnow()

        token = create_access_token(data, expires_delta=delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_dt = datetime.utcfromtimestamp(payload["exp"])
        # The expiry should be ~5 minutes from now (with some tolerance)
        expected = before + delta
        assert abs((exp_dt - expected).total_seconds()) < 5


class TestRefreshToken:
    """AUTH-UNIT-006: Refresh token creation."""

    def test_refresh_token_has_type_refresh(self):
        """AUTH-UNIT-006: create_refresh_token sets type='refresh'."""
        data = {"sub": "student@test.com", "user_id": "1"}
        token = create_refresh_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "refresh"
        assert payload["sub"] == "student@test.com"


class TestTokenEmptySecret:
    """AUTH-UNIT-007: Token creation fails when SECRET_KEY is empty."""

    def test_access_token_raises_when_secret_empty(self, monkeypatch):
        """AUTH-UNIT-007: create_access_token raises ValueError when SECRET_KEY is empty."""
        monkeypatch.setattr("app.core.security.SECRET_KEY", "")
        with pytest.raises(ValueError, match="JWT_SECRET_KEY is not configured"):
            create_access_token(data={"sub": "x", "user_id": "1"})

    def test_refresh_token_raises_when_secret_empty(self, monkeypatch):
        """Supplementary: create_refresh_token also raises with empty key."""
        monkeypatch.setattr("app.core.security.SECRET_KEY", "")
        with pytest.raises(ValueError, match="JWT_SECRET_KEY is not configured"):
            create_refresh_token(data={"sub": "x", "user_id": "1"})


class TestVerifyToken:
    """AUTH-UNIT-008 through 012: Security.verify_token behaviour."""

    def test_verify_valid_access_token(self):
        """AUTH-UNIT-008: verify_token returns payload for a valid access token."""
        token = create_access_token({"sub": "a@b.com", "user_id": "1"})
        payload = security.verify_token(token, "access")
        assert payload is not None
        assert payload["sub"] == "a@b.com"
        assert payload["type"] == "access"

    def test_verify_expired_token_returns_none(self):
        """AUTH-UNIT-009: verify_token returns None for an expired token."""
        token = create_access_token(
            {"sub": "a@b.com", "user_id": "1"},
            expires_delta=timedelta(seconds=-10),  # already expired
        )
        result = security.verify_token(token, "access")
        assert result is None

    def test_verify_wrong_token_type_returns_none(self):
        """AUTH-UNIT-010: verify_token returns None when type doesn't match."""
        access_token = create_access_token({"sub": "a@b.com", "user_id": "1"})
        # Try to verify an access token as if it were a refresh token
        result = security.verify_token(access_token, "refresh")
        assert result is None

    def test_verify_tampered_token_returns_none(self):
        """AUTH-UNIT-011: verify_token returns None for a tampered token."""
        token = create_access_token({"sub": "a@b.com", "user_id": "1"})
        # Tamper with the token by modifying the last character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        result = security.verify_token(tampered, "access")
        assert result is None

    def test_verify_returns_none_when_secret_empty(self, monkeypatch):
        """AUTH-UNIT-012: verify_token returns None when SECRET_KEY is empty."""
        token = create_access_token({"sub": "a@b.com", "user_id": "1"})
        monkeypatch.setattr("app.core.security.SECRET_KEY", "")
        result = security.verify_token(token, "access")
        assert result is None

    def test_verify_invalid_string_returns_none(self):
        """Supplementary: verify_token returns None for garbage strings."""
        assert security.verify_token("not.a.jwt", "access") is None
        assert security.verify_token("", "access") is None


# ==========================================================================
# INTEGRATION TESTS — AUTH-INT
# ==========================================================================


class TestSignupEndpoint:
    """AUTH-INT-001, 002, 003: POST /api/v1/auth/signup"""

    def test_signup_creates_user_and_returns_jwt(self, client, db_session):
        """AUTH-INT-001: Successful signup creates user and returns JWT pair."""
        payload = {
            "username": "newstudent",
            "email": "newstudent@study-space.test",
            "password": "Password123!",
        }
        response = client.post("/api/v1/auth/signup", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify user is in the database
        user = db_session.query(User).filter(User.username == "newstudent").first()
        assert user is not None
        assert user.email == "newstudent@study-space.test"
        assert verify_password("Password123!", user.hashed_password)

    def test_signup_duplicate_email_returns_409(self, client, test_user):
        """AUTH-INT-002: Signup with existing email returns 409."""
        payload = {
            "username": "uniquename",
            "email": "student@study-space.test",  # same as test_user
            "password": "Password123!",
        }
        response = client.post("/api/v1/auth/signup", json=payload)
        assert response.status_code == 409
        assert "registered" in response.json()["detail"].lower()

    def test_signup_duplicate_username_returns_409(self, client, test_user):
        """AUTH-INT-003: Signup with existing username returns 409."""
        payload = {
            "username": "teststudent",  # same as test_user
            "email": "unique@study-space.test",
            "password": "Password123!",
        }
        response = client.post("/api/v1/auth/signup", json=payload)
        assert response.status_code == 409
        assert "registered" in response.json()["detail"].lower()


class TestLoginEndpoint:
    """AUTH-INT-004, 005, 006: POST /api/v1/auth/login"""

    def test_login_valid_credentials(self, client, test_user):
        """AUTH-INT-004: Login with valid credentials returns JWT pair."""
        payload = {"username": "teststudent", "password": "TestPassword123"}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client, test_user):
        """AUTH-INT-005: Login with wrong password returns 401."""
        payload = {"username": "teststudent", "password": "WrongPassword123"}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    def test_login_nonexistent_user_returns_401(self, client):
        """AUTH-INT-006: Login with non-existent user returns 401."""
        payload = {"username": "ghostuser", "password": "SomePassword123"}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401


class TestRefreshEndpoint:
    """AUTH-INT-007, 008, 009: POST /api/v1/auth/refresh"""

    def test_refresh_valid_token(self, client, test_user):
        """AUTH-INT-007: Refresh with a valid refresh token returns new pair."""
        refresh_token = create_refresh_token(
            data={"sub": test_user.email, "user_id": str(test_user.id)}
        )
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_expired_token_returns_401(self, client, test_user):
        """AUTH-INT-008: Refresh with an expired token returns 401."""
        expired_token = create_refresh_token(
            data={"sub": test_user.email, "user_id": str(test_user.id)},
            expires_delta=timedelta(seconds=-10),
        )
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token},
        )
        assert response.status_code == 401

    def test_refresh_with_access_token_returns_401(self, client, test_user):
        """AUTH-INT-009: Using an access token as refresh token returns 401."""
        access_token = create_access_token(
            data={"sub": test_user.email, "user_id": str(test_user.id)}
        )
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401

    def test_refresh_malformed_token_returns_401(self, client):
        """Supplementary: Malformed refresh token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.valid.jwt.token"},
        )
        assert response.status_code == 401


class TestProtectedEndpoints:
    """AUTH-INT-010, 011, 012: Auth enforcement on protected endpoints."""

    def test_protected_endpoint_no_auth_returns_401(self, client):
        """AUTH-INT-010: Protected endpoint without auth header returns 401."""
        response = client.get("/api/v1/materials/files")
        assert response.status_code == 401

    def test_protected_endpoint_with_header_auth(self, client, test_user, auth_headers):
        """AUTH-INT-012: Protected endpoint works with Authorization header."""
        response = client.get("/api/v1/materials/files", headers=auth_headers)
        # Should NOT be 401 — the exact status depends on the endpoint logic
        # but we're testing that auth passes, so anything other than 401 is good
        assert response.status_code != 401

    def test_protected_endpoint_with_cookie_auth(self, client, test_user):
        """AUTH-INT-011: Protected endpoint works with cookie-based auth."""
        token = create_access_token(
            data={"sub": test_user.email, "user_id": str(test_user.id)}
        )
        client.cookies.set("access_token", token)
        response = client.get("/api/v1/materials/files")
        assert response.status_code != 401
