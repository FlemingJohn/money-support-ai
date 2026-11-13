import re

from livekit.agents.llm import ChatItem, ChatMessage


class GoodbyeChecker:
    closing_question = re.compile(r"anything else", re.IGNORECASE)
    goodbye = re.compile(
        r"\b(bye|goodbye|that['’]?s all|that is all|that['’]?s everything|nothing else|all done|i['’]?m done)\b"
        r"|^\W*(no|nope|no,? thanks?( you)?)\W*$",
        re.IGNORECASE,
    )

    def can_end_call(self, items: list[ChatItem]) -> bool:
        messages = [item for item in items if isinstance(item, ChatMessage)]
        has_asked = self.closing_question.search(self.find_last_text(messages, "assistant")) is not None
        has_said_goodbye = self.goodbye.search(self.find_last_text(messages, "user")) is not None
        return has_asked and has_said_goodbye

    def find_last_text(self, messages: list[ChatMessage], role: str) -> str:
        texts = [message.text_content or "" for message in messages if message.role == role]
        return texts[-1] if texts else ""
