import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import excel
from app.api.routers import prompt as prompt_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="AI Content Assistant API",
        description=(
            "Marketing automation service for processing social media calendar files."
        ),
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(excel.router)
    app.include_router(prompt_router.router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Return the application health status."""
        return {"status": "ok"}

    return app


app = create_app()
