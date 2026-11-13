from app.backend.models.AssistantSettings import AssistantSettings
from app.backend.models.Faq import Faq
from app.configuration.AppConfiguration import AppConfiguration


class SampleData:
    hand_off_sentence = "That's not something I can help with on this line, so I'm transferring you to a human agent."

    def make_configuration(self, **overrides: object) -> AppConfiguration:
        return AppConfiguration(_env_file=None, service_secret="secret", **overrides)

    def make_faqs(self) -> list[Faq]:
        return [
            Faq(id="faq-2", number=2, question="When will my money arrive?", answer="Check the estimate on the transfer.", category="arrival", is_active=True),
            Faq(id="faq-1", number=1, question="How do I check my transfer's status?", answer="Log in and open the transfer.", category="status", is_active=True),
        ]

    def make_faq_rows(self) -> list[dict]:
        return [faq.model_dump(by_alias=True) | {"updatedAt": "2026-11-03T10:00:00.000Z"} for faq in self.make_faqs()]

    def make_settings_rows(self) -> dict:
        return {
            "agent": {
                "assistantName": "Money Support Agent",
                "language": "en",
                "greeting": "Hi, how can I help?",
                "voice": "Elliot",
                "longestCallMinutes": 10,
                "silenceSeconds": 10,
            },
            "handOff": {"handOffSentence": self.hand_off_sentence, "emailTeam": True, "teamEmail": ""},
            "privacy": {
                "maskCardNumbers": True,
                "maskBankAccountNumbers": True,
                "maskEmailAddresses": True,
                "maskNames": True,
                "keepNumbersForCallbacks": True,
                "startInPrivacyMode": False,
                "transcriptRetentionDays": 30,
            },
            "phone": {"deskPhone": "", "mobilePhone": "", "storedNumberRetention": "whenResolved"},
        }

    def make_settings(self) -> AssistantSettings:
        return AssistantSettings.model_validate(self.make_settings_rows())
