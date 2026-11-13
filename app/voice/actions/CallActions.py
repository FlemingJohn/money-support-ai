from typing import Protocol


class CallActions(Protocol):
    async def hand_off(self, reason: str, caller_need: str) -> None: ...

    async def end_call(self) -> None: ...
