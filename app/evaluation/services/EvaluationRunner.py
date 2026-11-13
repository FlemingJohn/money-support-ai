import asyncio

from app.assistant.services.AssistantSyncService import AssistantSyncService
from app.backend.exceptions.BackendRequestError import BackendRequestError
from app.evaluation.clients.ReviewTestClient import ReviewTestClient
from app.evaluation.models.EvaluationCase import EvaluationCase
from app.evaluation.models.EvaluationCaseResult import EvaluationCaseResult
from app.evaluation.models.EvaluationProgress import EvaluationProgress
from app.evaluation.models.EvaluationReport import EvaluationReport
from app.evaluation.services.CaseRehearsal import CaseRehearsal
from app.evaluation.services.EvaluationCaseLoader import EvaluationCaseLoader


class EvaluationRunner:
    def __init__(
        self,
        case_loader: EvaluationCaseLoader,
        sync_service: AssistantSyncService,
        case_rehearsal: CaseRehearsal,
        review_test_client: ReviewTestClient,
        max_concurrent_runs: int,
    ) -> None:
        self.case_loader = case_loader
        self.sync_service = sync_service
        self.case_rehearsal = case_rehearsal
        self.review_test_client = review_test_client
        self.run_limit = asyncio.Semaphore(max_concurrent_runs)

    async def run(self, extra_rules: list[str] | None = None, progress: EvaluationProgress | None = None) -> EvaluationReport:
        draft = await self.sync_service.make_draft(extra_rules)
        cases = self.case_loader.load_cases() + await self.load_review_cases()
        if progress:
            await progress.on_start(len(cases))
        results = await asyncio.gather(*[self.run_reported_case(case, draft.prompt_content, progress) for case in cases])
        return EvaluationReport.from_results(list(results))

    async def load_review_cases(self) -> list[EvaluationCase]:
        try:
            return await self.review_test_client.get_review_tests()
        except BackendRequestError:
            return []

    async def run_reported_case(self, case: EvaluationCase, prompt_content: str, progress: EvaluationProgress | None) -> EvaluationCaseResult:
        async with self.run_limit:
            result = await self.case_rehearsal.rehearse(case, prompt_content)
        if progress:
            await progress.on_result(result)
        return result
