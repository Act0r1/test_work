from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    log_level: str = "INFO"

    postgres_user: str = "app"
    postgres_password: str = "app"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "app"

    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672

    api_key: str = "changeme"

    webhook_timeout: float = 10.0
    webhook_max_retries: int = 3
    webhook_base_delay: float = 1.0

    POLL_INTERVAL: float = 5.0

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )


settings = Settings()
