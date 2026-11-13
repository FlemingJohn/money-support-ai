import asyncio

from app.backend.clients.BackendClient import BackendClient
from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.handoff.services.HandOffService import HandOffService
from tests.support.FakeHttpServer import FakeHttpServer


class HandOffServiceTest:
    ring_path = ("POST", "/internal/hand-offs/ring")

    def make_service(self, backend: FakeHttpServer) -> HandOffService:
        return HandOffService(HandOffReasonCatalog(), BackendClient(backend.make_client("http://backend.test")))

    def test_rings_the_team_with_the_reason_in_plain_words(self) -> None:
        backend = FakeHttpServer({self.ring_path: {"isRung": True}})
        assert asyncio.run(self.make_service(backend).ring_team("call-1", "possibleScam", "thinks they were scammed"))
        assert backend.get_sent_bodies(*self.ring_path) == [{"callId": "call-1", "reason": "reported a possible scam", "callerNeed": "thinks they were scammed"}]

    def test_treats_an_unknown_reason_as_out_of_scope(self) -> None:
        backend = FakeHttpServer({self.ring_path: {"isRung": True}})
        asyncio.run(self.make_service(backend).ring_team("call-1", "somethingElse", ""))
        assert backend.get_sent_bodies(*self.ring_path)[0]["reason"] == "has a question the agent cannot answer"

    def test_says_the_team_was_not_rung_when_the_backend_is_down(self) -> None:
        assert not asyncio.run(self.make_service(FakeHttpServer({})).ring_team("call-1", "askedForPerson", ""))
