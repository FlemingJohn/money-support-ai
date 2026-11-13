class VoiceCatalog:
    speech_model = "inworld/inworld-tts-1.5"
    voices_by_name = {"Elliot": "Dennis", "Kylie": "Ashley", "Rohan": "Edward"}

    def get_voice(self, voice_name: str) -> str:
        return self.voices_by_name[voice_name]
