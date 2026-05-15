from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://regional:regional_dev@localhost:5437/regional_data"

    class Config:
        env_file = ".env"


settings = Settings()