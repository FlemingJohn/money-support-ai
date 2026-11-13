import httpx
from fastapi import APIRouter

from app.analysis.catalogs.MaskKindCatalog import MaskKindCatalog
from app.analysis.routes.AnalysisRouter import AnalysisRouter
from app.analysis.services.CallAnalysisGraph import CallAnalysisGraph
from app.analysis.services.CallAnalysisService import CallAnalysisService
from app.analysis.services.CheckNode import CheckNode
from app.analysis.services.FieldsNode import FieldsNode
from app.analysis.services.HandOffDetector import HandOffDetector
from app.analysis.services.LineMasker import LineMasker
from app.analysis.services.LineMaskingNode import LineMaskingNode
from app.analysis.services.OwnNumberMatcher import OwnNumberMatcher
from app.analysis.services.PieceMasker import PieceMasker
from app.analysis.services.ReviewSuggester import ReviewSuggester
from app.analysis.services.SummaryNode import SummaryNode
from app.analysis.services.TopicNode import TopicNode
from app.analysis.services.TranscriptFormatter import TranscriptFormatter
from app.assistant.routes.AssistantRouter import AssistantRouter
from app.assistant.services.AssistantSyncService import AssistantSyncService
from app.assistant.services.PromptBuilder import PromptBuilder
from app.backend.clients.BackendClient import BackendClient
from app.common.clients.AzureStructuredModel import AzureStructuredModel
from app.common.clients.StructuredModel import StructuredModel
from app.common.guards.ServiceSecretGuard import ServiceSecretGuard
from app.common.services.ServerSentEvents import ServerSentEvents
from app.common.services.TemplateRenderer import TemplateRenderer
from app.configuration.AppConfiguration import AppConfiguration
from app.evaluation.clients.ReviewTestClient import ReviewTestClient
from app.evaluation.factories.JudgeModelFactory import JudgeModelFactory
from app.evaluation.routes.EvaluationRouter import EvaluationRouter
from app.evaluation.services.CaseRehearsal import CaseRehearsal
from app.evaluation.services.EvaluationCaseLoader import EvaluationCaseLoader
from app.evaluation.services.EvaluationRunner import EvaluationRunner
from app.evaluation.services.EvaluationStreamService import EvaluationStreamService
from app.evaluation.services.TurnChecker import TurnChecker
from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.health.routes.HealthRouter import HealthRouter
from app.improvement.routes.ImprovementRouter import ImprovementRouter
from app.improvement.services.FeedbackNode import FeedbackNode
from app.improvement.services.ImprovementGraph import ImprovementGraph
from app.improvement.services.ImprovementService import ImprovementService
from app.improvement.services.ProposeRuleNode import ProposeRuleNode
from app.improvement.services.TestRuleNode import TestRuleNode
from app.voice.factories.AssistantModelFactory import AssistantModelFactory
from app.voice.factories.VoiceAgentFactory import VoiceAgentFactory
from app.voice.services.GoodbyeChecker import GoodbyeChecker
from app.voice.services.PromptInjectionGuard import PromptInjectionGuard
from app.voice.tools.EndCallToolFactory import EndCallToolFactory
from app.voice.tools.HandOffToolFactory import HandOffToolFactory


class ServiceContainer:
    def __init__(
        self,
        configuration: AppConfiguration,
        backend_http_client: httpx.AsyncClient,
        structured_model: StructuredModel,
        case_rehearsal: CaseRehearsal,
    ) -> None:
        self.configuration = configuration
        self.backend_http_client = backend_http_client
        self.structured_model = structured_model
        self.case_rehearsal = case_rehearsal
        self.template_renderer = TemplateRenderer(configuration.prompts_folder)
        self.service_secret_guard = ServiceSecretGuard(configuration)
        self.backend_client = BackendClient(backend_http_client)
        self.sync_service = AssistantSyncService(self.backend_client, PromptBuilder(self.template_renderer))

    @classmethod
    def from_configuration(cls, configuration: AppConfiguration) -> "ServiceContainer":
        backend_http_client = httpx.AsyncClient(
            base_url=configuration.backend_url,
            headers={"x-service-secret": configuration.service_secret},
            timeout=10,
        )
        return cls(configuration, backend_http_client, AzureStructuredModel(configuration), cls.make_case_rehearsal(configuration))

    @staticmethod
    def make_case_rehearsal(configuration: AppConfiguration) -> CaseRehearsal:
        prompt_injection_guard = PromptInjectionGuard()
        return CaseRehearsal(
            VoiceAgentFactory(HandOffToolFactory(HandOffReasonCatalog()), EndCallToolFactory(GoodbyeChecker()), prompt_injection_guard),
            AssistantModelFactory(configuration),
            JudgeModelFactory(configuration),
            TurnChecker(TemplateRenderer(configuration.prompts_folder)),
            prompt_injection_guard,
        )

    def make_routers(self) -> list[APIRouter]:
        return [
            HealthRouter().make(),
            AssistantRouter(self.sync_service, self.service_secret_guard).make(),
            self.make_analysis_router(),
            self.make_evaluation_router(),
            self.make_improvement_router(),
        ]

    def make_improvement_router(self) -> APIRouter:
        graph = ImprovementGraph(
            FeedbackNode(self.backend_client),
            ProposeRuleNode(self.structured_model, self.template_renderer),
            TestRuleNode(self.make_evaluation_runner()),
        )
        return ImprovementRouter(ImprovementService(graph, ServerSentEvents()), self.service_secret_guard).make()

    def make_analysis_router(self) -> APIRouter:
        line_masker = LineMasker(self.structured_model, self.template_renderer, PieceMasker(MaskKindCatalog(), OwnNumberMatcher()), MaskKindCatalog())
        transcript_formatter = TranscriptFormatter()
        graph = CallAnalysisGraph(
            LineMaskingNode(line_masker),
            SummaryNode(self.structured_model, self.template_renderer, transcript_formatter),
            TopicNode(self.structured_model, self.template_renderer, transcript_formatter),
            FieldsNode(self.structured_model, self.template_renderer, transcript_formatter),
            CheckNode(self.structured_model, self.template_renderer, transcript_formatter),
        )
        call_analysis_service = CallAnalysisService(graph, HandOffDetector(), ReviewSuggester())
        return AnalysisRouter(call_analysis_service, line_masker, self.service_secret_guard).make()

    def make_evaluation_router(self) -> APIRouter:
        runner = self.make_evaluation_runner()
        return EvaluationRouter(runner, EvaluationStreamService(runner, ServerSentEvents()), self.service_secret_guard).make()

    def make_evaluation_runner(self) -> EvaluationRunner:
        return EvaluationRunner(
            EvaluationCaseLoader(self.configuration.evaluation_cases_folder),
            self.sync_service,
            self.case_rehearsal,
            ReviewTestClient(self.backend_client),
            self.configuration.max_concurrent_runs,
        )

    async def close(self) -> None:
        await self.backend_http_client.aclose()
