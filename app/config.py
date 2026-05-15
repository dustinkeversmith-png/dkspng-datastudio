from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://regional:regional@localhost:5437/regional_data"
    raw_data_dir: str = "./data/raw"
    staged_data_dir: str = "./data/staged"
    normalized_data_dir: str = "./data/normalized"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
