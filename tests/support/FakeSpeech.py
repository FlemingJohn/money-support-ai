class FakeSpeech:
    def __init__(self) -> None:
        self.callbacks = []

    def add_done_callback(self, callback) -> None:
        self.callbacks.append(callback)

    def finish(self) -> None:
        for callback in self.callbacks:
            callback(self)
