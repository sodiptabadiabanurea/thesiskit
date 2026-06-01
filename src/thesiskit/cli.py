"""CLI for ThesisKit."""

import argparse
import os
import shutil
from importlib import resources
from pathlib import Path
from typing import Any

from rich.console import Console

from thesiskit import __version__
from thesiskit.config import Config
from thesiskit.literature.citations import (
    CitationVerifier,
    load_citations_bibtex,
    load_citations_json,
    verify_citations_json_file,
    write_citations_bibtex,
    write_citations_json,
)
from thesiskit.pipeline.runner import run_pipeline

console = Console()


def _project_root() -> Path:
    """Return the repository root when running from a source checkout."""
    return Path(__file__).resolve().parents[2]


def _mini_run_source():
    """Return mini-run artifacts from a source checkout or installed package data."""
    checkout_source = _project_root() / "examples" / "mini-run"
    if checkout_source.is_dir():
        return checkout_source

    try:
        package_source = resources.files("thesiskit.example_data").joinpath("mini-run")
    except ModuleNotFoundError as exc:  # pragma: no cover - packaging failure guard
        raise FileNotFoundError("Bundled mini-run example data is not available") from exc

    if package_source.is_dir():
        return package_source

    raise FileNotFoundError(f"Mini-run example not found: {checkout_source}")


def _is_thesiskit_mini_run(path: Path) -> bool:
    """Return whether a directory looks like a previous ThesisKit mini-run copy."""
    markers = [
        "input/topic.txt",
        "citations/papers.json",
        "experiment/results.json",
        "verification/full_report.md",
    ]
    return path.is_dir() and all((path / marker).is_file() for marker in markers)


def _copy_tree(source, destination: Path) -> None:
    """Copy a filesystem path or importlib Traversable tree."""
    if isinstance(source, Path):
        shutil.copytree(source, destination)
        return

    destination.mkdir(parents=True, exist_ok=False)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            _copy_tree(child, target)
        else:
            target.write_bytes(child.read_bytes())


def _default_metadata_cache_dir() -> Path:
    """Return the default user cache for reusable live metadata."""
    cache_home = os.environ.get("XDG_CACHE_HOME")
    base_dir = Path(cache_home) if cache_home else Path.home() / ".cache"
    return base_dir / "thesiskit" / "metadata"


def copy_mini_run_example(output_dir: Path, overwrite: bool = False) -> Path:
    """Copy the checked-in mini-run example to a user-controlled directory."""
    source_dir = _mini_run_source()

    output_dir = output_dir.resolve()
    if output_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"Output path already exists: {output_dir}. Use --overwrite to replace it."
            )
        if output_dir.is_dir():
            is_empty = not any(output_dir.iterdir())
            if not is_empty and not _is_thesiskit_mini_run(output_dir):
                raise FileExistsError(
                    f"Output path exists and is not a ThesisKit mini-run: {output_dir}. "
                    "Refusing to delete unrelated files."
                )
            shutil.rmtree(output_dir)
        else:
            raise FileExistsError(
                f"Output path exists and is not a ThesisKit mini-run directory: {output_dir}"
            )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    _copy_tree(source_dir, output_dir)
    return output_dir


def _build_verifier(
    verifier_factory,
    s2_api_key: str | None = None,
    arxiv_base_url: str | None = None,
    acl_base_url: str | None = None,
    cache_dir: Path | None = None,
    retry_attempts: int = 1,
    retry_backoff_seconds: float = 0.0,
):
    """Create a citation verifier while keeping tests injectable."""
    kwargs: dict[str, Any] = {}
    resolved_s2_api_key = s2_api_key or os.environ.get("S2_API_KEY")
    resolved_cache_dir = cache_dir or _default_metadata_cache_dir()
    if resolved_s2_api_key:
        kwargs["s2_api_key"] = resolved_s2_api_key
    if arxiv_base_url:
        kwargs["arxiv_base_url"] = arxiv_base_url
    if acl_base_url:
        kwargs["acl_base_url"] = acl_base_url
    kwargs["cache_dir"] = resolved_cache_dir
    if retry_attempts != 1:
        kwargs["retry_attempts"] = retry_attempts
    if retry_backoff_seconds != 0.0:
        kwargs["retry_backoff_seconds"] = retry_backoff_seconds
    return verifier_factory(**kwargs)


def main(argv: list[str] | None = None, verifier_factory: Any = CitationVerifier) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="thesiskit",
        description="Everything you need to ship academic research",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the research pipeline")
    run_parser.add_argument(
        "--topic",
        "-t",
        type=str,
        help="Research topic",
    )
    run_parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config file",
    )
    run_parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve gate stages",
    )
    run_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output directory",
    )

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument(
        "name",
        type=str,
        help="Project name",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate config file")
    validate_parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config file",
    )

    # Example command
    example_parser = subparsers.add_parser("example", help="Copy reproducible examples")
    example_subparsers = example_parser.add_subparsers(
        dest="example_name",
        help="Available examples",
    )
    mini_run_parser = example_subparsers.add_parser(
        "mini-run",
        help="Copy the citation-verified mini-run demo",
    )
    mini_run_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("mini-run"),
        help="Destination directory for copied artifacts",
    )
    mini_run_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the destination if it already exists",
    )

    # Citations command
    citations_parser = subparsers.add_parser(
        "citations",
        help="Verify and report citation metadata",
    )
    citation_subparsers = citations_parser.add_subparsers(
        dest="citation_command",
        help="Citation commands",
    )
    citation_verify_parser = citation_subparsers.add_parser(
        "verify",
        help="Verify papers.json citations and write a Markdown report",
    )
    citation_verify_parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("citations/papers.json"),
        help="Path to a JSON list of citation metadata",
    )
    citation_verify_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("citations/verification_report.md"),
        help="Path for the generated Markdown verification report",
    )
    citation_verify_parser.add_argument(
        "--s2-api-key",
        type=str,
        default=None,
        help="Optional Semantic Scholar API key",
    )
    citation_verify_parser.add_argument(
        "--arxiv-base-url",
        type=str,
        default=None,
        help="Optional arXiv API query endpoint, such as a Cloudflare Worker cache proxy",
    )
    citation_verify_parser.add_argument(
        "--acl-base-url",
        type=str,
        default=None,
        help="Optional ACL Anthology base URL for exact-paper BibTeX lookups",
    )
    citation_verify_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Directory for reusable arXiv/Semantic Scholar/ACL Anthology metadata cache",
    )
    citation_verify_parser.add_argument(
        "--retry-attempts",
        type=int,
        default=1,
        help="Attempts per live metadata lookup before reporting an API failure",
    )
    citation_verify_parser.add_argument(
        "--retry-backoff",
        type=float,
        default=0.0,
        help="Initial retry backoff in seconds; doubles after each failed attempt",
    )
    citation_verify_parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="Write the report but exit 0 even when citations fail verification",
    )
    citation_export_parser = citation_subparsers.add_parser(
        "export-bibtex",
        help="Export papers.json citations to BibTeX",
    )
    citation_export_parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("citations/papers.json"),
        help="Path to a JSON list of citation metadata",
    )
    citation_export_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("citations/references.bib"),
        help="Path for the generated BibTeX file",
    )
    citation_import_parser = citation_subparsers.add_parser(
        "import-bibtex",
        help="Import BibTeX references into papers.json",
    )
    citation_import_parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("citations/references.bib"),
        help="Path to a BibTeX references file",
    )
    citation_import_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("citations/papers.json"),
        help="Path for the generated JSON citation metadata",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        # Load config
        if args.config.exists():
            config = Config.from_yaml(args.config)
        else:
            console.print("[yellow]Config not found, using defaults[/yellow]")
            config = Config()

        # Run pipeline
        run_pipeline(
            config=config,
            topic=args.topic,
            auto_approve=args.auto_approve,
            output_dir=args.output,
        )
        return 0

    elif args.command == "init":
        # Create project structure
        project_dir = Path(args.name)
        project_dir.mkdir(exist_ok=True)

        # Create config
        config = Config(project={"name": args.name})
        config.save_yaml(project_dir / "config.yaml")

        # Create directories
        (project_dir / "artifacts").mkdir(exist_ok=True)
        (project_dir / "references").mkdir(exist_ok=True)

        console.print(f"[green]Created project: {args.name}[/green]")
        console.print("  - config.yaml")
        console.print("  - artifacts/")
        console.print("  - references/")
        return 0

    elif args.command == "validate":
        if args.config.exists():
            config = Config.from_yaml(args.config)
            console.print("[green]✓ Config is valid[/green]")
            console.print(f"  Topic: {config.research.topic or '(not set)'}")
            console.print(f"  LLM: {config.llm.provider} / {config.llm.primary_model}")
            return 0
        else:
            console.print(f"[red]✗ Config not found: {args.config}[/red]")
            return 1

    elif args.command == "example" and args.example_name == "mini-run":
        try:
            copied_to = copy_mini_run_example(args.output, overwrite=args.overwrite)
        except (FileExistsError, FileNotFoundError) as exc:
            console.print(f"[red]✗ {exc}[/red]")
            return 1

        console.print(f"[green]Copied mini-run example to {copied_to}[/green]")
        return 0

    elif args.command == "example":
        example_parser.print_help()
        return 0

    elif args.command == "citations" and args.citation_command == "verify":
        verifier = _build_verifier(
            verifier_factory,
            s2_api_key=args.s2_api_key,
            arxiv_base_url=args.arxiv_base_url,
            acl_base_url=args.acl_base_url,
            cache_dir=args.cache_dir,
            retry_attempts=args.retry_attempts,
            retry_backoff_seconds=args.retry_backoff,
        )
        try:
            results = verify_citations_json_file(args.input, args.output, verifier=verifier)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]✗ {exc}[/red]")
            return 1
        finally:
            if hasattr(verifier, "close"):
                verifier.close()

        passed = sum(1 for result in results if result.passed)
        failed = len(results) - passed
        console.print(f"[green]Wrote citation verification report to {args.output}[/green]")
        if failed:
            console.print(f"[red]✗ Citation verification: {passed} passed / {failed} failed[/red]")
        else:
            console.print(f"[green]✓ Citation verification: {passed} passed / 0 failed[/green]")
        return 0 if failed == 0 or args.allow_failures else 1

    elif args.command == "citations" and args.citation_command == "export-bibtex":
        try:
            citations = load_citations_json(args.input)
            write_citations_bibtex(citations, args.output)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]✗ {exc}[/red]")
            return 1
        console.print(f"[green]Wrote BibTeX references to {args.output}[/green]")
        return 0

    elif args.command == "citations" and args.citation_command == "import-bibtex":
        try:
            citations = load_citations_bibtex(args.input)
            write_citations_json(citations, args.output)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]✗ {exc}[/red]")
            return 1
        console.print(f"[green]Wrote citation metadata to {args.output}[/green]")
        return 0

    elif args.command == "citations":
        citations_parser.print_help()
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
