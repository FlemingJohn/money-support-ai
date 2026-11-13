from dataclasses import dataclass
from datetime import datetime

from app.backend.models.CallChannel import CallChannel
from app.backend.models.CallEndReason import CallEndReason


@dataclass
class CallRecord:
    call_id: str
    channel: CallChannel
    customer_number: str | None
    started_at: datetime
    end_reason: CallEndReason | None = None
    hand_off_reason: str | None = None

    def end(self, reason: CallEndReason) -> None:
        if self.end_reason is None:
            self.end_reason = reason
