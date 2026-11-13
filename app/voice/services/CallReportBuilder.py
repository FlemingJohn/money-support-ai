from datetime import datetime

from livekit.agents.llm import ChatItem, ChatMessage

from app.backend.models.CallReport import CallReport
from app.backend.models.CallReportLine import CallReportLine
from app.backend.models.CallStart import CallStart
from app.voice.state.CallRecord import CallRecord


class CallReportBuilder:
    speakers_by_role = {"user": "caller", "assistant": "agent"}

    def build_start(self, call_record: CallRecord) -> CallStart:
        return CallStart(call_id=call_record.call_id, channel=call_record.channel, started_at=call_record.started_at)

    def build(self, call_record: CallRecord, items: list[ChatItem], ended_at: datetime) -> CallReport:
        return CallReport(
            call_id=call_record.call_id,
            channel=call_record.channel,
            customer_number=call_record.customer_number,
            started_at=call_record.started_at,
            ended_at=ended_at,
            end_reason=call_record.end_reason or "callerHungUp",
            hand_off_reason=call_record.hand_off_reason,
            lines=self.make_lines(call_record, items),
        )

    def make_lines(self, call_record: CallRecord, items: list[ChatItem]) -> list[CallReportLine]:
        spoken = [item for item in items if self.is_spoken_line(item)]
        start = call_record.started_at.timestamp()
        return [
            CallReportLine(position=position, speaker=self.speakers_by_role[item.role], text=item.text_content, seconds_from_start=max(0.0, item.created_at - start))
            for position, item in enumerate(spoken)
        ]

    def is_spoken_line(self, item: ChatItem) -> bool:
        return isinstance(item, ChatMessage) and item.role in self.speakers_by_role and bool((item.text_content or "").strip())
