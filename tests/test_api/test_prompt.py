from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.routers.prompt import get_prompt_service
from app.main import app
from app.models.prompt import Prompt

client = TestClient(app)


def _override_prompt_service(mock_service: AsyncMock) -> None:
    """Override PromptService dependency for endpoint tests."""

    app.dependency_overrides[get_prompt_service] = lambda: mock_service


def _clear_overrides() -> None:
    """Clear dependency overrides after each test."""

    app.dependency_overrides.clear()


def test_create_prompt_endpoint_success() -> None:
    """Create a prompt and return it through the HTTP API."""

    mock_service = AsyncMock()

    fake_prompt = Prompt(
        id=1,
        name="Test API Prompt",
        content="API Test Content",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_service.create_new_active_prompt.return_value = fake_prompt

    _override_prompt_service(mock_service)

    payload = {
        "name": "Test API Prompt",
        "content": "API Test Content",
    }

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["id"] == 1
        assert data["name"] == "Test API Prompt"
        assert data["content"] == "API Test Content"
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

        mock_service.create_new_active_prompt.assert_awaited_once()

        prompt_arg = mock_service.create_new_active_prompt.await_args.args[0]

        assert prompt_arg.name == "Test API Prompt"
        assert prompt_arg.content == "API Test Content"

    finally:
        _clear_overrides()


@pytest.mark.parametrize(
    ("payload", "expected_field"),
    [
        (
            {
                "name": "A",
                "content": "This content is long enough.",
            },
            "name",
        ),
        (
            {
                "name": "AB",
                "content": "This content is long enough.",
            },
            "name",
        ),
        (
            {
                "name": "Valid Prompt",
                "content": "short",
            },
            "content",
        ),
        (
            {
                "content": "This content is long enough.",
            },
            "name",
        ),
        (
            {
                "name": "Valid Prompt",
            },
            "content",
        ),
    ],
)
def test_create_prompt_endpoint_rejects_invalid_payload(
    payload: dict[str, str],
    expected_field: str,
) -> None:
    """Reject invalid prompt payloads before calling the service."""

    mock_service = AsyncMock()
    _override_prompt_service(mock_service)

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        data = response.json()

        assert "detail" in data
        assert any(expected_field in error["loc"] for error in data["detail"])

        mock_service.create_new_active_prompt.assert_not_awaited()

    finally:
        _clear_overrides()


def test_create_prompt_endpoint_rejects_name_over_max_length() -> None:
    """Reject prompt names longer than the configured maximum."""

    mock_service = AsyncMock()
    _override_prompt_service(mock_service)

    payload = {
        "name": "A" * 101,
        "content": "This content is long enough.",
    }

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        mock_service.create_new_active_prompt.assert_not_awaited()

    finally:
        _clear_overrides()


def test_create_prompt_endpoint_accepts_name_at_max_length() -> None:
    """Accept a prompt name exactly at the configured maximum length."""

    mock_service = AsyncMock()

    prompt_name = "A" * 100

    fake_prompt = Prompt(
        id=2,
        name=prompt_name,
        content="Valid prompt content.",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_service.create_new_active_prompt.return_value = fake_prompt

    _override_prompt_service(mock_service)

    payload = {
        "name": prompt_name,
        "content": "Valid prompt content.",
    }

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == prompt_name

        mock_service.create_new_active_prompt.assert_awaited_once()

    finally:
        _clear_overrides()


def test_create_prompt_endpoint_accepts_minimum_valid_lengths() -> None:
    """Accept values exactly at the configured minimum lengths."""

    mock_service = AsyncMock()

    fake_prompt = Prompt(
        id=3,
        name="ABC",
        content="1234567890",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_service.create_new_active_prompt.return_value = fake_prompt

    _override_prompt_service(mock_service)

    payload = {
        "name": "ABC",
        "content": "1234567890",
    }

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_201_CREATED

        mock_service.create_new_active_prompt.assert_awaited_once()

    finally:
        _clear_overrides()


def test_create_prompt_endpoint_rejects_null_name() -> None:
    """Reject a null prompt name."""

    mock_service = AsyncMock()
    _override_prompt_service(mock_service)

    payload = {
        "name": None,
        "content": "This content is long enough.",
    }

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        mock_service.create_new_active_prompt.assert_not_awaited()

    finally:
        _clear_overrides()


def test_create_prompt_endpoint_rejects_null_content() -> None:
    """Reject null prompt content."""

    mock_service = AsyncMock()
    _override_prompt_service(mock_service)

    payload = {
        "name": "Valid Prompt",
        "content": None,
    }

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        mock_service.create_new_active_prompt.assert_not_awaited()

    finally:
        _clear_overrides()


def test_create_prompt_endpoint_rejects_invalid_json_shape() -> None:
    """Reject non-object request payloads."""

    mock_service = AsyncMock()
    _override_prompt_service(mock_service)

    try:
        response = client.post(
            "/prompts",
            json=[
                {
                    "name": "Prompt",
                    "content": "Valid prompt content.",
                }
            ],
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        mock_service.create_new_active_prompt.assert_not_awaited()

    finally:
        _clear_overrides()


def test_create_prompt_endpoint_returns_service_http_exception() -> None:
    """Propagate HTTP errors raised by the service layer."""

    mock_service = AsyncMock()

    mock_service.create_new_active_prompt.side_effect = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Prompt name already exists.",
    )

    _override_prompt_service(mock_service)

    payload = {
        "name": "Existing Prompt",
        "content": "This content is long enough.",
    }

    try:
        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {"detail": "Prompt name already exists."}

        mock_service.create_new_active_prompt.assert_awaited_once()

    finally:
        _clear_overrides()


def test_get_prompts_endpoint_success() -> None:
    """Return all prompts through the HTTP API."""

    mock_service = AsyncMock()

    prompts = [
        Prompt(
            id=2,
            name="Newest Prompt",
            content="Newest prompt content.",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        Prompt(
            id=1,
            name="Older Prompt",
            content="Older prompt content.",
            is_active=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    ]

    mock_service.get_prompts.return_value = prompts

    _override_prompt_service(mock_service)

    try:
        response = client.get("/prompts")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert len(data) == 2
        assert data[0]["id"] == 2
        assert data[0]["name"] == "Newest Prompt"
        assert data[0]["is_active"] is True
        assert data[1]["id"] == 1
        assert data[1]["name"] == "Older Prompt"
        assert data[1]["is_active"] is False

        mock_service.get_prompts.assert_awaited_once_with()

    finally:
        _clear_overrides()


def test_get_prompt_endpoint_success() -> None:
    """Return a single prompt through the HTTP API."""

    mock_service = AsyncMock()

    prompt = Prompt(
        id=1,
        name="Existing Prompt",
        content="Existing prompt content.",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_service.get_prompt.return_value = prompt

    _override_prompt_service(mock_service)

    try:
        response = client.get("/prompts/1")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == 1
        assert data["name"] == "Existing Prompt"
        assert data["content"] == "Existing prompt content."
        assert data["is_active"] is True

        mock_service.get_prompt.assert_awaited_once_with(1)

    finally:
        _clear_overrides()


def test_get_prompt_endpoint_returns_404() -> None:
    """Return 404 when the requested prompt does not exist."""

    mock_service = AsyncMock()

    mock_service.get_prompt.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Prompt not found.",
    )

    _override_prompt_service(mock_service)

    try:
        response = client.get("/prompts/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Prompt not found."}

        mock_service.get_prompt.assert_awaited_once_with(999)

    finally:
        _clear_overrides()


def test_update_prompt_endpoint_success() -> None:
    """Update a prompt through the HTTP API."""

    mock_service = AsyncMock()

    updated_prompt = Prompt(
        id=1,
        name="Updated Prompt",
        content="Updated prompt content.",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_service.update_prompt.return_value = updated_prompt

    _override_prompt_service(mock_service)

    payload = {
        "name": "Updated Prompt",
        "content": "Updated prompt content.",
    }

    try:
        response = client.patch(
            "/prompts/1",
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == 1
        assert data["name"] == "Updated Prompt"
        assert data["content"] == "Updated prompt content."
        assert data["is_active"] is True

        mock_service.update_prompt.assert_awaited_once()

        call = mock_service.update_prompt.await_args

        assert call.kwargs["prompt_id"] == 1
        assert call.kwargs["prompt_data"].name == "Updated Prompt"
        assert call.kwargs["prompt_data"].content == "Updated prompt content."

    finally:
        _clear_overrides()


def test_update_prompt_endpoint_accepts_content_only() -> None:
    """Allow updating prompt content without changing its name."""

    mock_service = AsyncMock()

    updated_prompt = Prompt(
        id=1,
        name="Existing Prompt",
        content="Completely rewritten prompt content.",
        is_active=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_service.update_prompt.return_value = updated_prompt

    _override_prompt_service(mock_service)

    payload = {
        "content": "Completely rewritten prompt content.",
    }

    try:
        response = client.patch(
            "/prompts/1",
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["content"] == "Completely rewritten prompt content."

        call = mock_service.update_prompt.await_args

        assert call.kwargs["prompt_data"].name is None
        assert (
            call.kwargs["prompt_data"].content == "Completely rewritten prompt content."
        )

    finally:
        _clear_overrides()


def test_update_prompt_endpoint_returns_404() -> None:
    """Return 404 when updating a missing prompt."""

    mock_service = AsyncMock()

    mock_service.update_prompt.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Prompt not found.",
    )

    _override_prompt_service(mock_service)

    try:
        response = client.patch(
            "/prompts/999",
            json={
                "content": "Updated prompt content.",
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Prompt not found."}

    finally:
        _clear_overrides()


def test_activate_prompt_endpoint_success() -> None:
    """Activate a prompt through the HTTP API."""

    mock_service = AsyncMock()

    activated_prompt = Prompt(
        id=2,
        name="Activated Prompt",
        content="Activated prompt content.",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_service.activate_prompt.return_value = activated_prompt

    _override_prompt_service(mock_service)

    try:
        response = client.patch("/prompts/2/activate")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == 2
        assert data["name"] == "Activated Prompt"
        assert data["is_active"] is True

        mock_service.activate_prompt.assert_awaited_once_with(2)

    finally:
        _clear_overrides()


def test_activate_prompt_endpoint_returns_404() -> None:
    """Return 404 when activating a missing prompt."""

    mock_service = AsyncMock()

    mock_service.activate_prompt.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Prompt not found.",
    )

    _override_prompt_service(mock_service)

    try:
        response = client.patch("/prompts/999/activate")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Prompt not found."}

        mock_service.activate_prompt.assert_awaited_once_with(999)

    finally:
        _clear_overrides()


def test_activate_prompt_endpoint_rejects_invalid_id() -> None:
    """Return validation error when prompt ID is not an integer."""

    mock_service = AsyncMock()

    _override_prompt_service(mock_service)

    try:
        response = client.patch("/prompts/not-an-integer/activate")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        mock_service.activate_prompt.assert_not_awaited()

    finally:
        _clear_overrides()


def test_delete_prompt_endpoint_success() -> None:
    """Delete an inactive prompt through the HTTP API."""

    mock_service = AsyncMock()
    mock_service.delete_prompt.return_value = None

    _override_prompt_service(mock_service)

    try:
        response = client.delete("/prompts/2")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

        mock_service.delete_prompt.assert_awaited_once_with(2)

    finally:
        _clear_overrides()


def test_delete_prompt_endpoint_returns_409_for_active_prompt() -> None:
    """Return 409 when attempting to delete the active prompt."""

    mock_service = AsyncMock()

    mock_service.delete_prompt.side_effect = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Active prompt cannot be deleted.",
    )

    _override_prompt_service(mock_service)

    try:
        response = client.delete("/prompts/1")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            "detail": "Active prompt cannot be deleted.",
        }

        mock_service.delete_prompt.assert_awaited_once_with(1)

    finally:
        _clear_overrides()


def test_delete_prompt_endpoint_returns_404() -> None:
    """Return 404 when deleting a missing prompt."""

    mock_service = AsyncMock()

    mock_service.delete_prompt.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Prompt not found.",
    )

    _override_prompt_service(mock_service)

    try:
        response = client.delete("/prompts/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Prompt not found."}

        mock_service.delete_prompt.assert_awaited_once_with(999)

    finally:
        _clear_overrides()
