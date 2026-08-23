from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Main application configuration class that loads environment variables.

    Inherits from BaseSettings provided by pydantic-settings. Implements the
    Fail-Fast pattern: if a required variable (e.g. DATABASE_URL) is missing
    from the .env file or has an invalid type, the application will immediately
    raise an exception and fail to start.
    """

    PROJECT_NAME: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    OPENAI_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings() # pyright: ignore[reportCallIssue]
