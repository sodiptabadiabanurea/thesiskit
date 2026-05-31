# mini-run: a fully auditable ThesisKit example

A tiny, end-to-end example that shows what a ThesisKit run produces — from
topic string to final verification report — for a single, deliberately small
research topic.

**Topic:** `retrieval-augmented generation for small research teams`

This directory is intentionally readable by hand. Everything is plain text,
JSON, or Markdown. There are no compiled PDFs and no binary blobs.

> Alpha 0.4.0 — this is a worked example of ThesisKit's artifact set, not a
> peer-reviewed paper. The experiment is **synthetic and deterministic**
> (`seed=42`, no network). The three citations are real and resolvable so
> the demo can be re-audited by hand.

## Layout

```
examples/mini-run/
├── README.md                       # this file
├── input/
│   └── topic.txt                   # one-line research topic
├── citations/
│   ├── papers.json                 # 3 real papers (arXiv ID + DOI + URL)
│   ├── verification_report.md      # per-citation resolution + match check
│   └── references.bib              # BibTeX for the 3 citations
├── experiment/
│   ├── config.yaml                 # dataset, seed, conditions, metrics
│   └── results.json                # deterministic synthetic results
├── draft/
│   └── paper.md                    # 7-section conference-draft template
└── verification/
    └── full_report.md              # end-to-end gate report
```

## How to read this in 60 seconds

1. **`input/topic.txt`** — the one-line topic.
2. **`citations/papers.json`** — the 3 real papers ThesisKit grounded the
   draft on. Each entry has an `arxiv_id`, a `doi`, and a public `url`.
3. **`experiment/results.json`** — the deterministic numbers behind the
   results table in `draft/paper.md`.
4. **`draft/paper.md`** — the rendered draft, with its citations resolving
   into `citations/references.bib`.
5. **`verification/full_report.md`** — the final gate report explaining what
   "verified" actually means here.

## Citations used in this mini-run

| # | Paper                                                                 | Year | arXiv          | DOI                              |
|---|-----------------------------------------------------------------------|------|----------------|----------------------------------|
| 1 | Lewis et al. — Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | 2020 | 2005.11401     | 10.48550/arXiv.2005.11401        |
| 2 | Gao et al. — Retrieval-Augmented Generation for LLMs: A Survey         | 2023 | 2312.10997     | 10.48550/arXiv.2312.10997        |
| 3 | Ram et al. — In-Context Retrieval-Augmented Language Models            | 2023 | 2302.00083     | 10.48550/arXiv.2302.00083        |

Anyone can open the arXiv URLs in `citations/papers.json` and check that the
titles, authors, and abstracts match — that is what makes this example a
"citation-verified" artifact rather than just a generated draft.

## Synthetic experiment

The experiment is intentionally tiny and deterministic:

- **Dataset:** `synthetic_rag_team_questions_v1` — 20 hand-crafted factoid
  questions about a fictional 4-person research team.
- **Seed:** `42`.
- **Conditions:** closed-book `baseline` vs. naive `rag` (BM25, top-3).
- **Network required:** no.

The reported numbers (`baseline_answer_accuracy = 0.45`,
`rag_answer_accuracy = 0.85`, `citation_coverage = 0.95`) are **demo
numbers**, not a benchmark result. Their job is to show what the
`experiment/results.json` schema looks like and to provide a stable target
for the regression test in `tests/test_examples.py`.

## What ThesisKit guarantees from this example

- Every citation resolves to a public source (see `citations/verification_report.md`).
- Every number in the draft is regenerable from `experiment/config.yaml` plus
  the seed.
- Every gate in `verification/full_report.md` is plain-text auditable.

What ThesisKit does **not** guarantee from this example:

- That the draft would be accepted at any specific venue.
- That the synthetic numbers generalize beyond this 20-question demo set.
- That a future production run will reproduce these exact decimals (only the
  invariants tested in `tests/test_examples.py`).
