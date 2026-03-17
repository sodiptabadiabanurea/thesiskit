"""Multi-agent debate and review system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum


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
    

class BaseAgent(ABC):
    """Base class for review agents."""
    
    def __init__(self, role: AgentRole, llm_client=None):
        self.role = role
        self.llm = llm_client
    
    @abstractmethod
    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        """Analyze content from this agent's perspective."""
        pass
    
    def _build_prompt(self, content: str, context: Optional[dict] = None) -> str:
        """Build prompt for this agent."""
        return f"""You are a {self.role.value} reviewer analyzing academic research.

Your role: {self._role_description()}

Content to analyze:
{content}

Context: {context or 'None'}

Provide your analysis in this format:
1. Main observations (what you see)
2. Key strengths (from your perspective)
3. Key concerns (from your perspective)
4. Specific suggestions for improvement

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
        prompt = self._build_prompt(content, context)
        # TODO: Call LLM
        return AgentPerspective(
            role=self.role,
            content="[Optimist analysis would be generated here]",
            key_points=["Innovation potential", "Novel contributions"],
            concerns=["May need more validation"],
            suggestions=["Consider additional experiments"],
        )


class SkepticAgent(BaseAgent):
    """Skeptical reviewer - questions claims and methodology."""
    
    def __init__(self, llm_client=None):
        super().__init__(AgentRole.SKEPTIC, llm_client)
    
    def _role_description(self) -> str:
        return "You question everything. You look for flaws in methodology, overclaiming, and missing evidence."
    
    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        prompt = self._build_prompt(content, context)
        # TODO: Call LLM
        return AgentPerspective(
            role=self.role,
            content="[Skeptic analysis would be generated here]",
            key_points=["Methodological concerns", "Evidence gaps"],
            concerns=["Potential overclaiming", "Missing controls"],
            suggestions=["Add more rigorous validation"],
        )


class MethodologistAgent(BaseAgent):
    """Methodology-focused reviewer - checks experimental design."""
    
    def __init__(self, llm_client=None):
        super().__init__(AgentRole.METHODOLOGIST, llm_client)
    
    def _role_description(self) -> str:
        return "You are a methodology expert. You check experimental design, statistical validity, and reproducibility."
    
    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        prompt = self._build_prompt(content, context)
        # TODO: Call LLM
        return AgentPerspective(
            role=self.role,
            content="[Methodologist analysis would be generated here]",
            key_points=["Experimental design", "Statistical approach"],
            concerns=["Reproducibility issues"],
            suggestions=["Add detailed methodology section"],
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
        for concern in set(all_concerns):
            lines.append(f"- {concern}")
        
        lines.append("\n## Suggested Improvements")
        for suggestion in set(all_suggestions):
            lines.append(f"- {suggestion}")
        
        return "\n".join(lines)
