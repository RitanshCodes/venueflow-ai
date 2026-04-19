from __future__ import annotations

from dataclasses import dataclass

from app.core.models import AgentRole
from app.providers.base import LLMProvider


@dataclass
class AgentResult:
    output: str
    prompt: str


class BaseAgent:
    role: AgentRole
    system_prompt: str

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def run(self, prompt: str) -> AgentResult:
        output = self.provider.generate(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
        )
        return AgentResult(output=output, prompt=prompt)

