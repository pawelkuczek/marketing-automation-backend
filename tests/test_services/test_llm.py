from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.services.llm import LLMService


@pytest.mark.asyncio
async def test_generate_text_success() -> None:
    """Return generated text from a successful OpenAI response."""

    mock_response = SimpleNamespace(
        output_text="Wygenerowany post na platformę LinkedIn"
    )

    with patch("app.services.llm.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        service = LLMService(max_concurrent_requests=1)

        result = await service.generate_text(
            system_prompt="Jesteś ekspertem od contentu.",
            user_prompt="Temat: Nowości w firmie",
        )

        assert result == "Wygenerowany post na platformę LinkedIn"

        mock_client.responses.create.assert_awaited_once_with(
            model=settings.OPENAI_MODEL,
            instructions="Jesteś ekspertem od contentu.",
            input="Temat: Nowości w firmie",
            max_output_tokens=500,
        )


@pytest.mark.asyncio
async def test_generate_text_raises_error_for_empty_response() -> None:
    """Raise ValueError when OpenAI returns no generated text."""

    mock_response = SimpleNamespace(output_text="")

    with patch("app.services.llm.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        service = LLMService(max_concurrent_requests=1)

        with pytest.raises(
            ValueError,
            match="OpenAI returned an empty response.",
        ):
            await service.generate_text(
                system_prompt="System prompt",
                user_prompt="User prompt",
            )

        mock_client.responses.create.assert_awaited_once()
