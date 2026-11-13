import json

import pytest
from fastapi.testclient import TestClient

from app.ApplicationFactory import ApplicationFactory
from app.ServiceContainer import ServiceContainer
from tests.support.FakeHttpServer import FakeHttpServer
from tests.support.SampleData import SampleData
from tests.support.ScriptedAnswers import ScriptedAnswers
from tests.support.ScriptedCaseRehearsal import ScriptedCaseRehearsal
from tests.support.ScriptedStructuredModel import ScriptedStructuredModel

sample_data = SampleData()
secret_header = {"x-service-secret": "secret"}


@pytest.fixture
def analyzer() -> ScriptedStructuredModel:
    return ScriptedStructuredModel(ScriptedAnswers().all())


class ApplicationFactoryTest:
    def make_client(self, analyzer: ScriptedStructuredModel, backend: FakeHttpServer, rehearsal: ScriptedCaseRehearsal | None = None) -> TestClient:
        container = ServiceContainer(sample_data.make_configuration(), backend.make_client("http://backend.test"), analyzer, rehearsal or ScriptedCaseRehearsal())
        return TestClient(ApplicationFactory(container).make())

    def make_backend(self, faq_rows: list[dict] | None = None) -> FakeHttpServer:
        return FakeHttpServer(
            {
                ("GET", "/internal/faqs"): sample_data.make_faq_rows() if faq_rows is None else faq_rows,
                ("GET", "/internal/settings"): sample_data.make_settings_rows(),
            }
        )

    def test_health_needs_no_secret(self, analyzer: ScriptedStructuredModel) -> None:
        client = self.make_client(analyzer, self.make_backend())
        assert client.get("/health").json() == {"status": "ok"}

    def test_sync_needs_the_service_secret(self, analyzer: ScriptedStructuredModel) -> None:
        assert self.make_client(analyzer, self.make_backend()).post("/assistant/sync").status_code == 401

    def test_sync_returns_the_prompt_to_publish(self, analyzer: ScriptedStructuredModel) -> None:
        response = self.make_client(analyzer, self.make_backend()).post("/assistant/sync", headers=secret_header)
        assert response.status_code == 200
        assert len(response.json()["promptHash"]) == 64
        assert "1. How do I check my transfer's status?" in response.json()["promptContent"]

    def test_sync_refuses_without_active_faqs(self, analyzer: ScriptedStructuredModel) -> None:
        response = self.make_client(analyzer, self.make_backend(faq_rows=[])).post("/assistant/sync", headers=secret_header)
        assert response.status_code == 409

    def test_sync_reports_an_unreachable_backend(self, analyzer: ScriptedStructuredModel) -> None:
        assert self.make_client(analyzer, FakeHttpServer({})).post("/assistant/sync", headers=secret_header).status_code == 502

    def test_masks_one_line(self, analyzer: ScriptedStructuredModel) -> None:
        client = self.make_client(analyzer, self.make_backend())
        result = client.post("/masking/line", json={"text": "Email me at priya@example.com"}, headers=secret_header).json()
        assert result == {"redactedText": "Email me at [email address removed]", "removedKinds": ["email address"], "isChecked": True}

    def test_analyses_a_whole_call(self, analyzer: ScriptedStructuredModel) -> None:
        client = self.make_client(analyzer, self.make_backend())
        body = {"callId": "call-1", "lines": [{"position": 0, "speaker": "caller", "text": "This is Ananya"}], "faqs": [{"number": 2, "question": "When will my money arrive?"}]}
        result = client.post("/analysis", json=body, headers=secret_header).json()
        assert result["lines"][0]["redactedText"] == "This is [name removed]"
        assert result["matchedFaqNumber"] == 2
        assert result["isComplete"] is True

    def test_analysis_needs_the_service_secret(self, analyzer: ScriptedStructuredModel) -> None:
        assert self.make_client(analyzer, self.make_backend()).post("/analysis", json={"callId": "c", "lines": []}).status_code == 401

    def test_evaluations_rehearse_every_case_on_the_current_prompt(self, analyzer: ScriptedStructuredModel) -> None:
        rehearsal = ScriptedCaseRehearsal()
        report = self.make_client(analyzer, self.make_backend(), rehearsal).post("/evaluations/run", headers=secret_header).json()
        assert report["passedCount"] == 25
        assert report["failedCount"] == 0
        assert all("# Knowledge" in prompt for prompt in rehearsal.prompts)

    def test_evaluations_also_run_the_tests_from_reviews(self, analyzer: ScriptedStructuredModel) -> None:
        backend = self.make_backend()
        backend.responses[("GET", "/internal/review-tests")] = [
            {"id": "R01", "name": "From a review: fees", "turns": [{"role": "user", "content": "What are your fees to India?"}, {"role": "assistant", "check": "handsOff"}]}
        ]
        report = self.make_client(analyzer, backend).post("/evaluations/run", headers=secret_header).json()
        assert report["passedCount"] == 26
        assert any(result["caseId"] == "R01" for result in report["results"])

    def test_evaluations_need_active_faqs(self, analyzer: ScriptedStructuredModel) -> None:
        response = self.make_client(analyzer, self.make_backend(faq_rows=[])).post("/evaluations/run", headers=secret_header)
        assert response.status_code == 409

    def test_evaluations_stream_each_result_as_it_finishes(self, analyzer: ScriptedStructuredModel) -> None:
        response = self.make_client(analyzer, self.make_backend()).post("/evaluations/run/stream", headers=secret_header)
        events = [json.loads(line.removeprefix("data: ")) for line in response.text.splitlines() if line.startswith("data: ")]
        assert events[0] == {"type": "started", "total": 25}
        assert sum(event["type"] == "result" for event in events) == 25
        assert events[-1]["type"] == "finished" and events[-1]["report"]["passedCount"] == 25
