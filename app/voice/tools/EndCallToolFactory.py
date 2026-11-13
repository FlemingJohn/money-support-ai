from livekit.agents import RunContext, function_tool
from livekit.agents.llm import FunctionTool, StopResponse

from app.voice.actions.CallActions import CallActions
from app.voice.services.GoodbyeChecker import GoodbyeChecker


class EndCallToolFactory:
    tool_name = "endCall"
    description = "Ends the call once the caller has clearly finished. It thanks the caller and says goodbye, so say nothing yourself."
    refusal = "The call was not ended, because the caller has not said they are finished. Ask if there is anything else you can help with."

    def __init__(self, goodbye_checker: GoodbyeChecker) -> None:
        self.goodbye_checker = goodbye_checker

    def make(self, call_actions: CallActions) -> FunctionTool:
        async def end_call(context: RunContext) -> str:
            if not self.goodbye_checker.can_end_call(context.session.current_agent.chat_ctx.items):
                return self.refusal
            await call_actions.end_call()
            raise StopResponse()

        return function_tool(end_call, name=self.tool_name, description=self.description)
