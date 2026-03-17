"""Pipeline runner for ThesisKit."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console

from thesiskit.config import Config
from thesiskit.pipeline.stages import Stage, get_phase, is_gate

console = Console()


def _utcnow_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _generate_run_id() -> str:
    """Generate unique run ID."""
    now = datetime.now()
    return f"tk-{now.strftime('%Y%m%d-%H%M%S')}"


def run_pipeline(
    config: Config,
    topic: Optional[str] = None,
    auto_approve: bool = False,
    output_dir: Optional[Path] = None,
) -> dict:
    """Run the full ThesisKit pipeline.
    
    Args:
        config: Configuration object
        topic: Research topic (overrides config)
        auto_approve: Auto-approve gate stages
        output_dir: Output directory for artifacts
        
    Returns:
        Pipeline summary dict
    """
    # Setup
    if topic:
        config.research.topic = topic
    
    if not config.research.topic:
        raise ValueError("Research topic is required")
    
    run_id = _generate_run_id()
    output_dir = output_dir or Path("artifacts") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n[bold blue]ThesisKit Pipeline[/bold blue]")
    console.print(f"Run ID: {run_id}")
    console.print(f"Topic: {config.research.topic}")
    console.print(f"Output: {output_dir}")
    console.print(f"Auto-approve: {auto_approve}\n")
    
    results = {
        "run_id": run_id,
        "topic": config.research.topic,
        "stages": [],
        "started_at": _utcnow_iso(),
    }
    
    # Run stages
    for stage in Stage:
        phase = get_phase(stage)
        gate = is_gate(stage)
        
        console.print(f"[dim]{phase}[/dim] → Stage {stage.value:2d}: {stage.name}")
        
        # TODO: Implement actual stage execution
        # For now, just log the stage
        
        stage_result = {
            "stage": stage.value,
            "name": stage.name,
            "phase": phase,
            "is_gate": gate,
            "status": "pending",
        }
        
        results["stages"].append(stage_result)
    
    # Finalize
    results["completed_at"] = _utcnow_iso()
    results["final_status"] = "completed"
    
    # Write summary
    summary_path = output_dir / "pipeline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    
    console.print(f"\n[bold green]Pipeline complete![/bold green]")
    console.print(f"Summary: {summary_path}")
    
    return results
