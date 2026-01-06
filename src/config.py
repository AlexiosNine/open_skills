"""Configuration management for Skill Host."""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except ImportError:
    # python-dotenv is optional
    pass


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        # Required environment variables
        self.http_base_url: str = os.getenv(
            "OPENSKILL_HTTP_BASE_URL", "http://127.0.0.1:8000"
        )
        self.allowed_root: Path = Path(
            os.getenv("OPENSKILL_ALLOWED_ROOT", "./data")
        ).resolve()
        self.cli_dir: Path = Path(
            os.getenv("OPENSKILL_CLI_DIR", "./skill_cli")
        ).resolve()

        # Optional environment variables
        timeout_ms_str = os.getenv("OPENSKILL_TIMEOUT_MS", "15000")
        try:
            self.timeout_ms: int = int(timeout_ms_str)
            if self.timeout_ms <= 0:
                raise ValueError("timeout_ms must be > 0")
            if self.timeout_ms > 300000:  # 5 minutes
                logger.warning(f"timeout_ms ({self.timeout_ms}) is very large, consider reducing it")
        except ValueError as e:
            raise ValueError(f"Invalid OPENSKILL_TIMEOUT_MS value: {timeout_ms_str}. {e}")
        self.debug: bool = os.getenv("OPENSKILL_DEBUG", "0") == "1"

        # LLM API Configuration
        # OpenAI API
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_api_base: str = os.getenv(
            "OPENAI_API_BASE", "https://api.openai.com/v1"
        )
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        # Anthropic Claude API
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_api_base: str = os.getenv(
            "ANTHROPIC_API_BASE", "https://api.anthropic.com"
        )
        self.anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

        # Alibaba DashScope/Qianwen API (阿里百炼)
        self.dashscope_api_key: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
        self.dashscope_api_base: str = os.getenv(
            "DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/api/v1"
        )
        self.dashscope_model: str = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

        # Other LLM APIs (通用配置)
        self.llm_api_key: Optional[str] = os.getenv("LLM_API_KEY")
        self.llm_api_base: Optional[str] = os.getenv("LLM_API_BASE")
        self.llm_model: Optional[str] = os.getenv("LLM_MODEL")
        self.llm_provider: Optional[str] = os.getenv("LLM_PROVIDER")  # openai, anthropic, custom

        # Validate required paths exist
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        if not self.cli_dir.exists():
            raise ValueError(
                f"OPENSKILL_CLI_DIR does not exist: {self.cli_dir}"
            )
        if not self.cli_dir.is_dir():
            raise ValueError(
                f"OPENSKILL_CLI_DIR is not a directory: {self.cli_dir}"
            )

        # Create allowed_root if it doesn't exist
        if not self.allowed_root.exists():
            self.allowed_root.mkdir(parents=True, exist_ok=True)

    def get_skill_script_path(self, skill_id: str) -> Path:
        """Get the path to a skill script."""
        return self.cli_dir / f"{skill_id}.py"

    def has_llm_config(self) -> bool:
        """Check if any LLM API is configured."""
        return bool(
            self.openai_api_key
            or self.anthropic_api_key
            or self.dashscope_api_key
            or self.llm_api_key
        )

    def get_llm_providers(self) -> list[str]:
        """Get list of configured LLM providers."""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.dashscope_api_key:
            providers.append("dashscope")
        if self.llm_api_key:
            providers.append("custom")
        return providers


# Global config instance
config = Config()

