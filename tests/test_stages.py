"""Tests for pipeline stages."""

from thesiskit.pipeline.stages import Stage, get_phase, is_gate, GATE_STAGES


def test_stage_enum():
    """Test stage enum values."""
    assert Stage.TOPIC_INIT == 1
    assert Stage.PAPER_DRAFT == 17
    assert Stage.QUALITY_GATE == 20


def test_get_phase():
    """Test phase mapping."""
    assert get_phase(Stage.TOPIC_INIT) == "A: Scoping"
    assert get_phase(Stage.LITERATURE_COLLECT) == "B: Literature"
    assert get_phase(Stage.PAPER_DRAFT) == "G: Writing"
    assert get_phase(Stage.QUALITY_GATE) == "H: Finalization"


def test_is_gate():
    """Test gate stage detection."""
    assert is_gate(Stage.LITERATURE_SCREEN) is True
    assert is_gate(Stage.EXPERIMENT_DESIGN) is True
    assert is_gate(Stage.QUALITY_GATE) is True
    assert is_gate(Stage.TOPIC_INIT) is False
    assert is_gate(Stage.PAPER_DRAFT) is False


def test_gate_stages():
    """Test gate stages set."""
    assert len(GATE_STAGES) == 3
    assert Stage.LITERATURE_SCREEN in GATE_STAGES
    assert Stage.EXPERIMENT_DESIGN in GATE_STAGES
    assert Stage.QUALITY_GATE in GATE_STAGES
