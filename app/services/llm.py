import asyncio

from openai import (
    APIConnectionError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings


class LLMService:
    """
    Service for interacting with the OpenAI API.

    Handles concurrency limits and retries for transient API failures.
    """

    def __init__(self, max_concurrent_requests: int = 5) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (
                RateLimitError,
                APIConnectionError,
                InternalServerError,
            )
        ),
        reraise=True,
    )
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate text from system instructions and post-specific input."""

        async with self.semaphore:
            response = await self.client.responses.create(
                model=settings.OPENAI_MODEL,
                instructions=system_prompt,
                input=user_prompt,
                max_output_tokens=500,
            )

        if not response.output_text:
            raise ValueError("OpenAI returned an empty response.")

        return response.output_text


def get_llm_service() -> LLMService:
    """Provide an LLMService instance."""

    return LLMService()
