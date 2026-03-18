"""Hypothesis generation through multi-agent debate."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from thesiskit.agents.review import (
    BaseAgent,
    AgentRole,
    AgentPerspective,
)


@dataclass
class Hypothesis:
    """A research hypothesis."""
    claim: str
    rationale: str
    prediction: str
    failure_condition: str
    resource_estimate: str
    source_perspectives: list[AgentRole]


class HypothesisDebate:
    """Generate hypotheses through multi-agent debate."""
    
    def __init__(self, llm_client=None):
        self.agents = [
            InnovatorAgent(llm_client),
            PragmatistAgent(llm_client),
            ContrarianAgent(llm_client),
        ]
    
    def generate(
        self,
        topic: str,
        literature_summary: str,
        knowledge_gaps: list[str],
    ) -> list[Hypothesis]:
        """Generate hypotheses through debate.
        
        Args:
            topic: Research topic
            literature_summary: Summary of existing literature
            knowledge_gaps: Identified gaps in knowledge
            
        Returns:
            List of synthesized hypotheses
        """
        # Each agent proposes hypotheses
        perspectives = []
        for agent in self.agents:
            perspective = agent.analyze(
                f"Topic: {topic}\n\nLiterature: {literature_summary}\n\nGaps: {knowledge_gaps}"
            )
            perspectives.append(perspective)
        
        # Synthesize into hypotheses
        hypotheses = self._synthesize_hypotheses(perspectives)
        
        return hypotheses
    
    def _synthesize_hypotheses(
        self,
        perspectives: list[AgentPerspective],
    ) -> list[Hypothesis]:
        """Synthesize agent perspectives into hypotheses."""
        hypotheses = []
        
        # TODO: Use LLM to synthesize perspectives into hypotheses
        # For now, return placeholder
        hypothesis = Hypothesis(
            claim="Synthesized claim from debate",
            rationale="Rationale combining all perspectives",
            prediction="Measurable prediction",
            failure_condition="Condition that would disprove",
            resource_estimate="Time and compute needed",
            source_perspectives=[p.role for p in perspectives],
        )
        hypotheses.append(hypothesis)
        
        return hypotheses


class InnovatorAgent(BaseAgent):
    """Innovator - proposes novel approaches."""
    
    def __init__(self, llm_client=None):
        super().__init__(AgentRole.INNOVATOR, llm_client)
    
    def _role_description(self) -> str:
        return "You look for novel, unconventional approaches. You challenge assumptions and propose new methods."
    
    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        return AgentPerspective(
            role=self.role,
            content="[Innovator perspective]",
            key_points=["Novel approach potential"],
            concerns=["May be risky"],
            suggestions=["Try unconventional methods"],
        )


class PragmatistAgent(BaseAgent):
    """Pragmatist - focuses on feasibility."""
    
    def __init__(self, llm_client=None):
        super().__init__(AgentRole.PRAGMATIST, llm_client)
    
    def _role_description(self) -> str:
        return "You focus on what's practical and achievable. You consider resource constraints and proven methods."
    
    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        return AgentPerspective(
            role=self.role,
            content="[Pragmatist perspective]",
            key_points=["Feasibility", "Resource efficiency"],
            concerns=["Complexity may be too high"],
            suggestions=["Use proven methods first"],
        )


class ContrarianAgent(BaseAgent):
    """Contrarian - challenges problem framing."""
    
    def __init__(self, llm_client=None):
        super().__init__(AgentRole.CONTRARIAN, llm_client)
    
    def _role_description(self) -> str:
        return "You challenge the problem framing itself. You ask if this is the right problem to solve."
    
    def analyze(self, content: str, context: Optional[dict] = None) -> AgentPerspective:
        return AgentPerspective(
            role=self.role,
            content="[Contrarian perspective]",
            key_points=["Alternative framings"],
            concerns=["May be solving wrong problem"],
            suggestions=["Consider alternative approaches"],
        )
