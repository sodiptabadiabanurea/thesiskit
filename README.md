# ThesisKit

> **Everything you need to ship academic research.**

From research idea to conference-ready paper — with real citations, verified sources, and zero hallucinations.

## Why ThesisKit?

Academic research automation tools either hallucinate citations or require endless babysitting. ThesisKit is different:

- **📚 Real Citations** — arXiv, Semantic Scholar, CrossRef integration. Every citation verified.
- **🔬 Reproducible** — Experiments run in sandbox with actual results, not fake data.
- **📝 Conference-Ready** — NeurIPS, ICML, ICLR LaTeX templates built-in.
- **🤖 Multi-Agent Review** — Peer review simulation catches methodology gaps before submission.
- **⚡ Fast Iteration** — Generate-verify-repair loop converges quickly.

## Quick Start

```bash
# Install
pip install thesiskit

# Run research pipeline
thesiskit run --topic "Your research idea here" --auto-approve

# Output: paper.md, paper.tex, references.bib, charts/, experiment_runs/
```

## How It Works

```
Idea → Literature → Hypothesis → Experiment → Analysis → Paper → Review → LaTeX
  ↓        ↓            ↓            ↓           ↓         ↓        ↓        ↓
Topic   arXiv +      Multi-agent   Sandbox     Stats    Draft   Peer    Conference
Init    S2 APIs      Debate        Execution   Analysis        Review  Template
```

**8 Phases, 20 Stages:**

| Phase | Stages | What Happens |
|-------|--------|--------------|
| **A: Scoping** | 1-2 | Decompose topic into research questions |
| **B: Literature** | 3-6 | Search, collect, screen, extract from real papers |
| **C: Synthesis** | 7-8 | Cluster findings, generate testable hypotheses |
| **D: Design** | 9-11 | Design experiments, generate code, plan resources |
| **E: Execution** | 12-13 | Run experiments with self-healing |
| **F: Analysis** | 14-15 | Multi-agent analysis, proceed/refine/pivot decision |
| **G: Writing** | 16-19 | Outline, draft, peer review, revise |
| **H: Finalization** | 20 | Quality gate, LaTeX export, citation verification |

## Key Features

### ✅ Verified Citations
- 4-layer verification: arXiv ID → CrossRef DOI → Semantic Scholar → LLM relevance
- Hallucinated references automatically removed
- BibTeX with real, clickable links

### ✅ Real Experiments
- Sandbox execution with actual code runs
- NaN/Inf detection and auto-repair
- Partial result capture on failure
- Hardware-aware (GPU/MPS/CPU auto-detect)

### ✅ Multi-Agent Review
- Optimist, Skeptic, Methodologist perspectives
- Evidence-methodology consistency checks
- Catches overclaiming before you submit

### ✅ Conference Templates
- NeurIPS 2025
- ICML 2026
- ICLR 2026
- Custom templates supported

## Configuration

Minimal `config.yaml`:

```yaml
project:
  name: "my-research"

research:
  topic: "Your topic here"

llm:
  provider: "openai-compatible"
  base_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  primary_model: "gpt-4o"

experiment:
  mode: "sandbox"
  sandbox:
    python_path: ".venv/bin/python"
```

### Use Any LLM

```yaml
# OpenAI
llm:
  provider: "openai-compatible"
  base_url: "https://api.openai.com/v1"

# Anthropic
llm:
  provider: "anthropic"
  api_key_env: "ANTHROPIC_API_KEY"

# Local (Ollama, vLLM, etc.)
llm:
  provider: "openai-compatible"
  base_url: "http://localhost:11434/v1"

# ACP (Claude Code, Codex, etc.)
llm:
  provider: "acp"
  acp:
    agent: "codex"
```

## Output Structure

```
artifacts/run-YYYYMMDD-HHMMSS/
├── paper_draft.md          # Full paper in Markdown
├── deliverables/
│   ├── paper.tex           # Conference-ready LaTeX
│   ├── references.bib      # Verified BibTeX citations
│   └── charts/             # Auto-generated figures
├── experiment_runs/        # Code + results
├── verification_report.json
└── reviews.md              # Multi-agent peer review
```

## Comparison

| Feature | ThesisKit | AutoResearchClaw | AI Scientist |
|---------|-----------|------------------|--------------|
| Verified citations | ✅ 4-layer | ✅ 4-layer | ❌ |
| Real experiments | ✅ Sandbox | ✅ Sandbox | ⚠️ Simulated |
| Multi-agent review | ✅ | ✅ | ❌ |
| Conference templates | ✅ 3+ | ✅ 3+ | ❌ |
| Self-healing code | ✅ | ✅ | ❌ |
| Open source | ✅ MIT | ✅ MIT | ❌ |

## Philosophy

**No hallucinations.** Every citation is real. Every experiment actually runs.

**No babysitting.** Set `--auto-approve` and walk away. The pipeline self-corrects.

**No black boxes.** Every stage produces inspectable artifacts. You always know what happened.

## Roadmap

- [ ] Browser-based paper collection
- [ ] Obsidian knowledge base integration
- [ ] Parallel stage execution
- [ ] More conference templates (CVPR, ACL, etc.)
- [ ] Web UI for monitoring

## Contributing

Contributions welcome! Areas of interest:

- New literature sources (Google Scholar, PubMed, etc.)
- Additional conference templates
- Better experiment sandboxing
- Web dashboard

## License

MIT

## Citation

If you use ThesisKit in your research:

```bibtex
@misc{thesiskit2026,
  author       = {ThesisKit Contributors},
  title        = {ThesisKit: Everything You Need to Ship Academic Research},
  year         = {2026},
  url          = {https://github.com/YOUR_USERNAME/thesiskit},
}
```

---

**Built for researchers who ship.** 🚀
