"""
GoldTo Backend Configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM (default: Kimi / Moonshot AI)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.moonshot.cn/v1"
    llm_model_name: str = "moonshot-v1-8k"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.3

    # Zep Cloud (optional)
    zep_api_key: str = ""

    # Simulation defaults
    simulation_rounds: int = 30
    agents_count: int = 12
    max_tokens: int = 2000

    # Data Sources
    news_api_key: str = ""                       # newsapi.org API key (optional)
    enable_real_sources: bool = False             # 是否启用真实数据源（默认 Mock）
    source_timeout: int = 15                      # 数据源请求超时（秒）

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

    @property
    def use_real_sources(self) -> bool:
        """True when real data sources are enabled and available."""
        return self.enable_real_sources


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
