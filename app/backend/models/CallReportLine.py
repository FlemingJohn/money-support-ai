from typing import Literal

from app.common.models.CamelModel import CamelModel


class CallReportLine(CamelModel):
    position: int
    speaker: Literal["agent", "caller"]
    text: str
    seconds_from_start: float
