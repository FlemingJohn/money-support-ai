import asyncio

from langgraph.config import get_stream_writer

from app.evaluation.models.EvaluationCaseResult import EvaluationCaseResult
from app.evaluation.models.EvaluationProgress import EvaluationProgress
from app.evaluation.services.EvaluationRunner import EvaluationRunner
from app.improvement.state.ImprovementState import ImprovementState


class TestRuleNode:
    def __init__(self, evaluation_runner: EvaluationRunner) -> None:
        self.evaluation_runner = evaluation_runner

    async def __call__(self, state: ImprovementState) -> dict:
        write = get_stream_writer()
        write({"type": "step", "step": "tests", "status": "active"})
        counts = {"done": 0, "total": 0}
        progress = EvaluationProgress(on_start=lambda total: self.add_total(counts, total), on_result=lambda result: self.add_result(counts, result, write))
        before, after = await asyncio.gather(self.evaluation_runner.run(progress=progress), self.evaluation_runner.run([state["rule_text"]], progress))
        write({"type": "step", "step": "tests", "status": "done", "detail": f"{before.passed_count} → {after.passed_count} of {len(after.results)} passed"})
        return {"passed_before": before.passed_count, "passed_after": after.passed_count, "total_tests": len(after.results)}

    async def add_total(self, counts: dict, total: int) -> None:
        counts["total"] += total

    async def add_result(self, counts: dict, result: EvaluationCaseResult, write) -> None:
        counts["done"] += 1
        write({"type": "progress", "done": counts["done"], "total": counts["total"]})
