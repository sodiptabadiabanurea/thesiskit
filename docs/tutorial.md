# ThesisKit Tutorial - From Idea to Academic Paper

## 📚 Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Pipeline Overview](#pipeline-overview)
5. [Step-by-Step Walkthrough](#step-by-step-walkthrough)
6. [Configuration Guide](#configuration-guide)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is ThesisKit?

```
┌─────────────────────────────────────────────────────────────┐
│                      ThesisKit                              │
│                                                             │
│   "Everything you need to ship academic research"          │
│                                                             │
│   ┌─────────┐    ┌──────────┐    ┌─────────┐              │
│   │  Idea   │ -> │ Research │ -> │  Paper  │              │
│   └─────────┘    └──────────┘    └─────────┘              │
│                                                             │
│   • Real citations (arXiv, Semantic Scholar)               │
│   • Multi-agent peer review                                │
│   • Experiment sandbox                                      │
│   • Conference-ready LaTeX                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Use ThesisKit?

| Feature | Benefit |
|---------|---------|
| ✅ Real Citations | No hallucinated references |
| ✅ Verified Sources | 4-layer citation verification |
| ✅ Multi-Agent Review | Catches methodology gaps |
| ✅ Experiment Sandbox | Actual code execution |
| ✅ Conference Templates | NeurIPS, ICML, ICLR ready |

---

## Installation

### Step 1: Install via pip

```bash
# From PyPI (recommended)
pip install thesiskit

# Or from GitHub
pip install git+https://github.com/sodiptabadiabanurea/thesiskit.git
```

### Step 2: Verify Installation

```bash
$ thesiskit --version
thesiskit 0.4.0

$ thesiskit --help
usage: thesiskit [-h] [--version] {run,init,validate} ...

Everything you need to ship academic research
```

### Step 3: Set Up API Keys (Optional)

```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For GLM (Zhipu AI)
export ZAI_API_KEY="..."
```

---

## Quick Start

### Create Your First Project

```bash
# Step 1: Initialize project
$ thesiskit init my-research

Created project: my-research
  - config.yaml
  - artifacts/
  - references/

# Step 2: Navigate to project
$ cd my-research

# Step 3: Edit config.yaml with your topic
$ nano config.yaml
```

### Run Research Pipeline

```bash
# Step 4: Run pipeline
$ thesiskit run --topic "Your Research Topic" --auto-approve

ThesisKit Pipeline
Run ID: tk-20260318-093000
Topic: Your Research Topic
Output: artifacts/tk-20260318-093000

Stage  1/20: TOPIC_INIT         ✓
Stage  2/20: PROBLEM_DECOMPOSE  ✓
Stage  3/20: SEARCH_STRATEGY    ✓
...
Stage 20/20: QUALITY_GATE       ✓

Pipeline complete!
Stages completed: 20/20
```

---

## Pipeline Overview

### 20-Stage Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    ThesisKit Pipeline                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASE A: Scoping (Stages 1-2)                              │
│  ┌──────────────────────────────────────────────┐          │
│  │ 1. TOPIC_INIT                                │          │
│  │    ↓                                         │          │
│  │ 2. PROBLEM_DECOMPOSE                         │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  PHASE B: Literature (Stages 3-6)                           │
│  ┌──────────────────────────────────────────────┐          │
│  │ 3. SEARCH_STRATEGY                           │          │
│  │    ↓                                         │          │
│  │ 4. LITERATURE_COLLECT (arXiv + S2)          │          │
│  │    ↓                                         │          │
│  │ 5. LITERATURE_SCREEN *GATE*                 │          │
│  │    ↓                                         │          │
│  │ 6. KNOWLEDGE_EXTRACT                         │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  PHASE C: Synthesis (Stages 7-8)                            │
│  ┌──────────────────────────────────────────────┐          │
│  │ 7. SYNTHESIS                                 │          │
│  │    ↓                                         │          │
│  │ 8. HYPOTHESIS_GEN (Multi-Agent Debate)      │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  PHASE D: Design (Stages 9-11)                              │
│  ┌──────────────────────────────────────────────┐          │
│  │ 9. EXPERIMENT_DESIGN *GATE*                 │          │
│  │    ↓                                         │          │
│  │ 10. CODE_GENERATION                          │          │
│  │    ↓                                         │          │
│  │ 11. RESOURCE_PLANNING                        │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  PHASE E: Execution (Stages 12-13)                          │
│  ┌──────────────────────────────────────────────┐          │
│  │ 12. EXPERIMENT_RUN (Sandbox)                │          │
│  │    ↓                                         │          │
│  │ 13. ITERATIVE_REFINE                         │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  PHASE F: Analysis (Stages 14-15)                           │
│  ┌──────────────────────────────────────────────┐          │
│  │ 14. RESULT_ANALYSIS                          │          │
│  │    ↓                                         │          │
│  │ 15. RESEARCH_DECISION (PIVOT/REFINE)        │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  PHASE G: Writing (Stages 16-19)                            │
│  ┌──────────────────────────────────────────────┐          │
│  │ 16. PAPER_OUTLINE                            │          │
│  │    ↓                                         │          │
│  │ 17. PAPER_DRAFT                              │          │
│  │    ↓                                         │          │
│  │ 18. PEER_REVIEW (Multi-Agent)               │          │
│  │    ↓                                         │          │
│  │ 19. PAPER_REVISION                           │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  PHASE H: Finalization (Stage 20)                           │
│  ┌──────────────────────────────────────────────┐          │
│  │ 20. QUALITY_GATE *GATE*                     │          │
│  │     → LaTeX Export                           │          │
│  │     → Citation Verification                  │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Multi-Agent Review System

```
┌─────────────────────────────────────────────────────────┐
│              Multi-Agent Peer Review                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    ┌──────────┐                                        │
│    │ Optimist │ → Focus: Innovation, potential         │
│    └──────────┘                                        │
│         ↓                                              │
│    ┌──────────┐                                        │
│    │ Skeptic  │ → Focus: Flaws, overclaiming          │
│    └──────────┘                                        │
│         ↓                                              │
│    ┌───────────────┐                                   │
│    │ Methodologist │ → Focus: Experimental design      │
│    └───────────────┘                                   │
│         ↓                                              │
│    ┌───────────┐                                       │
│    │ Innovator │ → Focus: Novel approaches            │
│    └───────────┘                                       │
│         ↓                                              │
│    ┌───────────┐                                       │
│    │ Pragmatist│ → Focus: Feasibility                 │
│    └───────────┘                                       │
│         ↓                                              │
│    ┌───────────┐                                       │
│    │ Contrarian│ → Focus: Problem framing             │
│    └───────────┘                                       │
│         ↓                                              │
│    ┌────────────────────────────────────┐             │
│    │      SYNTHESIZED REVIEW            │             │
│    │  • Key concerns across agents      │             │
│    │  • Suggested improvements          │             │
│    └────────────────────────────────────┘             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Walkthrough

### Example: VPS Hardening Automation Research

#### Step 1: Initialize Project

```bash
$ thesiskit init vps-hardening-research

📁 Creating project: vps-hardening-research
├── config.yaml          # Configuration file
├── artifacts/           # Output directory
└── references/          # Citation storage

✅ Project initialized successfully!
```

#### Step 2: Configure Your Research

Edit `config.yaml`:

```yaml
project:
  name: "vps-hardening-research"

research:
  topic: "VPS Hardening Automation — Ansible/Bash scripts for auto-hardening Ubuntu VPS according to CIS Benchmark"
  domains:
    - "security"
    - "automation"
  daily_paper_count: 10
  quality_threshold: 4.0

llm:
  provider: "openai-compatible"
  base_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  primary_model: "gpt-4o"

experiment:
  mode: "sandbox"
  time_budget_sec: 300
```

#### Step 3: Run Pipeline

```bash
$ thesiskit run --config config.yaml --auto-approve

🚀 Starting ThesisKit Pipeline

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run ID: tk-20260318-093500
Topic: VPS Hardening Automation — Ansible/Bash scripts...
Output: artifacts/tk-20260318-093500
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE A: Scoping
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/20] TOPIC_INIT                ████████████ ✓ (0.2s)
[2/20] PROBLEM_DECOMPOSE         ████████████ ✓ (1.5s)
       → Generated 4 research questions

PHASE B: Literature
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/20] SEARCH_STRATEGY           ████████████ ✓ (0.1s)
[4/20] LITERATURE_COLLECT        ████████████ ✓ (3.2s)
       → arXiv: 12 papers
       → Semantic Scholar: 8 papers
[5/20] LITERATURE_SCREEN ⚠️     ████████████ ✓ (1.1s)
       → Retained 15 relevant papers
[6/20] KNOWLEDGE_EXTRACT         ████████████ ✓ (2.4s)

PHASE C: Synthesis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[7/20] SYNTHESIS                 ████████████ ✓ (1.8s)
[8/20] HYPOTHESIS_GEN            ████████████ ✓ (3.5s)
       → Generated 2 testable hypotheses

PHASE D: Design
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[9/20] EXPERIMENT_DESIGN ⚠️     ████████████ ✓ (2.1s)
[10/20] CODE_GENERATION          ████████████ ✓ (1.9s)
[11/20] RESOURCE_PLANNING        ████████████ ✓ (0.3s)

PHASE E: Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[12/20] EXPERIMENT_RUN           ████████████ ✓ (5.2s)
[13/20] ITERATIVE_REFINE         ████████████ ✓ (1.4s)

PHASE F: Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[14/20] RESULT_ANALYSIS          ████████████ ✓ (1.6s)
[15/20] RESEARCH_DECISION        ████████████ ✓ (0.5s)
       → Decision: PROCEED

PHASE G: Writing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[16/20] PAPER_OUTLINE            ████████████ ✓ (1.2s)
[17/20] PAPER_DRAFT              ████████████ ✓ (4.8s)
[18/20] PEER_REVIEW              ████████████ ✓ (3.2s)
       → 3 agents reviewed
[19/20] PAPER_REVISION           ████████████ ✓ (2.1s)

PHASE H: Finalization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[20/20] QUALITY_GATE ⚠️         ████████████ ✓ (1.8s)
       → All citations verified
       → LaTeX export complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Pipeline complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stages completed: 20/20
Total time: 35.2 seconds

Output files:
  📄 paper.md
  📄 paper.tex (NeurIPS 2025)
  📄 references.bib
  📊 verification_report.json
  📝 reviews.md
```

#### Step 4: Review Output

```bash
$ cd artifacts/tk-20260318-093500

$ ls -la
drwxr-xr-x  deliverables/
-rw-r--r--  paper.md
-rw-r--r--  pipeline_summary.json

$ cd deliverables

$ ls -la
-rw-r--r--  paper.tex           # Conference-ready LaTeX
-rw-r--r--  references.bib      # BibTeX citations
drwxr-xr-x  charts/             # Generated figures
```

---

## Configuration Guide

### Minimal Configuration

```yaml
project:
  name: "my-research"

research:
  topic: "Your topic here"

llm:
  provider: "openai-compatible"
  api_key_env: "OPENAI_API_KEY"
  primary_model: "gpt-4o"
```

### Full Configuration

```yaml
project:
  name: "my-research"
  
research:
  topic: "Your research topic"
  domains:
    - "machine-learning"
    - "security"
  daily_paper_count: 10
  quality_threshold: 4.0

runtime:
  timezone: "UTC"
  max_parallel_tasks: 3
  approval_timeout_hours: 12
  retry_limit: 2

llm:
  provider: "openai-compatible"
  base_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  primary_model: "gpt-4o"
  fallback_models:
    - "gpt-4o-mini"

experiment:
  mode: "sandbox"
  time_budget_sec: 300
  max_iterations: 10
  metric_key: "primary_metric"
  metric_direction: "minimize"
  sandbox:
    python_path: ".venv/bin/python"
    gpu_required: false
    max_memory_mb: 4096

security:
  hitl_required_stages: [5, 9, 20]
  allow_publish_without_approval: false
  redact_sensitive_logs: true
```

### LLM Provider Options

```
┌─────────────────────────────────────────────────────────┐
│              Supported LLM Providers                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  OpenAI Compatible                                      │
│  ┌───────────────────────────────────────────┐        │
│  │ provider: "openai-compatible"             │        │
│  │ base_url: "https://api.openai.com/v1"    │        │
│  │ primary_model: "gpt-4o"                   │        │
│  └───────────────────────────────────────────┘        │
│                                                         │
│  GLM (Zhipu AI)                                         │
│  ┌───────────────────────────────────────────┐        │
│  │ provider: "glm"                           │        │
│  │ base_url: "https://api.z.ai/api/..."     │        │
│  │ primary_model: "glm-5"                    │        │
│  └───────────────────────────────────────────┘        │
│                                                         │
│  Local (Ollama, vLLM, etc.)                            │
│  ┌───────────────────────────────────────────┐        │
│  │ provider: "openai-compatible"             │        │
│  │ base_url: "http://localhost:11434/v1"    │        │
│  │ primary_model: "llama3"                   │        │
│  └───────────────────────────────────────────┘        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Advanced Usage

### Python API

```python
from thesiskit import run_full_pipeline, Config

# Create config
config = Config()
config.research.topic = "Your Research Topic"
config.llm.primary_model = "gpt-4o"

# Run pipeline
result = run_full_pipeline(
    topic="Your Research Topic",
    config=config,
    auto_approve=True,
)

# Check results
print(f"Status: {result['final_status']}")
print(f"Stages completed: {len(result['stages'])}")
```

### Use Specific Modules

```python
# Literature search
from thesiskit.literature.arxiv import ArxivClient
from thesiskit.literature.semanticscholar import SemanticScholarClient

with ArxivClient() as arxiv:
    papers = arxiv.search("machine learning", max_results=10)
    for paper in papers:
        print(f"{paper['title']} - {paper['arxiv_id']}")

# Citation verification
from thesiskit.literature.citations import Citation, CitationVerifier

citation = Citation(
    title="Attention Is All You Need",
    authors=["Vaswani et al."],
    arxiv_id="1706.03762",
)

with CitationVerifier() as verifier:
    verified = verifier.verify(citation)
    print(f"Verified: {verified.verification_level}")

# Paper building
from thesiskit.writing import PaperBuilder

paper = (
    PaperBuilder()
    .set_title("My Research Paper")
    .add_author("John Doe")
    .set_abstract("This is my abstract.")
    .add_section("Introduction", "Introduction text...", level=1)
    .add_section("Methods", "Methods text...", level=1)
    .build()
)

paper.save("paper.md", format="markdown")
paper.save("paper.tex", format="latex")
```

### Custom Templates

```python
from thesiskit.templates import generate_latex, Conference

latex = generate_latex(
    conference=Conference.NEURIPS_2025,
    title="My Paper",
    authors="John Doe and Jane Smith",
    abstract="Abstract text...",
    body="\\section{Introduction}\n...",
)
```

---

## Troubleshooting

### Common Issues

#### Import Error

```
❌ Error: ImportError: cannot import name 'X' from 'thesiskit'
```

**Solution:**
```bash
# Reinstall package
pip install --upgrade --force-reinstall thesiskit
```

#### API Key Not Found

```
❌ Error: OPENAI_API_KEY not found in environment
```

**Solution:**
```bash
# Set environment variable
export OPENAI_API_KEY="sk-..."

# Or in config.yaml
llm:
  api_key: "sk-..."  # Not recommended for public repos
```

#### Sandbox Timeout

```
❌ Error: Execution timed out after 300s
```

**Solution:**
```yaml
# Increase timeout in config.yaml
experiment:
  time_budget_sec: 600  # 10 minutes
```

#### Citation Verification Failed

```
⚠️ Warning: Citation could not be verified
```

**Solution:**
- Check arXiv ID is correct
- Check DOI is valid
- Check internet connection
- Some papers may not be in Semantic Scholar

---

## Output Structure

```
artifacts/tk-YYYYMMDD-HHMMSS/
├── paper.md                 # Full paper in Markdown
├── pipeline_summary.json    # Pipeline execution summary
├── deliverables/
│   ├── paper.tex            # Conference-ready LaTeX
│   ├── references.bib       # BibTeX citations
│   └── charts/              # Auto-generated figures
│       ├── figure1.png
│       └── figure2.png
├── experiment_runs/         # Experiment code + results
│   ├── experiment.py
│   └── results.json
├── verification_report.json # Citation verification status
└── reviews.md               # Multi-agent peer review
```

---

## Citation

If you use ThesisKit in your research:

```bibtex
@misc{thesiskit2026,
  author       = {ThesisKit Contributors},
  title        = {ThesisKit: Everything You Need to Ship Academic Research},
  year         = {2026},
  url          = {https://github.com/sodiptabadiabanurea/thesiskit},
}
```

---

## Support

- **GitHub:** https://github.com/sodiptabadiabanurea/thesiskit
- **Issues:** https://github.com/sodiptabadiabanurea/thesiskit/issues
- **Docs:** https://github.com/sodiptabadiabanurea/thesiskit#readme

---

**Built for researchers who ship.** 🚀
