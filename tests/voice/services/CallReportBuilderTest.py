from datetime import UTC, datetime, timedelta

from livekit.agents import ChatContext

from app.voice.services.CallReportBuilder import CallReportBuilder
from app.voice.state.CallRecord import CallRecord


class CallReportBuilderTest:
    started_at = datetime(2026, 11, 13, 10, 0, tzinfo=UTC)

    def make_record(self) -> CallRecord:
        return CallRecord(call_id="call-7", channel="phone", customer_number="+447700900123", started_at=self.started_at)

    def make_items(self):
        history = ChatContext.empty()
        start = self.started_at.timestamp()
        history.add_message(role="system", content="You are an agent.", created_at=start)
        history.add_message(role="assistant", content="Hi, how can I help?", created_at=start + 1)
        history.add_message(role="user", content="   ", created_at=start + 2)
        history.add_message(role="user", content="Where is my money?", created_at=start + 4.5)
        return history.items

    def test_keeps_only_spoken_lines_in_order(self) -> None:
        report = CallReportBuilder().build(self.make_record(), self.make_items(), self.started_at + timedelta(minutes=2))
        assert [(line.position, line.speaker, line.text) for line in report.lines] == [(0, "agent", "Hi, how can I help?"), (1, "caller", "Where is my money?")]
        assert report.lines[1].seconds_from_start == 4.5

    def test_says_the_caller_hung_up_when_nothing_else_ended_the_call(self) -> None:
        report = CallReportBuilder().build(self.make_record(), [], self.started_at)
        assert report.end_reason == "callerHungUp"

    def test_keeps_the_first_reason_the_call_ended(self) -> None:
        record = self.make_record()
        record.end("handedOff")
        record.end("callerHungUp")
        assert CallReportBuilder().build(record, [], self.started_at).end_reason == "handedOff"

    def test_sends_the_report_in_the_shape_the_backend_reads(self) -> None:
        record = self.make_record()
        record.hand_off_reason = "askedForPerson"
        body = CallReportBuilder().build(record, self.make_items(), self.started_at).model_dump(by_alias=True, mode="json")
        assert body["callId"] == "call-7"
        assert body["customerNumber"] == "+447700900123"
        assert body["handOffReason"] == "askedForPerson"
        assert body["lines"][0]["secondsFromStart"] == 1.0
