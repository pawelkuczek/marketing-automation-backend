import asyncio

from app.repositories.prompt import PromptRepository
from app.services.excel_processor import (
    ExcelProcessorService,
    GenerationRequest,
    GenerationResult,
)
from app.services.llm import LLMService


class CalendarProcessingService:
    """Coordinate Excel processing, prompts, and AI generation."""

    def __init__(
        self,
        excel_processor: ExcelProcessorService,
        prompt_repository: PromptRepository,
        llm_service: LLMService,
    ) -> None:
        self.excel_processor = excel_processor
        self.prompt_repository = prompt_repository
        self.llm_service = llm_service

    @staticmethod
    def _build_user_prompt(request: GenerationRequest) -> str:
        """Build an AI input prompt from an Excel row."""

        return (
            f"Cycle: {request.cycle}\n"
            f"Post type: {request.post_type}\n"
            f"Topic: {request.topic}"
        )

    async def _generate_result(
        self,
        request: GenerationRequest,
        system_prompt: str,
    ) -> GenerationResult:
        """Generate missing content for a single Excel row."""

        user_prompt = self._build_user_prompt(request)

        content = None
        hashtags = None

        if request.generate_content:
            content = await self.llm_service.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

        if request.generate_hashtags:
            hashtag_prompt = f"{user_prompt}\nGenerate relevant hashtags for this post."

            hashtags = await self.llm_service.generate_text(
                system_prompt=system_prompt,
                user_prompt=hashtag_prompt,
            )

        return GenerationResult(
            sheet_name=request.sheet_name,
            row_idx=request.row_idx,
            content=content,
            hashtags=hashtags,
        )

    async def process_calendar_file(
        self,
        file_bytes: bytes,
    ) -> bytes:
        """Process an Excel calendar using the active AI prompt."""

        active_prompt = await self.prompt_repository.get_active()

        if active_prompt is None:
            raise ValueError("No active prompt configured.")

        workbook = await self.excel_processor.load_workbook(file_bytes)

        requests = await self.excel_processor.collect_generation_requests(workbook)

        results = await asyncio.gather(
            *[
                self._generate_result(
                    request=request,
                    system_prompt=active_prompt.content,
                )
                for request in requests
            ]
        )

        processed_workbook = await self.excel_processor.apply_generation_results(
            workbook,
            list(results),
        )

        return await self.excel_processor.save_workbook(processed_workbook)
