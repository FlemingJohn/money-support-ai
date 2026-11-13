from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantDraft:
    prompt_content: str
    prompt_hash: str
