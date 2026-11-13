import asyncio
from datetime import UTC, datetime

from app.backend.clients.BackendClient import BackendClient
from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.handoff.services.HandOffGraph import HandOffGraph
from app.handoff.services.ReasonNode import ReasonNode
from app.handoff.services.RingTeamNode import RingTeamNode
from app.voice.actions.LiveCallActions import LiveCallActions
from app.voice.state.CallRecord import CallRecord
from tests.support.FakeHttpServer import FakeHttpServer
from tests.support.FakeVoiceSession import FakeVoiceSession
from tests.support.SampleData import SampleData


class LiveCallActionsTest:
    ring_path = ("POST", "/internal/hand-offs/ring")

    def make_actions(self, backend: FakeHttpServer) -> tuple[LiveCallActions, FakeVoiceSession, CallRecord]:
        session = FakeVoiceSession()
        record = CallRecord(call_id="call-1", channel="web", customer_number=None, started_at=datetime.now(UTC))
        reason_catalog = HandOffReasonCatalog()
        graph = HandOffGraph(ReasonNode(reason_catalog), RingTeamNode(BackendClient(backend.make_client("http://backend.test"))))
        return LiveCallActions(session, record, SampleData.hand_off_sentence, graph, reason_catalog), session, record

    def test_hand_off_says_why_rings_the_team_then_says_the_sentence(self) -> None:
        backend = FakeHttpServer({self.ring_path: {"isRung": True}})
        actions, session, record = self.make_actions(backend)
        asyncio.run(actions.hand_off("askedForPerson", "money to Spain not arrived"))
        assert session.spoken == [HandOffReasonCatalog.openings["askedForPerson"], SampleData.hand_off_sentence]
        assert backend.get_sent_bodies(*self.ring_path) == [{"callId": "call-1", "reason": "asked to speak to a person", "callerNeed": "money to Spain not arrived"}]
        assert (record.end_reason, record.hand_off_reason) == ("handedOff", "askedForPerson")

    def test_hand_off_still_ends_the_call_when_the_team_cannot_be_rung(self) -> None:
        actions, session, record = self.make_actions(FakeHttpServer({}))
        asyncio.run(actions.hand_off("somethingElse", ""))
        assert record.hand_off_reason == "outOfScope"
        assert session.spoken[-1] == SampleData.hand_off_sentence

    def test_ends_the_call_only_after_the_last_line_is_spoken(self) -> None:
        actions, session, record = self.make_actions(FakeHttpServer({}))
        asyncio.run(actions.end_call())
        assert session.spoken == [LiveCallActions.closing_line]
        assert not session.is_shut_down
        session.finish_speaking()
        assert session.is_shut_down
        assert record.end_reason == "agentEndedCall"
