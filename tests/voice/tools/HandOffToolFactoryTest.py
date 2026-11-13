import asyncio

import pytest
from livekit.agents.llm import StopResponse

from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.voice.tools.HandOffToolFactory import HandOffToolFactory
from tests.support.RecordingCallActions import RecordingCallActions


class HandOffToolFactoryTest:
    factory = HandOffToolFactory(HandOffReasonCatalog())

    def test_offers_every_known_reason_to_the_model(self) -> None:
        schema = self.factory.make(RecordingCallActions()).info.raw_schema
        assert schema["name"] == "handOffToHuman"
        assert schema["parameters"]["properties"]["reason"]["enum"] == HandOffReasonCatalog().reasons

    def test_hands_off_with_the_reason_and_need_then_stays_quiet(self) -> None:
        call_actions = RecordingCallActions()
        tool = self.factory.make(call_actions)
        with pytest.raises(StopResponse):
            asyncio.run(tool(raw_arguments={"reason": "askedForPerson", "callerNeed": "money to Spain not arrived"}))
        assert call_actions.hand_offs == [("askedForPerson", "money to Spain not arrived")]

    def test_treats_missing_arguments_as_out_of_scope(self) -> None:
        call_actions = RecordingCallActions()
        with pytest.raises(StopResponse):
            asyncio.run(self.factory.make(call_actions)(raw_arguments={}))
        assert call_actions.hand_offs == [("outOfScope", "")]
