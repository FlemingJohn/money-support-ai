import re

from app.analysis.models.AnalysisRequest import AnalysisRequest


class HandOffDetector:
    hand_off_reason = "handedOff"

    def is_handed_off(self, request: AnalysisRequest) -> bool:
        if request.ended_reason == self.hand_off_reason:
            return True
        if not request.hand_off_sentence:
            return False
        sentence = self.simplify(request.hand_off_sentence)
        return any(sentence in self.simplify(line.text) for line in request.lines if line.speaker == "agent")

    def simplify(self, text: str) -> str:
        return re.sub(r"[^a-z ]", "", text.lower().replace("’", "'").replace("'", ""))
