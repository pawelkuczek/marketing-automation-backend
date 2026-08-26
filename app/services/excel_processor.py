import asyncio
import io
import logging

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.workbook import Workbook

logger = logging.getLogger(__name__)


class ExcelProcessorService:
    """
    Parse, process, and generate Excel files.

    File operations are performed in memory to keep the service stateless.
    """

    @staticmethod
    def _load_workbook_sync(file_bytes: bytes) -> Workbook:
        """
        Load an Excel workbook synchronously from in-memory bytes.

        This blocking operation is intended to run in a separate thread.
        """

        return load_workbook(filename=io.BytesIO(file_bytes))

    @staticmethod
    def _save_workbook_sync(workbook: Workbook) -> bytes:
        """Save an Excel workbook synchronously to in-memory bytes."""

        output = io.BytesIO()
        workbook.save(output)
        return output.getvalue()

    @staticmethod
    def _process_workbook_sync(workbook: Workbook) -> Workbook:
        """Populate missing marketing content in eligible post rows."""

        required_columns = {
            "Cykl",
            "Typ posta",
            "Temat",
            "Treść posta",
        }

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]

            logger.info("Inspecting sheet: %s", sheet_name)

            headers = {}

            for cell in sheet[1]:
                if isinstance(cell.value, str) and cell.value.strip():
                    headers[cell.value.strip()] = cell.column

            if not required_columns.issubset(headers):
                missing_columns = required_columns - headers.keys()

                logger.info(
                    "Skipping sheet %s: missing required columns: %s",
                    sheet_name,
                    sorted(missing_columns),
                )
                continue

            logger.info("Processing sheet: %s", sheet_name)

            for row_idx in range(2, sheet.max_row + 1):
                row_values = [cell.value for cell in sheet[row_idx]]

                if any(
                    isinstance(value, str) and value.strip().casefold() == "stories"
                    for value in row_values
                ):
                    logger.info(
                        "Stopping sheet %s at Stories section (row %s).",
                        sheet_name,
                        row_idx,
                    )
                    break

                cycle = sheet.cell(
                    row=row_idx,
                    column=headers["Cykl"],
                ).value

                post_type = sheet.cell(
                    row=row_idx,
                    column=headers["Typ posta"],
                ).value

                topic = sheet.cell(
                    row=row_idx,
                    column=headers["Temat"],
                ).value

                logger.debug(
                    "Row %s values: cycle=%r, post_type=%r, topic=%r",
                    row_idx,
                    cycle,
                    post_type,
                    topic,
                )

                missing_fields = []

                for field_name, value in (
                    ("Cykl", cycle),
                    ("Typ posta", post_type),
                    ("Temat", topic),
                ):
                    if value is None or (isinstance(value, str) and not value.strip()):
                        missing_fields.append(field_name)

                if missing_fields:
                    logger.debug(
                        "Skipping row %s in sheet %s: missing fields: %s",
                        row_idx,
                        sheet_name,
                        missing_fields,
                    )
                    continue

                content_cell = sheet.cell(
                    row=row_idx,
                    column=headers["Treść posta"],
                )

                content_is_empty = content_cell.value is None or (
                    isinstance(content_cell.value, str)
                    and not content_cell.value.strip()
                )

                if not isinstance(content_cell, MergedCell) and content_is_empty:
                    mocked_content = (
                        "AI-GENERATED DRAFT. "
                        f"Cycle: {cycle}, "
                        f"post type: {post_type}, "
                        f"topic: {topic}"
                    )

                    content_cell.value = mocked_content

                    logger.debug(
                        "Generated content for row %s in sheet %s.",
                        row_idx,
                        sheet_name,
                    )
                else:
                    logger.debug(
                        "Preserving existing content in row %s of sheet %s.",
                        row_idx,
                        sheet_name,
                    )

                if "Hasła" in headers:
                    hashtag_cell = sheet.cell(
                        row=row_idx,
                        column=headers["Hasła"],
                    )

                    hashtags_are_empty = hashtag_cell.value is None or (
                        isinstance(hashtag_cell.value, str)
                        and not hashtag_cell.value.strip()
                    )

                    if not isinstance(hashtag_cell, MergedCell) and hashtags_are_empty:
                        hashtag_cell.value = "#ai #marketing #automation"

                        logger.debug(
                            "Generated hashtags for row %s in sheet %s.",
                            row_idx,
                            sheet_name,
                        )
                    else:
                        logger.debug(
                            "Preserving existing hashtags in row %s of sheet %s.",
                            row_idx,
                            sheet_name,
                        )

        return workbook

    async def process_calendar_file(self, file_bytes: bytes) -> bytes:
        """Process the marketing calendar Excel file."""

        workbook = await asyncio.to_thread(
            self._load_workbook_sync,
            file_bytes,
        )

        processed_workbook = await asyncio.to_thread(
            self._process_workbook_sync,
            workbook,
        )

        modified_file_bytes = await asyncio.to_thread(
            self._save_workbook_sync,
            processed_workbook,
        )

        return modified_file_bytes
