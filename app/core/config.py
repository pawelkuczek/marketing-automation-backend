from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load application configuration from environment variables."""

    PROJECT_NAME: str
    DATABASE_URL: str
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str

    CORS_ORIGINS: str = "http://localhost:5173"
    SQL_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return configured CORS origins as a list."""

        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()  # pyright: ignore[reportCallIssue]
