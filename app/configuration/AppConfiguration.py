from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfiguration(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_secret: str
    backend_url: str = "http://localhost:4000"
    agent_name: str = "money-support"
    livekit_api_key: str | None = None
    livekit_api_secret: str | None = None
    assistant_model: str = "openai/gpt-4o"
    judge_model: str = "openai/gpt-4.1"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2025-01-01-preview"
    max_concurrent_runs: int = 10
    project_folder: Path = Path(__file__).resolve().parents[2]

    @property
    def prompts_folder(self) -> Path:
        return self.project_folder / "prompts"

    @property
    def evaluation_cases_folder(self) -> Path:
        return self.project_folder / "evaluation" / "cases"
