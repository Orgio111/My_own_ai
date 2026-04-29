"""Centralized settings — env-driven, validated by pydantic."""
from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # NVIDIA
    nvidia_api_key: str = ""
    nvidia_api_base: str = "https://integrate.api.nvidia.com/v1"

    # Models per task class
    model_reasoning: str = "meta/llama-3.1-nemotron-70b-instruct"
    model_fast: str = "meta/llama-3.1-8b-instruct"
    model_code: str = "deepseek-ai/deepseek-coder-v2-instruct"
    model_vision: str = "meta/llama-3.2-90b-vision-instruct"
    model_embed: str = "nvidia/nv-embedqa-e5-v5"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Agent
    default_agent_mode: str = "guided"
    max_parallel_agents: int = 4
    max_tokens_per_min: int = 200_000

    # Storage
    data_dir: str = "./data"
    sqlite_path: str = "./data/arajim.db"
    vector_path: str = "./data/vectors.faiss"

    # Tooling
    shell_allowed_bin: str = "ls,cat,echo,pwd,git,python,pip,node,npm,curl,grep,find"
    self_modify_enabled: bool = False
    self_modify_branch: str = "arajim/self-improve"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def shell_allowed_list(self) -> List[str]:
        return [b.strip() for b in self.shell_allowed_bin.split(",") if b.strip()]

    def ensure_dirs(self) -> None:
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
