from app.backend.clients.BackendClient import BackendClient
from app.backend.exceptions.BackendRequestError import BackendRequestError
from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog


class HandOffService:
    def __init__(self, reason_catalog: HandOffReasonCatalog, backend_client: BackendClient) -> None:
        self.reason_catalog = reason_catalog
        self.backend_client = backend_client

    async def ring_team(self, call_id: str, reason: str, caller_need: str) -> bool:
        try:
            return await self.backend_client.ring_team(call_id, self.reason_catalog.describe(reason), caller_need)
        except BackendRequestError:
            return False
