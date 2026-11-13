import httpx

from app.backend.clients.BackendClient import BackendClient
from app.configuration.AppConfiguration import AppConfiguration
from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.handoff.services.HandOffGraph import HandOffGraph
from app.handoff.services.ReasonNode import ReasonNode
from app.handoff.services.RingTeamNode import RingTeamNode
from app.voice.catalogs.KeyTermCatalog import KeyTermCatalog
from app.voice.catalogs.VoiceCatalog import VoiceCatalog
from app.voice.factories.AssistantModelFactory import AssistantModelFactory
from app.voice.factories.CallRecordFactory import CallRecordFactory
from app.voice.factories.SessionFactory import SessionFactory
from app.voice.factories.VoiceAgentFactory import VoiceAgentFactory
from app.voice.services.CallHandler import CallHandler
from app.voice.services.CallReportBuilder import CallReportBuilder
from app.voice.services.GoodbyeChecker import GoodbyeChecker
from app.voice.services.PromptInjectionGuard import PromptInjectionGuard
from app.voice.tools.EndCallToolFactory import EndCallToolFactory
from app.voice.tools.HandOffToolFactory import HandOffToolFactory


class VoiceContainer:
    def __init__(self, configuration: AppConfiguration, backend_http_client: httpx.AsyncClient) -> None:
        self.backend_http_client = backend_http_client
        backend_client = BackendClient(backend_http_client)
        reason_catalog = HandOffReasonCatalog()
        self.call_handler = CallHandler(
            backend_client,
            SessionFactory(AssistantModelFactory(configuration), VoiceCatalog(), KeyTermCatalog()),
            VoiceAgentFactory(HandOffToolFactory(reason_catalog), EndCallToolFactory(GoodbyeChecker()), PromptInjectionGuard()),
            CallRecordFactory(),
            CallReportBuilder(),
            HandOffGraph(ReasonNode(reason_catalog), RingTeamNode(backend_client)),
            reason_catalog,
        )

    @classmethod
    def from_configuration(cls, configuration: AppConfiguration) -> "VoiceContainer":
        backend_http_client = httpx.AsyncClient(
            base_url=configuration.backend_url,
            headers={"x-service-secret": configuration.service_secret},
            timeout=10,
        )
        return cls(configuration, backend_http_client)

    async def close(self) -> None:
        await self.backend_http_client.aclose()
