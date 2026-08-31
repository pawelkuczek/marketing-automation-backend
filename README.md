# Marketing Automation Backend - ETL Service

A backend service for automating social media content generation from Excel-based marketing calendars.

The application processes existing `.xlsx` content calendars, identifies posts that still require content, generates copy and supporting hashtags/keywords using the OpenAI API, and returns an updated workbook while preserving the original calendar structure.

The project was built around a real recurring marketing workflow where social media plans are prepared in Excel and completed manually each month. Based on feedback from the intended user, automating this workflow is expected to save approximately **3–5 hours of repetitive work per month**, potentially more depending on the size of the content calendar.

Rather than replacing the existing workflow with another planning tool, the application integrates AI-assisted content generation directly into the spreadsheet-based process already used by the marketer.

## Features

### Excel calendar processing

Upload an existing `.xlsx` social media calendar and receive a processed workbook containing generated marketing content.

The processor:

* works with Excel workbooks in memory,
* supports workbooks containing multiple worksheets,
* identifies columns by their header names rather than fixed positions,
* skips rows without the required source information,
* preserves content that has already been written,
* optionally generates hashtags and keywords when the `Hasła` column exists,
* stops processing a worksheet when it reaches the `STORIES` section,
* preserves the workbook structure instead of creating a new spreadsheet from scratch.

Required columns:

```text
Cykl
Typ posta
Temat
Treść posta
```

Optional column:

```text
Hasła
```

For each eligible row, the generation context is built from:

```text
Cycle
Post type
Topic
```

If `Treść posta` is empty, the application generates the post content.

If the optional `Hasła` column exists and is empty, the application generates five hashtags and five relevant keywords or key phrases.

Existing content is not overwritten.

### OpenAI integration

Content generation uses the OpenAI Responses API.

The integration includes:

* asynchronous API requests,
* configurable OpenAI model selection,
* bounded request concurrency,
* automatic retries for transient API failures,
* detection of empty model responses.

The model and API key are configured through environment variables rather than hardcoded in the application.

### Prompt management

System prompts used for content generation are stored in PostgreSQL and can be managed independently from the application code.

The API supports:

* creating prompts,
* listing prompt history,
* retrieving a single prompt,
* editing prompt content,
* manually activating a selected prompt,
* deleting inactive prompts.

Only one prompt is intended to be active at a time.

Creating a new prompt automatically activates it and deactivates previously active prompts. Editing a prompt does not change its activation status, allowing prompt versions to be modified without unexpectedly changing the configuration used for generation.

The currently active prompt cannot be deleted.

This makes prompt iteration possible without redeploying or modifying application code.

## Processing workflow

```text
Excel calendar (.xlsx)
        |
        v
FastAPI upload endpoint
        |
        v
CalendarProcessingService
        |
        +----> Load active prompt from PostgreSQL
        |
        +----> Analyze workbook
        |       |
        |       +----> Find eligible rows
        |       +----> Preserve existing content
        |
        +----> Generate content through OpenAI
        |
        +----> Apply generated results
        |
        v
Processed Excel workbook
        |
        v
File download
```

The responsibilities are separated between services:

* `ExcelProcessorService` handles workbook parsing and modification.
* `CalendarProcessingService` coordinates the complete processing workflow.
* `LLMService` handles communication with the OpenAI API.
* `PromptService` contains prompt-management business rules.
* `PromptRepository` isolates database queries from business logic.

## Architecture

The backend follows a layered structure:

```text
API / Routers
     |
     v
Services
     |
     v
Repositories
     |
     v
SQLAlchemy
     |
     v
PostgreSQL
```

External AI generation is isolated behind `LLMService`, while spreadsheet operations are handled separately by `ExcelProcessorService`.

This keeps HTTP handling, business rules, persistence, Excel processing, and external API communication from being tightly coupled.

## Tech stack

**Backend**

* Python
* FastAPI
* Pydantic
* SQLAlchemy 2
* PostgreSQL
* asyncpg

**AI**

* OpenAI Responses API
* Tenacity

**Excel processing**

* OpenPyXL

**Database migrations**

* Alembic

**Testing and code quality**

* pytest
* pytest-asyncio
* Ruff

**Local infrastructure**

* Docker Compose
* PostgreSQL 16

## API

### Process Excel calendar

```http
POST /excel/process-calendar
```

Accepts an `.xlsx` file as multipart form data and returns the processed workbook.

Files with unsupported extensions are rejected.

### Prompt endpoints

```http
POST   /prompts
GET    /prompts
GET    /prompts/{prompt_id}
PATCH  /prompts/{prompt_id}
PATCH  /prompts/{prompt_id}/activate
DELETE /prompts/{prompt_id}
```

FastAPI provides interactive API documentation after starting the application:

```text
http://localhost:8000/docs
```

## Project structure

```text
app/
├── api/
│   └── routers/
│       ├── excel.py
│       └── prompt.py
│
├── core/
│   ├── config.py
│   └── database.py
│
├── models/
│   ├── base.py
│   ├── prompt.py
│   └── ai_usage_log.py
│
├── repositories/
│   └── prompt.py
│
├── schemas/
│   └── prompt.py
│
├── services/
│   ├── calendar_processing.py
│   ├── excel_processor.py
│   ├── llm.py
│   └── prompt.py
│
└── main.py

migrations/
tests/
docker-compose.yml
alembic.ini
requirements.txt
```

## Getting started

### Prerequisites

You need:

* Python 3.13+
* Docker and Docker Compose
* an OpenAI API key

### 1. Clone the repository

```bash
git clone <repository-url>
cd marketing-automation-backend
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example configuration:

```bash
cp .env.example .env
```

Configure the values in `.env`:

```env
PROJECT_NAME=Marketing Automation Backend

POSTGRES_USER=<user>
POSTGRES_PASSWORD=<password>
POSTGRES_DB=<database>

DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/<database>

OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=<openai-model>
```

Do not commit `.env` or real credentials to version control.

### 5. Start PostgreSQL

```bash
docker compose up -d
```

The Docker Compose configuration reads PostgreSQL credentials from environment variables.

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive Swagger documentation:

```text
http://localhost:8000/docs
```

## Testing

The project contains automated tests covering multiple layers of the application, including:

* Excel workbook processing,
* calendar-processing orchestration,
* OpenAI service behavior,
* prompt business logic,
* prompt repository operations,
* prompt API endpoints,
* database-backed prompt behavior.

Tests use a dedicated PostgreSQL test database rather than the development database.

Create the test environment configuration:

```bash
cp .env.test.example .env.test
```

Configure the test database URL and load the environment variables before running the suite.

On Linux/macOS:

```bash
set -a
source .env.test
set +a

pytest -q
```

The current backend test suite contains **91 passing test cases**.

## Code quality

Run Ruff against the entire repository:

```bash
ruff check .
```

Automatically fix supported issues with:

```bash
ruff check . --fix
```

Before merging backend changes, the expected local checks are:

```bash
ruff check .
pytest -q
```

## Design decisions

### Keep the existing Excel workflow

The application deliberately works with existing marketing calendars instead of introducing a new calendar format or requiring the user to move the planning process into another system.

The workbook is treated as the input and output interface.

This decision is important to the project's goal: reduce repetitive work without forcing a non-technical user to adopt a completely different content-planning workflow.

### Do not overwrite human-written content

Generation is performed only when the relevant destination cell is empty.

This allows AI-generated and manually written content to coexist in the same calendar and prevents the application from replacing content that has already been prepared.

### Separate Excel processing from AI generation

`ExcelProcessorService` does not need to know how OpenAI requests are performed.

It discovers generation work and applies results, while `CalendarProcessingService` coordinates AI generation.

This separation also makes spreadsheet behavior testable without making real API calls.

### Store prompts outside application code

Prompts change more frequently than backend logic.

Persisting them in PostgreSQL allows prompt versions to be created, edited, reviewed, and activated without changing source code or redeploying the application.

### Keep external requests bounded

OpenAI requests are asynchronous, but concurrency is intentionally limited instead of starting an unrestricted number of API calls.

Transient OpenAI errors are retried with exponential backoff.

### Keep Excel operations away from the event loop

OpenPyXL performs synchronous workbook operations. Potentially blocking workbook loading, scanning, modification, and serialization are therefore executed outside the main asynchronous event loop.

## Current status

The backend MVP currently provides:

* Excel calendar upload and processing,
* real OpenAI content generation,
* PostgreSQL-backed prompt management,
* prompt version activation,
* asynchronous processing orchestration,
* database migrations,
* automated tests,
* Docker-based local PostgreSQL setup.

The backend is ready to serve as the API layer for the planned web interface.

## Roadmap

Planned improvements include:

* web interface designed for a non-technical user,
* drag-and-drop calendar upload and processed-file download,
* visual prompt management,
* generation progress and error feedback,
* production deployment,
* AI usage and cost monitoring,
* structured validation of generated model output,
* integration with external keyword-research data sources.

The repository already contains the beginning of an AI usage data model, but usage and cost tracking are intentionally outside the current MVP and are not yet exposed as application functionality.

## Motivation

This project was created to automate a recurring real-world marketing task rather than as an isolated API demonstration.

The intended user prepares social media content calendars in Excel and currently has to complete much of the content-writing workflow manually. Based on their estimate, automating the repetitive part of this process is expected to save approximately **3–5 hours each month**, with the potential for greater savings for larger calendars.

The goal is not to replace the existing planning process, but to remove repetitive work from it.

The marketer continues preparing the calendar in a familiar Excel format, while the application identifies unfinished entries, generates the required content, and returns the completed workbook in the same format.

Beyond solving that practical problem, the project demonstrates the design of a Python backend involving asynchronous APIs, relational database persistence, external AI integration, spreadsheet processing, automated testing, migrations, and separation of responsibilities.
