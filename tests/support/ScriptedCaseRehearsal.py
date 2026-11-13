from app.evaluation.models.EvaluationCase import EvaluationCase
from app.evaluation.models.EvaluationCaseResult import EvaluationCaseResult


class ScriptedCaseRehearsal:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def rehearse(self, case: EvaluationCase, prompt_content: str) -> EvaluationCaseResult:
        self.prompts.append(prompt_content)
        return EvaluationCaseResult(case_id=case.id, name=case.name, status="passed", detail="")
