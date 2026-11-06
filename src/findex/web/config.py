from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    index_path: str = "index.bin"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

def get_settings() -> Settings:
    return Settings()