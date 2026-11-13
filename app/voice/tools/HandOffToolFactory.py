from livekit.agents import function_tool
from livekit.agents.llm import RawFunctionTool, StopResponse

from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.handoff.models.HandOffArguments import HandOffArguments
from app.voice.actions.CallActions import CallActions


class HandOffToolFactory:
    tool_name = "handOffToHuman"
    description = (
        "Hands the caller to the human support team. Call it without saying anything first: "
        "it tells the caller why, rings the team's phone straight away, then says the hand-off sentence and ends the call."
    )

    def __init__(self, reason_catalog: HandOffReasonCatalog) -> None:
        self.reason_catalog = reason_catalog

    def make(self, call_actions: CallActions) -> RawFunctionTool:
        async def hand_off_to_human(raw_arguments: dict[str, object]) -> None:
            arguments = HandOffArguments.model_validate(raw_arguments)
            await call_actions.hand_off(arguments.reason, arguments.caller_need)
            raise StopResponse()

        return function_tool(hand_off_to_human, raw_schema=self.make_schema())

    def make_schema(self) -> dict:
        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "enum": self.reason_catalog.reasons, "description": "Why the caller needs a person"},
                    "callerNeed": {"type": "string", "description": "What the caller needs, in a few words, with no names, numbers or other personal details"},
                },
                "required": ["reason", "callerNeed"],
            },
        }
