from livekit.agents import Agent, ChatContext, ChatMessage

from app.voice.services.PromptInjectionGuard import PromptInjectionGuard


class GuardedAgent(Agent):
    def __init__(self, prompt_injection_guard: PromptInjectionGuard, **agent_options: object) -> None:
        super().__init__(**agent_options)
        self.prompt_injection_guard = prompt_injection_guard

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        caller_text = new_message.text_content or ""
        cleaned_text = self.prompt_injection_guard.clean(caller_text)
        if cleaned_text != caller_text:
            new_message.content = [cleaned_text]
