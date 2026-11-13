from datetime import UTC, datetime

from livekit import rtc

from app.voice.state.CallRecord import CallRecord


class CallRecordFactory:
    phone_number_attribute = "sip.phoneNumber"

    def make(self, room_name: str, caller: rtc.RemoteParticipant) -> CallRecord:
        is_phone_call = caller.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
        return CallRecord(
            call_id=room_name,
            channel="phone" if is_phone_call else "web",
            customer_number=caller.attributes.get(self.phone_number_attribute) if is_phone_call else None,
            started_at=datetime.now(UTC),
        )
