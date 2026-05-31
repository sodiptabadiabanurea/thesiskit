# Mini-run Full Verification Report

**Topic:** retrieval-augmented generation for small research teams
**Pipeline status:** all gates pass on the checked-in artifacts.
**Gate philosophy:** every claim in the draft must be either (a) a citation
that resolves, or (b) a number that is regenerable from the experiment config
and seed in this directory.

## Gate summary

| Gate                            | Result | Evidence                                                    |
|---------------------------------|--------|-------------------------------------------------------------|
| Topic recorded                  | pass   | `input/topic.txt` matches `experiment/config.yaml` context. |
| Citations have real IDs         | pass   | 3 / 3 arXiv IDs + 3 / 3 DOIs in `citations/papers.json`.    |
| Citation URL shape is canonical | pass   | All three URLs use canonical arXiv abstract pages. Live network resolution was verified during PR preparation but is not required to re-run this offline example. |
| BibTeX references match JSON    | pass   | Keys `lewis2020rag`, `gao2023ragsurvey`, `ram2023incontext` map 1-to-1 to `papers.json` entries. |
| Citation coverage of draft      | pass   | 3 / 3 in-text references in `draft/paper.md` resolve.       |
| Experiment is reproducible      | pass   | `experiment/config.yaml` declares `seed: 42`, `deterministic: true`, `requires_network: false`. |
| Results respect demo invariants | pass   | `rag_answer_accuracy (0.85) > baseline_answer_accuracy (0.45)` and `citation_coverage (0.95) >= 0.9` per `experiment/results.json`. |
| Draft does not overclaim        | pass   | Numbers are framed as synthetic demo, not benchmark.        |
| No PDF / binary blobs           | pass   | Only plain-text / JSON / Markdown artifacts in this folder. |

## Scope and honesty notes

- This mini-run is an **example artifact set**, not a research finding.
- The experiment is **synthetic and deterministic** on purpose: the value of
  the demo is auditability, not novelty.
- "Verified" here means **the citation source resolves and matches its
  metadata**, not "peer reviewed" or "endorsed by the cited authors".
- All numbers are reproducible from `experiment/config.yaml` + the recorded
  seed without any network access.

## How to re-audit this mini-run by hand

1. Open each URL in `citations/papers.json` and confirm the title, authors,
   and year on the arXiv landing page.
2. Cross-reference `citations/references.bib` against `citations/papers.json`
   — every BibTeX entry should correspond to one JSON entry.
3. Check that every `[N]` reference in `draft/paper.md` appears in
   `references.bib`.
4. Re-derive the result invariants: `rag > baseline` and
   `citation_coverage >= 0.9` should both hold in `experiment/results.json`.
5. Confirm `experiment/config.yaml` declares `seed: 42` and a named dataset.
