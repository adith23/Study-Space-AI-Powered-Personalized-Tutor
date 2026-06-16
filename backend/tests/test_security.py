"""
Security-focused tests.

Covers: SEC-001 through SEC-007

See qa_testing_plan.md Section 10.1.
"""

from datetime import timedelta

import pytest
from jose import jwt

from app.core.security import (ALGORITHM, SECRET_KEY, create_access_token,
                               create_refresh_token, get_password_hash,
                               security, verify_password)
from app.models.user_model import User

# ==========================================================================
# SEC-001 through SEC-007: Authentication & Authorization Security
# ==========================================================================


class TestTokenForgery:
    """SEC-001: JWT tokens cannot be forged with a different secret."""

    def test_token_forged_with_wrong_secret_is_rejected(self):
        """SEC-001: A token signed with a different key is rejected."""
        forged_payload = {
            "sub": "attacker@evil.com",
            "user_id": "1",
            "type": "access",
        }
        forged_token = jwt.encode(
            forged_payload, "wrong-secret-key-12345", algorithm=ALGORITHM
        )
        result = security.verify_token(forged_token, "access")
        assert result is None


class TestTokenExpiry:
    """SEC-002: Expired access tokens are rejected."""

    def test_expired_access_token_rejected(self):
        """SEC-002: An expired access token is not accepted."""
        token = create_access_token(
            data={"sub": "user@test.com", "user_id": "1"},
            expires_delta=timedelta(seconds=-60),  # expired 1 min ago
        )
        result = security.verify_token(token, "access")
        assert result is None


class TestTokenTypeMismatch:
    """SEC-003: Refresh token cannot be used as access token."""

    def test_refresh_token_rejected_as_access(self, client, test_user):
        """SEC-003: Using a refresh token in the Authorization header is rejected."""
        refresh_token = create_refresh_token(
            data={"sub": test_user.email, "user_id": str(test_user.id)}
        )
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = client.get("/api/v1/materials/files", headers=headers)
        assert response.status_code == 401


class TestDeletedUserToken:
    """SEC-004: Deleted user's tokens are invalidated."""

    def test_deleted_user_token_rejected(self, client, db_session):
        """SEC-004: Token for a deleted user no longer grants access."""
        # Create a temporary user
        user = User(
            username="temporary_user",
            email="temp@study-space.test",
            hashed_password=get_password_hash("TempPass123!"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create a valid token for this user
        token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})

        # Delete the user
        db_session.delete(user)
        db_session.commit()

        # Try to use the old token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/materials/files", headers=headers)
        assert response.status_code == 401


class TestIDEnumeration:
    """SEC-005: User A cannot access User B's resources."""

    def test_user_b_cannot_access_user_a_file_status(
        self, client, db_session, test_user, second_user, second_user_headers
    ):
        """SEC-005: User B cannot view User A's file status by guessing the ID."""
        from app.models.material_model import (FileType, ProcessingStatus,
                                               UploadedFile)

        # Create a file belonging to test_user (User A)
        file_record = UploadedFile(
            name="secret_notes.pdf",
            stored_path="/fake/path.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.SUCCESS,
            user_id=test_user.id,
        )
        db_session.add(file_record)
        db_session.commit()
        db_session.refresh(file_record)

        # User B tries to access it
        response = client.get(
            f"/api/v1/materials/{file_record.id}/status",
            headers=second_user_headers,
        )
        assert response.status_code == 404


class TestPasswordNeverReturned:
    """SEC-006: Password / hash is never returned in API responses."""

    def test_signup_response_has_no_password(self, client):
        """SEC-006: Signup response contains only tokens, not passwords."""
        payload = {
            "username": "checkuser",
            "email": "check@study-space.test",
            "password": "SecurePass123!",
        }
        response = client.post("/api/v1/auth/signup", json=payload)
        data = response.json()

        # Must not contain password or hashed_password anywhere
        response_text = str(data).lower()
        assert "securepass" not in response_text
        assert "hashed_password" not in response_text

    def test_login_response_has_no_password(self, client, test_user):
        """SEC-006: Login response contains only tokens, not passwords."""
        payload = {"username": "teststudent", "password": "TestPassword123"}
        response = client.post("/api/v1/auth/login", json=payload)
        data = response.json()

        response_text = str(data).lower()
        assert "testpassword" not in response_text
        assert "hashed_password" not in response_text


class TestPasswordStorageSecurity:
    """SEC-007: Passwords are stored as bcrypt hashes, never as plaintext."""

    def test_password_stored_as_bcrypt(self, db_session, test_user):
        """SEC-007: The hashed_password field in the DB uses bcrypt."""
        user = db_session.query(User).filter(User.id == test_user.id).first()
        assert user.hashed_password.startswith(
            "$2b$"
        ) or user.hashed_password.startswith("$2a$")
        # It should NOT be the plaintext password
        assert user.hashed_password != "TestPassword123"
