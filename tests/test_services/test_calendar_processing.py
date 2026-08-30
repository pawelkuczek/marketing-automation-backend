from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.calendar_processing import CalendarProcessingService
from app.services.excel_processor import GenerationRequest


def create_service() -> tuple[CalendarProcessingService, AsyncMock]:
    """Create CalendarProcessingService with mocked dependencies."""

    excel_processor = MagicMock()
    prompt_repository = MagicMock()
    llm_service = MagicMock()
    llm_service.generate_text = AsyncMock()

    service = CalendarProcessingService(
        excel_processor=excel_processor,
        prompt_repository=prompt_repository,
        llm_service=llm_service,
    )

    return service, llm_service.generate_text


@pytest.mark.asyncio
async def test_generate_result_generates_content_and_hashtags() -> None:
    """Generate both content and hashtags when both are missing."""

    service, generate_text = create_service()

    generate_text.side_effect = [
        "Generated LinkedIn post.",
        "#marketing #automation",
    ]

    request = GenerationRequest(
        sheet_name="LinkedIn",
        row_idx=2,
        cycle="Employer branding",
        post_type="Carousel",
        topic="New office",
        generate_content=True,
        generate_hashtags=True,
    )

    result = await service._generate_result(
        request=request,
        system_prompt="You are a marketing expert.",
    )

    assert result.content == "Generated LinkedIn post."
    assert result.hashtags == "#marketing #automation"
    assert generate_text.await_count == 2


@pytest.mark.asyncio
async def test_generate_result_generates_only_content() -> None:
    """Generate content only when hashtags already exist."""

    service, generate_text = create_service()

    generate_text.return_value = "Generated LinkedIn post."

    request = GenerationRequest(
        sheet_name="LinkedIn",
        row_idx=2,
        cycle="Employer branding",
        post_type="Carousel",
        topic="New office",
        generate_content=True,
        generate_hashtags=False,
    )

    result = await service._generate_result(
        request=request,
        system_prompt="You are a marketing expert.",
    )

    assert result.content == "Generated LinkedIn post."
    assert result.hashtags is None
    generate_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_result_generates_only_hashtags() -> None:
    """Generate hashtags only when content already exists."""

    service, generate_text = create_service()

    generate_text.return_value = "#marketing #automation"

    request = GenerationRequest(
        sheet_name="LinkedIn",
        row_idx=2,
        cycle="Employer branding",
        post_type="Carousel",
        topic="New office",
        generate_content=False,
        generate_hashtags=True,
    )

    result = await service._generate_result(
        request=request,
        system_prompt="You are a marketing expert.",
    )

    assert result.content is None
    assert result.hashtags == "#marketing #automation"
    generate_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_calendar_file_runs_full_workflow() -> None:
    """Process a calendar using the active prompt and generated results."""

    excel_processor = MagicMock()
    prompt_repository = MagicMock()
    llm_service = MagicMock()

    prompt_repository.get_active = AsyncMock(
        return_value=MagicMock(content="System prompt")
    )

    workbook = MagicMock()

    request = GenerationRequest(
        sheet_name="LinkedIn",
        row_idx=2,
        cycle="Employer branding",
        post_type="Carousel",
        topic="New office",
        generate_content=True,
        generate_hashtags=False,
    )

    excel_processor.load_workbook = AsyncMock(return_value=workbook)
    excel_processor.collect_generation_requests = AsyncMock(return_value=[request])
    excel_processor.apply_generation_results = AsyncMock(return_value=workbook)
    excel_processor.save_workbook = AsyncMock(return_value=b"processed-file")

    llm_service.generate_text = AsyncMock(return_value="Generated post.")

    service = CalendarProcessingService(
        excel_processor=excel_processor,
        prompt_repository=prompt_repository,
        llm_service=llm_service,
    )

    result = await service.process_calendar_file(b"input-file")

    assert result == b"processed-file"

    prompt_repository.get_active.assert_awaited_once()
    excel_processor.load_workbook.assert_awaited_once_with(b"input-file")
    excel_processor.collect_generation_requests.assert_awaited_once_with(workbook)
    llm_service.generate_text.assert_awaited_once_with(
        system_prompt="System prompt",
        user_prompt=(
            "Cycle: Employer branding\nPost type: Carousel\nTopic: New office"
        ),
    )
    excel_processor.apply_generation_results.assert_awaited_once()
    excel_processor.save_workbook.assert_awaited_once_with(workbook)


@pytest.mark.asyncio
async def test_process_calendar_file_raises_error_without_active_prompt() -> None:
    """Raise ValueError when no active prompt is configured."""

    excel_processor = MagicMock()
    prompt_repository = MagicMock()
    llm_service = MagicMock()

    prompt_repository.get_active = AsyncMock(return_value=None)

    service = CalendarProcessingService(
        excel_processor=excel_processor,
        prompt_repository=prompt_repository,
        llm_service=llm_service,
    )

    with pytest.raises(
        ValueError,
        match="No active prompt configured.",
    ):
        await service.process_calendar_file(b"input-file")

    prompt_repository.get_active.assert_awaited_once()
