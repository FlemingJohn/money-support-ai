import asyncio
from types import SimpleNamespace

import pytest
from livekit.agents import ChatContext
from livekit.agents.llm import StopResponse

from app.voice.services.GoodbyeChecker import GoodbyeChecker
from app.voice.tools.EndCallToolFactory import EndCallToolFactory
from tests.support.RecordingCallActions import RecordingCallActions


class EndCallToolFactoryTest:
    factory = EndCallToolFactory(GoodbyeChecker())

    def make_context(self, agent_line: str, caller_line: str) -> SimpleNamespace:
        history = ChatContext.empty()
        history.add_message(role="assistant", content=agent_line)
        history.add_message(role="user", content=caller_line)
        return SimpleNamespace(session=SimpleNamespace(current_agent=SimpleNamespace(chat_ctx=history)))

    def test_ends_the_call_when_the_caller_has_finished(self) -> None:
        call_actions = RecordingCallActions()
        with pytest.raises(StopResponse):
            asyncio.run(self.factory.make(call_actions)(context=self.make_context("Anything else?", "No, bye!")))
        assert call_actions.end_call_count == 1

    def test_tells_the_model_to_check_first_when_the_caller_has_not_finished(self) -> None:
        call_actions = RecordingCallActions()
        answer = asyncio.run(self.factory.make(call_actions)(context=self.make_context("Log in and open the transfer.", "Okay")))
        assert answer == EndCallToolFactory.refusal
        assert call_actions.end_call_count == 0
