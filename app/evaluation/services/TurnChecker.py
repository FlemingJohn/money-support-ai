from livekit.agents import NOT_GIVEN, RunResult
from livekit.agents.llm import LLM
from livekit.agents.voice.run_result import FunctionCallEvent

from app.common.services.TemplateRenderer import TemplateRenderer
from app.evaluation.models.EvaluationTurn import EvaluationTurn


class TurnChecker:
    hand_off_tool = "handOffToHuman"
    end_call_tool = "endCall"

    def __init__(self, template_renderer: TemplateRenderer) -> None:
        self.template_renderer = template_renderer

    async def check(self, result: RunResult, turn: EvaluationTurn, judge_model: LLM) -> None:
        if turn.check == "handsOff":
            self.check_hand_off(result, turn)
        elif turn.check == "endsCall":
            result.expect.contains_function_call(name=self.end_call_tool)
        else:
            await self.check_answer(result, turn, judge_model)

    def check_hand_off(self, result: RunResult, turn: EvaluationTurn) -> None:
        arguments = {"reason": turn.reason} if turn.reason else NOT_GIVEN
        result.expect.contains_function_call(name=self.hand_off_tool, arguments=arguments)

    async def check_answer(self, result: RunResult, turn: EvaluationTurn, judge_model: LLM) -> None:
        if self.has_called(result, self.hand_off_tool):
            raise AssertionError("It handed off instead of answering.")
        intent = self.template_renderer.render("evaluation/Judge.md", expectation=turn.expectation)
        await result.expect.contains_message(role="assistant").judge(judge_model, intent=intent)

    def has_called(self, result: RunResult, tool_name: str) -> bool:
        return any(isinstance(event, FunctionCallEvent) and event.item.name == tool_name for event in result.events)
