from livekit.agents import Agent, ChatContext

from app.voice.actions.CallActions import CallActions
from app.voice.tools.EndCallToolFactory import EndCallToolFactory
from app.voice.tools.HandOffToolFactory import HandOffToolFactory


class VoiceAgentFactory:
    def __init__(self, hand_off_tool_factory: HandOffToolFactory, end_call_tool_factory: EndCallToolFactory) -> None:
        self.hand_off_tool_factory = hand_off_tool_factory
        self.end_call_tool_factory = end_call_tool_factory

    def make(self, prompt_content: str, call_actions: CallActions, history: ChatContext | None = None) -> Agent:
        tools = [self.hand_off_tool_factory.make(call_actions), self.end_call_tool_factory.make(call_actions)]
        return Agent(instructions=prompt_content, tools=tools, chat_ctx=history or ChatContext.empty())
