from tests.support.FakeSpeech import FakeSpeech


class FakeVoiceSession:
    def __init__(self) -> None:
        self.spoken: list[str] = []
        self.speeches: list[FakeSpeech] = []
        self.is_shut_down = False

    def say(self, text: str, allow_interruptions: bool = True) -> FakeSpeech:
        self.spoken.append(text)
        speech = FakeSpeech()
        self.speeches.append(speech)
        return speech

    def shutdown(self) -> None:
        self.is_shut_down = True

    def finish_speaking(self) -> None:
        for speech in self.speeches:
            speech.finish()
