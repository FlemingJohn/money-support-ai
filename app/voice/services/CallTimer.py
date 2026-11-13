import asyncio

from app.voice.actions.LiveCallActions import LiveCallActions


class CallTimer:
    time_limit_line = "We've reached the time limit for this call, so I'll end it now. Goodbye."

    def start(self, longest_call_minutes: int, call_actions: LiveCallActions) -> asyncio.Task[None]:
        return asyncio.create_task(self.end_after(longest_call_minutes * 60, call_actions))

    async def end_after(self, seconds: float, call_actions: LiveCallActions) -> None:
        await asyncio.sleep(seconds)
        call_actions.end_with(self.time_limit_line, "timeLimit")
