from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Load application configuration from environment variables."""

    PROJECT_NAME: str
    DATABASE_URL: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str

    CORS_ORIGINS: str = "http://localhost:5173"
    SQL_ECHO: bool = False

    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_NAME: str | None = None
    INSTANCE_UNIX_SOCKET: str | None = None

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

    @property
    def database_url(self) -> str | URL:
        """Return the configured local or Cloud SQL database URL."""

        if self.INSTANCE_UNIX_SOCKET:
            if not all((self.DB_USER, self.DB_PASSWORD, self.DB_NAME)):
                raise ValueError(
                    "DB_USER, DB_PASSWORD and DB_NAME are required "
                    "when INSTANCE_UNIX_SOCKET is configured."
                )

            return URL.create(
                drivername="postgresql+asyncpg",
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                database=self.DB_NAME,
                query={"host": self.INSTANCE_UNIX_SOCKET},
            )

        if self.DATABASE_URL:
            return self.DATABASE_URL

        raise ValueError(
            "DATABASE_URL or Cloud SQL database settings must be configured."
        )


settings = Settings()  # pyright: ignore[reportCallIssue]
