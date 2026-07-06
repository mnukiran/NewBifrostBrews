from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: str
    admin_username: str
    admin_password_hash: str = ""
    database_url: str = "sqlite:///data/bifrost.db"
    site_url: str = "http://localhost:8000"
    site_tz: str = "Asia/Kolkata"
    env: str = "dev"

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"


settings = Settings()
