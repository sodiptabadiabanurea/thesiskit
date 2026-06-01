"""Multi-agent debate and review system."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class AgentRole(str, Enum):
    """Roles for multi-agent debate."""

    OPTIMIST = "optimist"
    SKEPTIC = "skeptic"
    METHODOLOGIST = "methodologist"
    INNOVATOR = "innovator"
    PRAGMATIST = "pragmatist"
    CONTRARIAN = "contrarian"


@dataclass
class AgentPerspective:
    """A perspective from one agent."""

    role: AgentRole
    content: str
    key_points: list[str]
    concerns: list[str]
    suggestions: list[str]


def _coerce_string_list(value: Any) -> list[str]:
    """Normalize LLM JSON values into a clean string list."""
    if value is None:
        return []
    if isinstance(value, str):
        candidates = value.splitlines() or [value]
    elif isinstance(value, (list, tuple, set)):
        candidates = value
    else:
        candidates = [value]

    normalized = []
    for item in candidates:
        text = str(item).strip()
        text = re.sub(r"^(?:[-•*]|\d+[.)])\s*", "", text).strip()
        if text:
            normalized.append(text)
    return normalized


def _coerce_content(value: Any, fallback: str) -> str:
    """Normalize an LLM content field."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _unique_preserve_order(items: list[str]) -> list[str]:
    """Return unique non-empty strings while preserving first-seen order."""
    seen = set()
    unique = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


class BaseAgent(ABC):
    """Base class for review agents."""

    def __init__(self, role: AgentRole, llm_client=None):
        self.role = role
        self.llm = llm_client

    @abstractmethod
    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        """Analyze content from this agent's perspective."""
        pass

    def _analyze_with_optional_llm(
        self,
        content: str,
        context: Optional[dict],
        fallback: AgentPerspective,
    ) -> AgentPerspective:
        """Return an LLM-backed perspective, or the deterministic fallback without an LLM."""
        if self.llm is None:
            return fallback

        response = self.llm.generate_json(
            prompt=self._build_prompt(content, context),
            system=(
                "Return only JSON with string field 'content' and array fields "
                "'key_points', 'concerns', and 'suggestions'."
            ),
        )
        if not isinstance(response, dict):
            raise ValueError("LLM review response must be a JSON object")

        return AgentPerspective(
            role=self.role,
            content=_coerce_content(response.get("content"), fallback.content),
            key_points=_coerce_string_list(response.get("key_points")),
            concerns=_coerce_string_list(response.get("concerns")),
            suggestions=_coerce_string_list(response.get("suggestions")),
        )

    def _build_prompt(self, content: str, context: Optional[dict] = None) -> str:
        """Build prompt for this agent."""
        return f"""You are a {self.role.value} reviewer analyzing academic research.

Your role: {self._role_description()}

Content to analyze:
{content}

Context: {context or 'None'}

Return only a JSON object with these keys:
- content: concise narrative analysis string
- key_points: array of key strength/observation strings
- concerns: array of concern strings
- suggestions: array of specific improvement strings

Be thorough but concise. Focus on what a {self.role.value} would care about.
"""

    @abstractmethod
    def _role_description(self) -> str:
        """Return description of this role."""
        pass


class OptimistAgent(BaseAgent):
    """Optimistic reviewer - focuses on potential and positive aspects."""

    def __init__(self, llm_client=None):
        super().__init__(AgentRole.OPTIMIST, llm_client)

    def _role_description(self) -> str:
        return "You see the best in research. You look for innovation, potential impact, and novel contributions."

    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        return self._analyze_with_optional_llm(
            content,
            context,
            fallback=AgentPerspective(
                role=self.role,
                content="[Optimist analysis would be generated here]",
                key_points=["Innovation potential", "Novel contributions"],
                concerns=["May need more validation"],
                suggestions=["Consider additional experiments"],
            ),
        )


class SkepticAgent(BaseAgent):
    """Skeptical reviewer - questions claims and methodology."""

    def __init__(self, llm_client=None):
        super().__init__(AgentRole.SKEPTIC, llm_client)

    def _role_description(self) -> str:
        return "You question everything. You look for flaws in methodology, overclaiming, and missing evidence."

    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        return self._analyze_with_optional_llm(
            content,
            context,
            fallback=AgentPerspective(
                role=self.role,
                content="[Skeptic analysis would be generated here]",
                key_points=["Methodological concerns", "Evidence gaps"],
                concerns=["Potential overclaiming", "Missing controls"],
                suggestions=["Add more rigorous validation"],
            ),
        )


class MethodologistAgent(BaseAgent):
    """Methodology-focused reviewer - checks experimental design."""

    def __init__(self, llm_client=None):
        super().__init__(AgentRole.METHODOLOGIST, llm_client)

    def _role_description(self) -> str:
        return "You are a methodology expert. You check experimental design, statistical validity, and reproducibility."

    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        return self._analyze_with_optional_llm(
            content,
            context,
            fallback=AgentPerspective(
                role=self.role,
                content="[Methodologist analysis would be generated here]",
                key_points=["Experimental design", "Statistical approach"],
                concerns=["Reproducibility issues"],
                suggestions=["Add detailed methodology section"],
            ),
        )


class MultiAgentReview:
    """Coordinate multiple agents for comprehensive review."""

    def __init__(self, agents: Optional[list[BaseAgent]] = None, llm_client=None):
        if agents is None:
            agents = [
                OptimistAgent(llm_client),
                SkepticAgent(llm_client),
                MethodologistAgent(llm_client),
            ]
        self.agents = agents

    def review(self, content: str, context: Optional[dict] = None) -> dict:
        """Run multi-agent review on content.

        Returns:
            Dict with perspectives from each agent and synthesized summary
        """
        perspectives = []

        for agent in self.agents:
            perspective = agent.analyze(content, context)
            perspectives.append(perspective)

        # Synthesize
        summary = self._synthesize(perspectives)

        return {
            "perspectives": perspectives,
            "summary": summary,
        }

    def _synthesize(self, perspectives: list[AgentPerspective]) -> str:
        """Synthesize multiple perspectives into a summary."""
        lines = ["# Multi-Agent Review Summary\n"]

        # Collect all concerns
        all_concerns = []
        for p in perspectives:
            all_concerns.extend(p.concerns)

        # Collect all suggestions
        all_suggestions = []
        for p in perspectives:
            all_suggestions.extend(p.suggestions)

        lines.append("## Key Concerns Across Agents")
        for concern in _unique_preserve_order(all_concerns):
            lines.append(f"- {concern}")

        lines.append("\n## Suggested Improvements")
        for suggestion in _unique_preserve_order(all_suggestions):
            lines.append(f"- {suggestion}")

        return "\n".join(lines)
