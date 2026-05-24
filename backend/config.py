"""
GoldTo Backend Configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model_name: str = "qwen-plus"

    # Zep Cloud (optional)
    zep_api_key: str = ""

    # Simulation defaults
    simulation_rounds: int = 30
    agents_count: int = 12
    max_tokens: int = 2000

    # WorldMonitor integration
    worldmonitor_base_url: str = "http://localhost:3000"
    worldmonitor_timeout: float = 120.0

    # Paths
    upload_dir: Path = Path("uploads")

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_mock(self) -> bool:
        """True when running without a real LLM API key."""
        _placeholders = {"", "sk-placeholder", "your_api_key_here", "your_api_key"}
        key = (self.llm_api_key or "").strip()
        return key in _placeholders or key.startswith("your_")


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
