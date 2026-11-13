from livekit.agents import AgentSession, inference, room_io
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.english import EnglishModel

from app.backend.models.AgentSettings import AgentSettings
from app.backend.models.CallChannel import CallChannel
from app.voice.catalogs.KeyTermCatalog import KeyTermCatalog
from app.voice.catalogs.VoiceCatalog import VoiceCatalog
from app.voice.factories.AssistantModelFactory import AssistantModelFactory


class SessionFactory:
    transcription_model = "deepgram/nova-3"
    shortest_pause_seconds = 0.6
    fewest_interrupting_words = 2

    def __init__(self, assistant_model_factory: AssistantModelFactory, voice_catalog: VoiceCatalog, key_term_catalog: KeyTermCatalog) -> None:
        self.assistant_model_factory = assistant_model_factory
        self.voice_catalog = voice_catalog
        self.key_term_catalog = key_term_catalog

    def make(self, agent: AgentSettings) -> AgentSession:
        return AgentSession(
            stt=inference.STT(self.transcription_model, language=agent.language, extra_kwargs={"keyterm": self.key_term_catalog.key_terms}),
            llm=self.assistant_model_factory.make(),
            tts=inference.TTS(self.voice_catalog.speech_model, voice=self.voice_catalog.get_voice(agent.voice)),
            vad=silero.VAD.load(),
            turn_handling={
                "turn_detection": EnglishModel(),
                "endpointing": {"min_delay": self.shortest_pause_seconds},
                "interruption": {"min_words": self.fewest_interrupting_words},
            },
            user_away_timeout=agent.silence_seconds,
        )

    def make_room_options(self, channel: CallChannel) -> room_io.RoomOptions:
        denoiser = noise_cancellation.BVCTelephony() if channel == "phone" else noise_cancellation.BVC()
        return room_io.RoomOptions(audio_input=room_io.AudioInputOptions(noise_cancellation=denoiser), delete_room_on_close=True)
