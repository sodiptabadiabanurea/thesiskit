"""Pipeline stages for ThesisKit."""

from enum import IntEnum


class Stage(IntEnum):
    """20-stage research pipeline."""
    
    # Phase A: Scoping
    TOPIC_INIT = 1
    PROBLEM_DECOMPOSE = 2
    
    # Phase B: Literature
    SEARCH_STRATEGY = 3
    LITERATURE_COLLECT = 4
    LITERATURE_SCREEN = 5  # GATE
    KNOWLEDGE_EXTRACT = 6
    
    # Phase C: Synthesis
    SYNTHESIS = 7
    HYPOTHESIS_GEN = 8
    
    # Phase D: Design
    EXPERIMENT_DESIGN = 9  # GATE
    CODE_GENERATION = 10
    RESOURCE_PLANNING = 11
    
    # Phase E: Execution
    EXPERIMENT_RUN = 12
    ITERATIVE_REFINE = 13
    
    # Phase F: Analysis
    RESULT_ANALYSIS = 14
    RESEARCH_DECISION = 15  # PIVOT/REFINE
    
    # Phase G: Writing
    PAPER_OUTLINE = 16
    PAPER_DRAFT = 17
    PEER_REVIEW = 18
    PAPER_REVISION = 19
    
    # Phase H: Finalization
    QUALITY_GATE = 20  # GATE


# Stage sequence
STAGE_SEQUENCE = tuple(Stage)

# Gate stages (require approval)
GATE_STAGES = frozenset({
    Stage.LITERATURE_SCREEN,
    Stage.EXPERIMENT_DESIGN,
    Stage.QUALITY_GATE,
})

# Phase groupings
PHASE_MAP = {
    "A: Scoping": (Stage.TOPIC_INIT, Stage.PROBLEM_DECOMPOSE),
    "B: Literature": (Stage.SEARCH_STRATEGY, Stage.LITERATURE_COLLECT, 
                      Stage.LITERATURE_SCREEN, Stage.KNOWLEDGE_EXTRACT),
    "C: Synthesis": (Stage.SYNTHESIS, Stage.HYPOTHESIS_GEN),
    "D: Design": (Stage.EXPERIMENT_DESIGN, Stage.CODE_GENERATION, Stage.RESOURCE_PLANNING),
    "E: Execution": (Stage.EXPERIMENT_RUN, Stage.ITERATIVE_REFINE),
    "F: Analysis": (Stage.RESULT_ANALYSIS, Stage.RESEARCH_DECISION),
    "G: Writing": (Stage.PAPER_OUTLINE, Stage.PAPER_DRAFT, 
                   Stage.PEER_REVIEW, Stage.PAPER_REVISION),
    "H: Finalization": (Stage.QUALITY_GATE,),
}


def get_phase(stage: Stage) -> str:
    """Get phase name for a stage."""
    for phase, stages in PHASE_MAP.items():
        if stage in stages:
            return phase
    return "Unknown"


def is_gate(stage: Stage) -> bool:
    """Check if stage is a gate stage."""
    return stage in GATE_STAGES
