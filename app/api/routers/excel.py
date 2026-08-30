import io
import logging
import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.prompt import PromptRepository
from app.services.calendar_processing import CalendarProcessingService
from app.services.excel_processor import ExcelProcessorService
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/excel",
    tags=["Excel Processing"],
)


def get_calendar_processing_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CalendarProcessingService:
    """Provide a configured CalendarProcessingService instance."""

    return CalendarProcessingService(
        excel_processor=ExcelProcessorService(),
        prompt_repository=PromptRepository(session=session),
        llm_service=get_llm_service(),
    )


@router.post("/process-calendar")
async def process_calendar(
    file: Annotated[UploadFile, File()],
    service: Annotated[
        CalendarProcessingService,
        Depends(get_calendar_processing_service),
    ],
) -> StreamingResponse:
    """
    Process an uploaded marketing calendar.

    Returns the processed workbook as an Excel file.
    """

    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .xlsx files are supported.",
        )

    try:
        file_bytes = await file.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded file.")
        raise HTTPException(
            status_code=400,
            detail="Error reading the file.",
        ) from exc

    try:
        processed_bytes = await service.process_calendar_file(file_bytes)
    except ValueError as exc:
        logger.warning(
            "Calendar processing failed: %s",
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to process Excel file.")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during file processing.",
        ) from exc

    safe_filename = urllib.parse.quote(f"ai_processed_{file.filename}")

    return StreamingResponse(
        io.BytesIO(processed_bytes),
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (f"attachment; filename*=utf-8''{safe_filename}")
        },
    )
