from livekit.agents import inference

from app.configuration.AppConfiguration import AppConfiguration


class JudgeModelFactory:
    def __init__(self, configuration: AppConfiguration) -> None:
        self.configuration = configuration

    def make(self) -> inference.LLM:
        return inference.LLM(
            self.configuration.judge_model,
            api_key=self.configuration.livekit_api_key,
            api_secret=self.configuration.livekit_api_secret,
        )
