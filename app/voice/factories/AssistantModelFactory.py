from livekit.agents import inference

from app.configuration.AppConfiguration import AppConfiguration


class AssistantModelFactory:
    longest_reply_tokens = 250

    def __init__(self, configuration: AppConfiguration) -> None:
        self.configuration = configuration

    def make(self) -> inference.LLM:
        return inference.LLM(
            self.configuration.assistant_model,
            api_key=self.configuration.livekit_api_key,
            api_secret=self.configuration.livekit_api_secret,
            extra_kwargs={"temperature": 0, "max_completion_tokens": self.longest_reply_tokens},
        )
