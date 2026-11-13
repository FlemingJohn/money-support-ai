import asyncio

from livekit.agents import AgentSession, UserStateChangedEvent

from app.voice.actions.LiveCallActions import LiveCallActions


class SilenceWatcher:
    reminder = "Are you still there?"
    goodbye = "I haven't heard anything, so I'll end the call now. Goodbye."
    reminder_count = 2

    def __init__(self, session: AgentSession, call_actions: LiveCallActions, silence_seconds: int) -> None:
        self.session = session
        self.call_actions = call_actions
        self.silence_seconds = silence_seconds
        self.reminders: asyncio.Task[None] | None = None

    def watch(self) -> None:
        self.session.on("user_state_changed", self.handle_user_state)

    def handle_user_state(self, event: UserStateChangedEvent) -> None:
        self.stop()
        if event.new_state == "away":
            self.reminders = asyncio.create_task(self.remind_then_end())

    def stop(self) -> None:
        if self.reminders is not None:
            self.reminders.cancel()
            self.reminders = None

    async def remind_then_end(self) -> None:
        for _ in range(self.reminder_count):
            self.session.say(self.reminder)
            await asyncio.sleep(self.silence_seconds)
        self.call_actions.end_with(self.goodbye, "silenceTimeout")
