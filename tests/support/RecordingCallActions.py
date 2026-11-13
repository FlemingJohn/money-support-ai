class RecordingCallActions:
    def __init__(self) -> None:
        self.hand_offs: list[tuple[str, str]] = []
        self.end_call_count = 0

    async def hand_off(self, reason: str, caller_need: str) -> None:
        self.hand_offs.append((reason, caller_need))

    async def end_call(self) -> None:
        self.end_call_count += 1
