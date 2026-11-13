FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.12.17

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group voice

COPY app ./app
COPY prompts ./prompts
RUN uv run --no-sync python -m livekit.agents download-files

CMD ["uv", "run", "--no-sync", "python", "-m", "app.voice.VoiceWorker", "start"]
