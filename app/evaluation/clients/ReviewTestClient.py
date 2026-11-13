from pydantic import TypeAdapter

from app.backend.clients.BackendClient import BackendClient
from app.evaluation.models.EvaluationCase import EvaluationCase


class ReviewTestClient:
    case_list = TypeAdapter(list[EvaluationCase])

    def __init__(self, backend_client: BackendClient) -> None:
        self.backend_client = backend_client

    async def get_review_tests(self) -> list[EvaluationCase]:
        body = await self.backend_client.get("/internal/review-tests")
        return self.backend_client.parse(lambda: self.case_list.validate_python(body))
