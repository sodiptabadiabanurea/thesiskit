"""CLI for ThesisKit."""

import argparse
from pathlib import Path

from rich.console import Console

from thesiskit import __version__
from thesiskit.config import Config
from thesiskit.pipeline.runner import run_pipeline

console = Console()


def main():
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
        "--topic", "-t",
        type=str,
        help="Research topic",
    )
    run_parser.add_argument(
        "--config", "-c",
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
        "--output", "-o",
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
        "--config", "-c",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config file",
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        # Load config
        if args.config.exists():
            config = Config.from_yaml(args.config)
        else:
            console.print(f"[yellow]Config not found, using defaults[/yellow]")
            config = Config()
        
        # Run pipeline
        run_pipeline(
            config=config,
            topic=args.topic,
            auto_approve=args.auto_approve,
            output_dir=args.output,
        )
    
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
        console.print(f"  - config.yaml")
        console.print(f"  - artifacts/")
        console.print(f"  - references/")
    
    elif args.command == "validate":
        if args.config.exists():
            config = Config.from_yaml(args.config)
            console.print(f"[green]✓ Config is valid[/green]")
            console.print(f"  Topic: {config.research.topic or '(not set)'}")
            console.print(f"  LLM: {config.llm.provider} / {config.llm.primary_model}")
        else:
            console.print(f"[red]✗ Config not found: {args.config}[/red]")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
