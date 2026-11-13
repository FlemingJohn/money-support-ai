from datetime import datetime

from app.backend.models.CallChannel import CallChannel
from app.backend.models.CallEndReason import CallEndReason
from app.backend.models.CallReportLine import CallReportLine
from app.common.models.CamelModel import CamelModel


class CallReport(CamelModel):
    call_id: str
    channel: CallChannel
    customer_number: str | None
    started_at: datetime
    ended_at: datetime
    end_reason: CallEndReason
    hand_off_reason: str | None
    lines: list[CallReportLine]
