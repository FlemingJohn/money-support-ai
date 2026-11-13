# money-support-ai

Python code for everything the agent says and thinks. It holds two programs that share one codebase:

- **The voice worker** (`app/voice/`) runs every live call on LiveKit. It hears the caller, answers from the FAQs, hands off to a person, and reports the call to the backend when it ends.
- **The API** (`app/main.py`) builds the prompt from the FAQs and settings, analyses every finished call with a LangGraph graph on Azure OpenAI (masking personal data, summary, topic, matched FAQ, fields and checks), masks live test-call lines, tests the agent, and suggests new rules from reviews.

Neither program touches the database. Both read and write through the backend.

## How it is built

- Classes only. Routers handle HTTP, services hold the steps, factories and catalogs build pieces, clients talk to the backend.
- Every class is alone in a file named after it.
- `ServiceContainer` wires the API and `VoiceContainer` wires the worker. The API never imports the audio packages, so it stays small enough for Vercel.
- `VoiceAgentFactory` builds the agent from the prompt and two tools. The worker gives it live call actions; tests give it rehearsal actions that do nothing.
- Prompts are Markdown files in `prompts/`, filled in with Jinja.

## A live call

1. LiveKit sends the call to the worker named `money-support`. The room name is the call id.
2. `CallHandler` reads the published prompt and settings from `GET /internal/agent/published`, starts the session and reports `POST /internal/calls/started`.
3. `SessionFactory` builds the session on LiveKit Inference: Deepgram nova-3 with Wise key terms, `openai/gpt-4o` at temperature 0, an Inworld voice from `VoiceCatalog`, the English turn detector, and noise cancellation (telephone-tuned for phone calls).
4. The agent greets the caller and answers from the FAQs. Before the model reads each caller turn, `PromptInjectionGuard` replaces any attempt to change, ignore or read out the instructions with a short note, so the model treats it as out of scope and hands off. Rehearsals clean the caller line the same way.
5. `handOffToHuman` says why, runs the `HandOffGraph` (describe_reason, then ring_team), says the hand-off sentence and ends the call.
6. `endCall` ends the call only after the agent asked if there is anything else and the caller said goodbye (`GoodbyeChecker`).
7. `SilenceWatcher` asks "Are you still there?" twice, then ends the call. `CallTimer` ends it at the time limit.
8. When the session closes, `CallReportBuilder` turns the conversation into a report and sends `POST /internal/calls/finished`, with one of `callerHungUp`, `agentEndedCall`, `handedOff`, `silenceTimeout`, `timeLimit` or `error`.

## Endpoints

| Method | Path | Used by | What it does |
|---|---|---|---|
| GET | `/health` | backend Connections tab | Says the service is up |
| POST | `/assistant/sync` | backend, after FAQ or settings changes | Builds the prompt and returns it with its hash, for the backend to publish |
| POST | `/analysis` | backend, when a call ends | Runs the call analysis graph and returns masked lines, summary, topic, matched FAQ, fields, checks and a suggested review |
| POST | `/masking/line` | backend, for the Test call page | Masks one caller line |
| POST | `/evaluations/run` | backend, on demand | Rehearses every test case and returns the results |
| POST | `/evaluations/run/stream` | backend, on demand | The same, streaming each result as it finishes |
| POST | `/improvements/suggest/stream` | backend, on demand | Proposes a rule from wrong replies and tests it on a copy of the agent |

Everything except `/health` needs the `x-service-secret` header, with the same value as the backend's `SERVICE_SECRET`.

## Call analysis

There are no patterns or regular expressions. Azure OpenAI gpt-4o reads each line in context and returns the exact personal pieces with their kind; code checks each piece is really in the line and replaces it, so the model never rewrites what the caller said.

```
START ─▶ fan out lines ══Send × each line══▶ mask_line ─▶ join_lines
join_lines ─┬─▶ summarise ──────┐
            ├─▶ classify_topic ─┼─▶ check_call ─▶ END
            └─▶ extract_fields ─┘
```

| Node | Does | Output schema |
|---|---|---|
| `mask_line` | Finds names, card and account numbers (even a few spoken digits), emails, phone numbers and addresses in one line | `MaskingOutput { pieces: [{ text, kind }] }` |
| `summarise` | Two or three sentences from the masked transcript | `SummaryOutput { summary }` |
| `classify_topic` | Topic and the FAQ the agent answered from, `0` for none | `TopicOutput { topic, matched_faq_number }` |
| `extract_fields` | Amount, currency, date, country, status, each with a confidence and its line | `FieldsOutput { fields }` |
| `check_call` | Whether a hand-off was expected, whether the agent repeated personal data, and whether it made a mistake | `CheckOutput` |

Every model call uses a strict JSON schema and retries three times. A step that still fails is listed in `failedSteps`; a line that could not be checked is returned as "[waiting for privacy check]" and never in its raw form.

## Tests of the agent

| Kind | Where | How it runs |
|---|---|---|
| Rehearsals | `evaluation/cases/E01…E25` and the tests made from reviews | `CaseRehearsal` runs the real agent as text in a LiveKit session. Answers are judged by `openai/gpt-4.1` against the expectation, hand-offs by the `handOffToHuman` call and its reason, goodbyes by the `endCall` call. |
| DeepEval | `evaluation/masking/cases.json` (52 lines), `evaluation/analysis/calls.json` (4 calls) | `tests/live/`: masking checked line by line, and whole calls checked for matched FAQ, hand-off, review reason and fields, plus a GEval judge for summary quality. Run with `uv run pytest -m live`. |

Rehearsals use LiveKit Inference and DeepEval uses Azure OpenAI, so they only run when asked. `uv run pytest` runs only the fast tests, which use scripted models.

## Structure

```
money-support-ai/
├── app/
│   ├── main.py · ApplicationFactory.py · ServiceContainer.py
│   ├── configuration/  AppConfiguration
│   ├── common/         CamelModel, ServiceSecretGuard, TemplateRenderer, errors
│   ├── backend/        BackendClient and the models the backend sends and receives
│   ├── assistant/      prompt and sync
│   ├── voice/          the worker: agent, tools, session, call actions, report
│   ├── handoff/        LangGraph hand-off graph
│   ├── analysis/       LangGraph call analysis graph, its nodes, schemas and Azure client
│   ├── evaluation/     rehearsals of the case files
│   ├── improvement/    LangGraph rule suggestion graph
│   └── health/
├── prompts/            assistant · analysis · evaluation · improvement
├── evaluation/cases/   one JSON file per test case
├── Dockerfile          the voice worker image
└── tests/              mirrors app/
```

## Local setup

Needs Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group voice
cp .env.example .env
uv run uvicorn app.main:app --port 8000
uv run python -m app.voice.VoiceWorker dev
```

| Variable | Value |
|---|---|
| `SERVICE_SECRET` | Same as the backend |
| `BACKEND_URL` | `http://localhost:4000` |
| `LIVEKIT_URL` | The LiveKit project URL, needed by the worker |
| `LIVEKIT_API_KEY` | LiveKit project key, for the worker and for rehearsals |
| `LIVEKIT_API_SECRET` | LiveKit project secret |
| `ASSISTANT_MODEL` | `openai/gpt-4o` |
| `JUDGE_MODEL` | Model for the rehearsal judge, `openai/gpt-4.1` by default |
| `AZURE_OPENAI_*` | The Azure deployment used by call analysis and masking |

Then set `AI_SERVICE_URL=http://localhost:8000` in the backend so it uses this service.

| Command | What it does |
|---|---|
| `uv run pytest` | Runs the fast tests |
| `uv run uvicorn app.main:app --reload --port 8000` | Starts the API and restarts on changes |
| `uv run python -m app.voice.VoiceWorker dev` | Starts the voice worker against your LiveKit project |
| `lk agent create` / `lk agent deploy` | Builds the `Dockerfile` and deploys the worker to LiveKit Cloud |
