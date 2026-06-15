"""
Materials API integration tests.

Covers: MAT-INT-001 through MAT-INT-006

See qa_testing_plan.md Section 7.2.
"""

import pytest
from unittest.mock import patch

from app.models.material_model import ProcessingStatus, UploadedFile, FileType


# ==========================================================================
# MAT-INT-001 through 006: Materials API
# ==========================================================================


class TestMaterialUpload:
    """MAT-INT-001, 003, 005: POST /api/v1/materials/file (multipart form)."""

    @patch("app.services.material_service.process_document_task")
    def test_upload_valid_pdf_creates_file_record(
        self, mock_task, client, db_session, test_user, auth_headers, sample_pdf
    ):
        """MAT-INT-001: Upload a valid PDF via multipart form creates a file record with PENDING status."""
        file_path, pdf_bytes = sample_pdf

        response = client.post(
            "/api/v1/materials/file",
            headers=auth_headers,
            files={"file": ("test_document.pdf", pdf_bytes, "application/pdf")},
            data={"file_type": "pdf"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "pdf"
        assert data["status"] == "pending"
        assert data["name"] == "test_document.pdf"

    @patch("app.services.material_service.process_document_task")
    def test_upload_triggers_celery_task(
        self, mock_task, client, db_session, test_user, auth_headers, sample_pdf
    ):
        """MAT-INT-003: Upload calls process_document_task.delay(file_id)."""
        _, pdf_bytes = sample_pdf

        response = client.post(
            "/api/v1/materials/file",
            headers=auth_headers,
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
            data={"file_type": "pdf"},
        )
        assert response.status_code == 200
        file_id = response.json()["id"]

        # Verify Celery .delay() was called with the correct file_id
        mock_task.delay.assert_called_once_with(file_id)

    @patch("app.services.material_service.process_document_task")
    def test_upload_without_file_or_url_returns_400(
        self, mock_task, client, auth_headers
    ):
        """MAT-INT-005: Upload without file or URL returns 400."""
        response = client.post(
            "/api/v1/materials/file",
            headers=auth_headers,
            data={"file_type": "pdf"},
        )
        assert response.status_code == 400
        assert "file or a URL" in response.json()["detail"]


class TestMaterialList:
    """MAT-INT-002: GET /api/v1/materials/files."""

    @patch("app.services.material_service.process_document_task")
    def test_returns_only_current_user_materials(
        self, mock_task, client, db_session, test_user, second_user,
        auth_headers, second_user_headers, sample_pdf
    ):
        """MAT-INT-002: GET /files returns only the current user's materials."""
        _, pdf_bytes = sample_pdf

        # Upload as test_user
        client.post(
            "/api/v1/materials/file",
            headers=auth_headers,
            files={"file": ("user_a.pdf", pdf_bytes, "application/pdf")},
            data={"file_type": "pdf"},
        )

        # Upload as second_user
        client.post(
            "/api/v1/materials/file",
            headers=second_user_headers,
            files={"file": ("user_b.pdf", pdf_bytes, "application/pdf")},
            data={"file_type": "pdf"},
        )

        # List as test_user — should only see 1
        response = client.get("/api/v1/materials/files", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "user_a.pdf"


class TestMaterialAccessControl:
    """MAT-INT-004, 006: Cross-user access and file content."""

    def test_user_b_cannot_see_user_a_file_status(
        self, client, db_session, test_user, second_user, second_user_headers
    ):
        """MAT-INT-004: User A's file returns 404 for User B."""
        file_record = UploadedFile(
            name="secret.pdf",
            stored_path="/fake/path.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.SUCCESS,
            user_id=test_user.id,
        )
        db_session.add(file_record)
        db_session.commit()
        db_session.refresh(file_record)

        response = client.get(
            f"/api/v1/materials/{file_record.id}/status",
            headers=second_user_headers,
        )
        assert response.status_code == 404

    def test_file_content_returns_404_when_file_missing(
        self, client, db_session, test_user, auth_headers
    ):
        """MAT-INT-006: GET /files/{id}/content returns 404 when stored file is missing."""
        file_record = UploadedFile(
            name="gone.pdf",
            stored_path="/nonexistent/path/gone.pdf",
            file_type=FileType.pdf,
            status=ProcessingStatus.SUCCESS,
            user_id=test_user.id,
        )
        db_session.add(file_record)
        db_session.commit()
        db_session.refresh(file_record)

        response = client.get(
            f"/api/v1/materials/files/{file_record.id}/content",
            headers=auth_headers,
        )
        assert response.status_code == 404
