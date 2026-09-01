import io
from unittest.mock import AsyncMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.api.routers.excel import get_calendar_processing_service
from app.main import app

client = TestClient(app)


def create_valid_excel_bytes() -> bytes:
    """Create a minimal valid Excel workbook in memory."""

    workbook = Workbook()
    worksheet = workbook.active

    assert worksheet is not None

    worksheet.title = "Test_Sheet"
    worksheet.append(
        [
            "Cykl",
            "Typ posta",
            "Temat",
            "Treść posta",
            "Hasła",
        ]
    )
    worksheet.append(
        [
            "Q1",
            "Carousel",
            "Product campaign",
            None,
            None,
        ]
    )

    output = io.BytesIO()
    workbook.save(output)

    return output.getvalue()


def override_excel_service(mock_service: AsyncMock) -> None:
    """Override the ExcelProcessorService dependency."""

    app.dependency_overrides[get_calendar_processing_service] = lambda: mock_service


def clear_dependency_overrides() -> None:
    """Clear FastAPI dependency overrides."""

    app.dependency_overrides.clear()


def test_process_calendar_success() -> None:
    """Process a valid Excel file and return it as a download."""

    mock_service = AsyncMock()

    input_bytes = create_valid_excel_bytes()
    processed_bytes = b"processed-excel-bytes"

    mock_service.process_calendar_file.return_value = processed_bytes

    override_excel_service(mock_service)

    try:
        response = client.post(
            "/excel/process-calendar",
            files={
                "file": (
                    "calendar.xlsx",
                    input_bytes,
                    (
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.content == processed_bytes

        assert response.headers["content-type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        content_disposition = response.headers["content-disposition"]

        assert "attachment" in content_disposition
        assert "ai_processed_calendar.xlsx" in content_disposition

        mock_service.process_calendar_file.assert_awaited_once()

        file_bytes = mock_service.process_calendar_file.await_args.args[0]

        assert file_bytes == input_bytes

    finally:
        clear_dependency_overrides()


@pytest.mark.parametrize(
    "filename",
    [
        "calendar.csv",
        "calendar.xls",
        "calendar.txt",
        "calendar.pdf",
        "calendar",
    ],
)
def test_process_calendar_rejects_invalid_file_extension(
    filename: str,
) -> None:
    """Reject files that do not use the .xlsx extension."""

    mock_service = AsyncMock()
    override_excel_service(mock_service)

    try:
        response = client.post(
            "/excel/process-calendar",
            files={
                "file": (
                    filename,
                    b"invalid-file",
                    "application/octet-stream",
                )
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "Invalid file type. Only .xlsx files are supported."
        }

        mock_service.process_calendar_file.assert_not_awaited()

    finally:
        clear_dependency_overrides()


def test_process_calendar_accepts_uppercase_xlsx_extension() -> None:
    """Accept .xlsx extensions regardless of letter casing."""

    mock_service = AsyncMock()

    input_bytes = create_valid_excel_bytes()
    mock_service.process_calendar_file.return_value = b"processed"

    override_excel_service(mock_service)

    try:
        response = client.post(
            "/excel/process-calendar",
            files={
                "file": (
                    "CALENDAR.XLSX",
                    input_bytes,
                    "application/octet-stream",
                )
            },
        )

        assert response.status_code == status.HTTP_200_OK
        mock_service.process_calendar_file.assert_awaited_once()

    finally:
        clear_dependency_overrides()


def test_process_calendar_returns_500_when_processor_fails() -> None:
    """Return 500 when the Excel processor raises an unexpected error."""

    mock_service = AsyncMock()

    mock_service.process_calendar_file.side_effect = RuntimeError("Processing failed")

    override_excel_service(mock_service)

    try:
        response = client.post(
            "/excel/process-calendar",
            files={
                "file": (
                    "calendar.xlsx",
                    create_valid_excel_bytes(),
                    "application/octet-stream",
                )
            },
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        assert response.json() == {
            "detail": ("Internal server error during file processing.")
        }

        mock_service.process_calendar_file.assert_awaited_once()

    finally:
        clear_dependency_overrides()


def test_process_calendar_encodes_non_ascii_filename() -> None:
    """Encode non-ASCII download filenames in Content-Disposition."""

    mock_service = AsyncMock()

    mock_service.process_calendar_file.return_value = b"processed"

    override_excel_service(mock_service)

    try:
        response = client.post(
            "/excel/process-calendar",
            files={
                "file": (
                    "sierpień 2026.xlsx",
                    create_valid_excel_bytes(),
                    "application/octet-stream",
                )
            },
        )

        assert response.status_code == status.HTTP_200_OK

        content_disposition = response.headers["content-disposition"]

        assert "filename*=utf-8''" in content_disposition
        assert "ai_processed_" in content_disposition
        assert "%C5%84" in content_disposition
        assert "%20" in content_disposition

    finally:
        clear_dependency_overrides()


def test_process_calendar_preserves_special_filename_characters_safely() -> None:
    """Safely encode spaces and special characters in download filenames."""

    mock_service = AsyncMock()

    mock_service.process_calendar_file.return_value = b"processed"

    override_excel_service(mock_service)

    try:
        response = client.post(
            "/excel/process-calendar",
            files={
                "file": (
                    "campaign & launch 2026.xlsx",
                    create_valid_excel_bytes(),
                    "application/octet-stream",
                )
            },
        )

        assert response.status_code == status.HTTP_200_OK

        content_disposition = response.headers["content-disposition"]

        assert "%20" in content_disposition
        assert "%26" in content_disposition

    finally:
        clear_dependency_overrides()


def test_process_calendar_rejects_missing_file() -> None:
    """Reject requests that do not contain an uploaded file."""

    mock_service = AsyncMock()
    override_excel_service(mock_service)

    try:
        response = client.post("/excel/process-calendar")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        mock_service.process_calendar_file.assert_not_awaited()

    finally:
        clear_dependency_overrides()


def test_process_calendar_rejects_empty_filename() -> None:
    """Reject uploaded files with an empty filename."""

    mock_service = AsyncMock()
    override_excel_service(mock_service)

    try:
        response = client.post(
            "/excel/process-calendar",
            files={
                "file": (
                    "",
                    b"content",
                    "application/octet-stream",
                )
            },
        )

        assert response.status_code in {
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        }

        mock_service.process_calendar_file.assert_not_awaited()

    finally:
        clear_dependency_overrides()
