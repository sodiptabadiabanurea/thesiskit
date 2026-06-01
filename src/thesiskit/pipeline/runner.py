"""Deterministic pipeline runner for ThesisKit."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from thesiskit.config import Config
from thesiskit.pipeline.stages import STAGE_SEQUENCE, Stage, get_phase, is_gate

console = Console()


def _utcnow_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _generate_run_id() -> str:
    """Generate unique run ID."""
    now = datetime.now()
    return f"tk-{now.strftime('%Y%m%d-%H%M%S')}"


def _slug(value: str) -> str:
    """Return a stable filesystem-friendly slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "stage"


def _topic_terms(topic: str, limit: int = 5) -> list[str]:
    """Extract deterministic keyword terms from a topic."""
    stop_words = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}
    terms: list[str] = []
    for term in re.findall(r"[A-Za-z0-9]+", topic.lower()):
        if term in stop_words or term in terms:
            continue
        terms.append(term)
        if len(terms) == limit:
            break
    return terms or ["research"]


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """Write deterministic UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _stage_artifact_path(output_dir: Path, stage: Stage) -> Path:
    """Return the artifact path for a stage."""
    return output_dir / f"stage_{stage.value:02d}_{_slug(stage.name)}.json"


def _run_deterministic_stage(stage: Stage, state: dict[str, Any]) -> dict[str, Any]:
    """Run one deterministic, local-only pipeline stage."""
    topic = state["topic"]
    terms = _topic_terms(topic)

    if stage == Stage.TOPIC_INIT:
        return {"topic": topic, "terms": terms}

    if stage == Stage.PROBLEM_DECOMPOSE:
        questions = [f"How does {topic} affect {term}?" for term in terms[:3]]
        state["questions"] = questions
        return {"questions": questions}

    if stage == Stage.SEARCH_STRATEGY:
        search_terms = terms[:3]
        strategy = {
            "sources": ["arXiv", "Semantic Scholar", "manual BibTeX"],
            "queries": [" ".join(search_terms), topic],
        }
        state["search_strategy"] = strategy
        return strategy

    if stage == Stage.LITERATURE_COLLECT:
        papers = [
            {
                "title": f"{topic.title()} — seed paper {index}",
                "source": "deterministic-runner",
                "year": 2020 + index,
            }
            for index in range(1, 4)
        ]
        state["literature"] = papers
        return {"papers_collected": len(papers), "papers": papers}

    if stage == Stage.LITERATURE_SCREEN:
        retained = [paper for paper in state.get("literature", []) if paper.get("title")]
        state["literature"] = retained
        return {"papers_retained": len(retained)}

    if stage == Stage.KNOWLEDGE_EXTRACT:
        claims = [f"Extracted claim from {paper['title']}" for paper in state.get("literature", [])]
        state["knowledge_claims"] = claims
        return {"claims_extracted": len(claims), "claims": claims}

    if stage == Stage.SYNTHESIS:
        synthesis = f"Synthesis for {topic} from {len(state.get('knowledge_claims', []))} claims."
        state["synthesis"] = synthesis
        return {"synthesis": synthesis}

    if stage == Stage.HYPOTHESIS_GEN:
        hypotheses = [
            f"H{index}: {term} improves the research outcome"
            for index, term in enumerate(terms[:3], start=1)
        ]
        state["hypotheses"] = hypotheses
        return {"hypotheses": hypotheses}

    if stage == Stage.EXPERIMENT_DESIGN:
        spec = {
            "mode": "simulated",
            "metric": state.get("metric_key", "primary_metric"),
            "hypotheses": state.get("hypotheses", []),
        }
        state["experiment_spec"] = spec
        return {"experiment_spec": spec}

    if stage == Stage.CODE_GENERATION:
        metric_key = state.get("metric_key", "primary_metric")
        code = f"metric_value = 1.0\nprint({{{metric_key!r}: metric_value}})\n"
        state["experiment_code"] = code
        return {"language": "python", "metric_key": metric_key, "code": code}

    if stage == Stage.RESOURCE_PLANNING:
        resources = {"runner": "local", "mode": "deterministic", "network": "disabled"}
        state["resources"] = resources
        return {"resources": resources}

    if stage == Stage.EXPERIMENT_RUN:
        metric_key = state.get("metric_key", "primary_metric")
        results = {metric_key: 1.0, "status": "simulated"}
        state["results"] = results
        return {"results": results}

    if stage == Stage.ITERATIVE_REFINE:
        refinement = {"iterations": 1, "decision": "keep-baseline"}
        state["refinement"] = refinement
        return refinement

    if stage == Stage.RESULT_ANALYSIS:
        analysis = {
            "summary": "Deterministic simulated result completed.",
            "metric": state.get("results", {}).get(state.get("metric_key", "primary_metric")),
        }
        state["analysis"] = analysis
        return {"analysis": analysis}

    if stage == Stage.RESEARCH_DECISION:
        decision = "proceed" if state.get("analysis") else "refine"
        state["decision"] = decision
        return {"decision": decision}

    if stage == Stage.PAPER_OUTLINE:
        outline = ["Introduction", "Related Work", "Method", "Results", "Conclusion"]
        state["outline"] = outline
        return {"outline": outline}

    if stage == Stage.PAPER_DRAFT:
        draft = {
            "title": topic.title(),
            "sections": state.get("outline", []),
            "status": "drafted",
        }
        state["paper_draft"] = draft
        return {"paper_draft": draft}

    if stage == Stage.PEER_REVIEW:
        review = {"reviewers": ["method", "writing", "reproducibility"], "blocking_issues": 0}
        state["review"] = review
        return {"review": review}

    if stage == Stage.PAPER_REVISION:
        revision = {"changes_applied": len(state.get("review", {}).get("reviewers", []))}
        state["revision"] = revision
        return revision

    if stage == Stage.QUALITY_GATE:
        quality = {"passed": True, "checks": ["artifacts", "summary", "review"]}
        state["quality"] = quality
        return {"quality": quality}

    raise ValueError(f"Unsupported stage: {stage}")


def run_pipeline(
    config: Config,
    topic: Optional[str] = None,
    auto_approve: bool = False,
    output_dir: Optional[Path] = None,
) -> dict:
    """Run the deterministic ThesisKit stage pipeline.

    This runner is intentionally local-only and deterministic: it records the
    canonical 20-stage research workflow, writes one JSON artifact per stage,
    and stops at human approval gates unless ``auto_approve`` is enabled.
    """
    if topic:
        config.research.topic = topic

    if not config.research.topic:
        raise ValueError("Research topic is required")

    run_id = _generate_run_id()
    output_dir = output_dir or Path("artifacts") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print("\n[bold blue]ThesisKit Pipeline[/bold blue]")
    console.print(f"Run ID: {run_id}")
    console.print(f"Topic: {config.research.topic}")
    console.print(f"Output: {output_dir}")
    console.print(f"Auto-approve: {auto_approve}\n")

    state: dict[str, Any] = {
        "topic": config.research.topic,
        "metric_key": config.experiment.metric_key,
    }
    results: dict[str, Any] = {
        "run_id": run_id,
        "topic": config.research.topic,
        "stages": [],
        "started_at": _utcnow_iso(),
    }
    final_status = "completed"

    for stage in STAGE_SEQUENCE:
        phase = get_phase(stage)
        gate = is_gate(stage)
        console.print(f"[dim]{phase}[/dim] → Stage {stage.value:2d}: {stage.name}")

        artifact_path = _stage_artifact_path(output_dir, stage)
        stage_result: dict[str, Any] = {
            "stage": stage.value,
            "name": stage.name,
            "phase": phase,
            "is_gate": gate,
            "requires_approval": gate,
            "approved": True if gate and auto_approve else False if gate else None,
            "started_at": _utcnow_iso(),
            "artifact": artifact_path.relative_to(output_dir).as_posix(),
        }

        if gate and not auto_approve:
            stage_result.update(
                {
                    "status": "blocked",
                    "message": "Stage requires human approval. Re-run with auto_approve=True to continue.",
                }
            )
            final_status = "blocked"
        else:
            outputs = _run_deterministic_stage(stage, state)
            stage_result.update({"status": "done", "outputs": outputs})

        stage_result["completed_at"] = _utcnow_iso()
        _write_json(artifact_path, stage_result)
        results["stages"].append(stage_result)

        if stage_result["status"] == "blocked":
            break

    results["completed_at"] = _utcnow_iso()
    results["final_status"] = final_status
    results["artifact_dir"] = str(output_dir)

    summary_path = output_dir / "pipeline_summary.json"
    _write_json(summary_path, results)

    if final_status == "completed":
        console.print("\n[bold green]Pipeline complete![/bold green]")
    elif final_status == "blocked":
        console.print("\n[bold yellow]Pipeline blocked at approval gate[/bold yellow]")
    else:
        console.print(f"\n[bold red]Pipeline ended with status: {final_status}[/bold red]")
    console.print(f"Summary: {summary_path}")

    return results
