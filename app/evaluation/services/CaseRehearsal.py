from livekit.agents import AgentSession, ChatContext

from app.evaluation.factories.JudgeModelFactory import JudgeModelFactory
from app.evaluation.models.EvaluationCase import EvaluationCase
from app.evaluation.models.EvaluationCaseResult import EvaluationCaseResult
from app.evaluation.services.TurnChecker import TurnChecker
from app.voice.actions.RehearsalCallActions import RehearsalCallActions
from app.voice.factories.AssistantModelFactory import AssistantModelFactory
from app.voice.factories.VoiceAgentFactory import VoiceAgentFactory
from app.voice.services.PromptInjectionGuard import PromptInjectionGuard


class CaseRehearsal:
    def __init__(
        self,
        voice_agent_factory: VoiceAgentFactory,
        assistant_model_factory: AssistantModelFactory,
        judge_model_factory: JudgeModelFactory,
        turn_checker: TurnChecker,
        prompt_injection_guard: PromptInjectionGuard,
    ) -> None:
        self.voice_agent_factory = voice_agent_factory
        self.assistant_model_factory = assistant_model_factory
        self.judge_model_factory = judge_model_factory
        self.turn_checker = turn_checker
        self.prompt_injection_guard = prompt_injection_guard

    async def rehearse(self, case: EvaluationCase, prompt_content: str) -> EvaluationCaseResult:
        try:
            await self.run_case(case, prompt_content)
        except AssertionError as error:
            return EvaluationCaseResult(case_id=case.id, name=case.name, status="failed", detail=str(error))
        except Exception as error:
            return EvaluationCaseResult(case_id=case.id, name=case.name, status="error", detail=str(error))
        return EvaluationCaseResult(case_id=case.id, name=case.name, status="passed", detail="")

    async def run_case(self, case: EvaluationCase, prompt_content: str) -> None:
        assistant_model = self.assistant_model_factory.make()
        judge_model = self.judge_model_factory.make()
        try:
            async with AgentSession(llm=assistant_model) as session:
                await session.start(self.voice_agent_factory.make(prompt_content, RehearsalCallActions(), self.make_history(case)))
                result = await session.run(user_input=self.prompt_injection_guard.clean(case.caller_line))
                await self.turn_checker.check(result, case.checked_turn, judge_model)
        finally:
            await assistant_model.aclose()
            await judge_model.aclose()

    def make_history(self, case: EvaluationCase) -> ChatContext:
        history = ChatContext.empty()
        for turn in case.earlier_turns:
            history.add_message(role=turn.role, content=turn.content)
        return history
