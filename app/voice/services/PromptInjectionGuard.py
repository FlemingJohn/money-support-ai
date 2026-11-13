import re


class PromptInjectionGuard:
    replacement = "[The caller asked the agent to change, ignore or reveal its instructions.]"
    injection = re.compile(
        "|".join(
            [
                r"\b(ignore|forget|disregard|override|bypass)\b.{0,30}\b(instructions?|rules|prompt|guidelines)\b",
                r"\b(reveal|show|print|repeat|tell me|read me|read out|what are)\b.{0,20}\byour\b.{0,20}\b(instructions?|prompt|rules|guidelines)\b",
                r"\b(system|developer)\s+(prompt|message|mode)\b",
                r"\byou are (now|no longer)\b",
                r"\b(act|behave|roleplay|role-play)\s+(as|like)\b",
                r"\bpretend\s+(to be|you['’]?re|you are)\b",
                r"\bjailbreak\b",
                r"\bnew (instructions?|rules)\b",
            ]
        ),
        re.IGNORECASE,
    )

    def clean(self, caller_text: str) -> str:
        return self.replacement if self.is_injection(caller_text) else caller_text

    def is_injection(self, caller_text: str) -> bool:
        return self.injection.search(caller_text) is not None
