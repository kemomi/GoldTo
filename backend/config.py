"""
GoldTo Backend Configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    llm_api_key: str = "sk-placeholder"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model_name: str = "qwen-plus"

    # Zep Cloud (optional)
    zep_api_key: str = ""

    # Simulation defaults
    simulation_rounds: int = 30
    agents_count: int = 12
    max_tokens: int = 2000

    # Paths
    upload_dir: Path = Path("uploads")

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
