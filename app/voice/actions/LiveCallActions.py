from livekit.agents import AgentSession

from app.backend.models.CallEndReason import CallEndReason
from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.handoff.services.HandOffService import HandOffService
from app.voice.state.CallRecord import CallRecord


class LiveCallActions:
    closing_line = "Thanks for calling Wise. Take care."

    def __init__(
        self,
        session: AgentSession,
        call_record: CallRecord,
        hand_off_sentence: str,
        hand_off_service: HandOffService,
        reason_catalog: HandOffReasonCatalog,
    ) -> None:
        self.session = session
        self.call_record = call_record
        self.hand_off_sentence = hand_off_sentence
        self.hand_off_service = hand_off_service
        self.reason_catalog = reason_catalog

    async def hand_off(self, reason: str, caller_need: str) -> None:
        known_reason = self.reason_catalog.normalise(reason)
        self.call_record.hand_off_reason = known_reason
        self.session.say(self.reason_catalog.openings[known_reason], allow_interruptions=False)
        await self.hand_off_service.ring_team(self.call_record.call_id, known_reason, caller_need)
        self.end_with(self.hand_off_sentence, "handedOff")

    async def end_call(self) -> None:
        self.end_with(self.closing_line, "agentEndedCall")

    def end_with(self, last_line: str, end_reason: CallEndReason) -> None:
        self.call_record.end(end_reason)
        speech = self.session.say(last_line, allow_interruptions=False)
        speech.add_done_callback(lambda _: self.session.shutdown())
