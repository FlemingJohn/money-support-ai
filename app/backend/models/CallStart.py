from datetime import datetime

from app.backend.models.CallChannel import CallChannel
from app.common.models.CamelModel import CamelModel


class CallStart(CamelModel):
    call_id: str
    channel: CallChannel
    started_at: datetime
