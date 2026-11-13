import hashlib

from app.assistant.exceptions.NoActiveFaqsError import NoActiveFaqsError
from app.assistant.models.AssistantDraft import AssistantDraft
from app.assistant.models.AssistantSyncResponse import AssistantSyncResponse
from app.assistant.services.PromptBuilder import PromptBuilder
from app.backend.clients.BackendClient import BackendClient
from app.backend.exceptions.BackendRequestError import BackendRequestError


class AssistantSyncService:
    def __init__(self, backend_client: BackendClient, prompt_builder: PromptBuilder) -> None:
        self.backend_client = backend_client
        self.prompt_builder = prompt_builder

    async def sync(self) -> AssistantSyncResponse:
        draft = await self.make_draft()
        return AssistantSyncResponse(prompt_hash=draft.prompt_hash, prompt_content=draft.prompt_content)

    async def make_draft(self, extra_rules: list[str] | None = None) -> AssistantDraft:
        faqs = await self.backend_client.get_active_faqs()
        if not faqs:
            raise NoActiveFaqsError("There are no active FAQs to build the agent from")
        settings = await self.backend_client.get_assistant_settings()
        learned_rules = await self.load_learned_rules() + (extra_rules or [])
        prompt_content = self.prompt_builder.build(faqs, settings, learned_rules)
        prompt_hash = hashlib.sha256(prompt_content.encode()).hexdigest()
        return AssistantDraft(faqs=faqs, settings=settings, prompt_content=prompt_content, prompt_hash=prompt_hash)

    async def load_learned_rules(self) -> list[str]:
        try:
            return await self.backend_client.get_learned_rules()
        except BackendRequestError:
            return []
