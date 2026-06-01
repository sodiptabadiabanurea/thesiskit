"""Tests for LLM-backed review agents."""

from thesiskit.agents.review import AgentRole, MultiAgentReview, OptimistAgent


class FakeLLM:
    """Deterministic fake LLM that records structured-generation calls."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_json(self, prompt, system=None):
        self.calls.append({"prompt": prompt, "system": system})
        if not self.responses:
            raise AssertionError("No fake LLM response left")
        return self.responses.pop(0)


def test_agent_uses_llm_json_response_for_perspective():
    """Agents with an LLM client should use structured LLM output, not placeholders."""
    fake_llm = FakeLLM(
        [
            {
                "content": "The paper has a clear deployment path.",
                "key_points": ["strong motivation", "useful artifact"],
                "concerns": ["evaluation is still narrow"],
                "suggestions": ["add a cross-domain ablation"],
            }
        ]
    )

    perspective = OptimistAgent(fake_llm).analyze(
        "Draft about retrieval augmented generation.",
        context={"venue": "ACL"},
    )

    assert perspective.role == AgentRole.OPTIMIST
    assert perspective.content == "The paper has a clear deployment path."
    assert perspective.key_points == ["strong motivation", "useful artifact"]
    assert perspective.concerns == ["evaluation is still narrow"]
    assert perspective.suggestions == ["add a cross-domain ablation"]
    assert len(fake_llm.calls) == 1
    assert "optimist reviewer" in fake_llm.calls[0]["prompt"]
    assert "Draft about retrieval augmented generation." in fake_llm.calls[0]["prompt"]
    assert "venue" in fake_llm.calls[0]["prompt"]


def test_agent_normalizes_llm_response_fields():
    """Structured responses should tolerate strings, missing fields, and unknown extra keys."""
    fake_llm = FakeLLM(
        [
            {
                "content": "Good idea, but needs tighter evidence.",
                "key_points": "2024 baseline result",
                "concerns": None,
                "suggestions": ["tighten claims"],
                "ignored_extra": "ok",
            }
        ]
    )

    perspective = OptimistAgent(fake_llm).analyze("Short draft")

    assert perspective.key_points == ["2024 baseline result"]
    assert perspective.concerns == []
    assert perspective.suggestions == ["tighten claims"]


def test_multi_agent_review_uses_llm_for_each_agent_and_summarizes_deterministically():
    """Review orchestration should call the LLM once per agent and keep summary order stable."""
    fake_llm = FakeLLM(
        [
            {
                "content": "Optimist view",
                "key_points": ["novelty"],
                "concerns": ["needs validation"],
                "suggestions": ["add ablation"],
            },
            {
                "content": "Skeptic view",
                "key_points": ["scope"],
                "concerns": ["needs validation", "overclaiming"],
                "suggestions": ["add ablation", "temper claims"],
            },
            {
                "content": "Methodologist view",
                "key_points": ["reproducibility"],
                "concerns": ["missing seeds"],
                "suggestions": ["publish config"],
            },
        ]
    )

    review = MultiAgentReview(llm_client=fake_llm).review("Full paper draft")

    assert [p.role for p in review["perspectives"]] == [
        AgentRole.OPTIMIST,
        AgentRole.SKEPTIC,
        AgentRole.METHODOLOGIST,
    ]
    assert [p.content for p in review["perspectives"]] == [
        "Optimist view",
        "Skeptic view",
        "Methodologist view",
    ]
    assert len(fake_llm.calls) == 3
    assert review["summary"].splitlines() == [
        "# Multi-Agent Review Summary",
        "",
        "## Key Concerns Across Agents",
        "- needs validation",
        "- overclaiming",
        "- missing seeds",
        "",
        "## Suggested Improvements",
        "- add ablation",
        "- temper claims",
        "- publish config",
    ]
