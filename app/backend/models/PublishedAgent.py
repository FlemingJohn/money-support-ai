from app.backend.models.AssistantSettings import AssistantSettings
from app.common.models.CamelModel import CamelModel


class PublishedAgent(CamelModel):
    prompt_content: str
    settings: AssistantSettings
