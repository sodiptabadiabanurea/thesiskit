# Retrieval-Augmented Generation for Small Research Teams: A Workflow Sketch

**Mini-run demo draft — produced by ThesisKit `examples/mini-run`.**
This is a conference-draft-style artifact, not a peer-reviewed paper.
All numerical results come from a synthetic deterministic experiment
(`experiment/results.json`) and should be read as an illustration of the
ThesisKit pipeline's output format, not as a benchmark claim.

## Abstract

Small research teams (2–6 people) often maintain a heterogeneous internal
knowledge base — design docs, meeting notes, prior experiment write-ups — that
is too small to justify a fine-tuned model but too large to keep in working
memory. We sketch a lightweight retrieval-augmented generation (RAG) workflow
for that setting and contrast it against a no-retrieval closed-book baseline on
a synthetic 20-question evaluation set (`synthetic_rag_team_questions_v1`). On
this small demo, naive BM25 retrieval over the team knowledge base lifts
answer accuracy from 0.45 to 0.85 while keeping citation coverage at 0.95.
The contribution of this artifact is the workflow shape and the auditable
artifact set, not the absolute numbers.

## 1. Introduction

Retrieval-augmented generation [1] has become the default architecture for
grounding language model outputs in external sources. Recent surveys [2]
catalogue a growing taxonomy — Naive, Advanced, and Modular RAG. For small
teams, the relevant design question is not which exotic retriever to pick but
how to keep a citation-verified, reproducible workflow attached to a modest
internal corpus.

This mini-run sketches such a workflow:

1. Define the topic (`input/topic.txt`).
2. Pull a few canonical sources (`citations/papers.json`) and verify them
   (`citations/verification_report.md`).
3. Run a tiny deterministic experiment (`experiment/`).
4. Produce a draft and a final verification report (this file and
   `verification/full_report.md`).

## 2. Background

The original RAG framework of Lewis et al. [1] combines parametric and
non-parametric memory and remains a strong baseline for knowledge-intensive
tasks. Gao et al. [2] survey the resulting design space and group methods into
Naive, Advanced, and Modular RAG. Ram et al. [3] show that even prepending
retrieved passages to an off-the-shelf model — In-Context RALM — yields large
perplexity gains without any retraining, which is exactly the kind of
near-zero-engineering setup a small team would adopt.

## 3. Method

We compare two conditions on a synthetic 20-question evaluation set generated
from a small fictional team knowledge base:

- **baseline:** closed-book; the model answers from parametric memory only.
- **rag:** naive RAG — top-3 BM25 retrieval over the team knowledge base,
  closer in spirit to the in-context variant of [3] than to the trained
  retrieval-then-generate setup of [1].

The dataset, conditions, metrics, and reproducibility settings are recorded in
`experiment/config.yaml`. The experiment is run with `seed=42` and does not
require network access.

## 4. Results

| Metric                     | baseline | rag   |
|----------------------------|----------|-------|
| answer accuracy            | 0.45     | 0.85  |
| citation coverage          | n/a      | 0.95  |
| retrieval recall@3         | n/a      | 0.90  |

Adding retrieval lifts answer accuracy by 0.40 absolute on this synthetic set.
Citation coverage of 0.95 indicates that 19 of 20 RAG answers cite at least
one retrieved passage. **These numbers describe a synthetic demo, not a
benchmark; do not generalize them.**

## 5. Discussion

The mini-run illustrates two ThesisKit guarantees that matter for small
teams: every citation is resolvable to a public source (see
`citations/verification_report.md`) and every reported number is regenerable
from `experiment/config.yaml` plus a fixed seed. The cost is honesty about
scope — this is a deterministic toy experiment, not a benchmark. The
positioning of the workflow within the Naive/Advanced/Modular RAG taxonomy
[2] is Naive RAG by design: small teams benefit more from auditability than
from architectural novelty.

## 6. Limitations

- The 20-question synthetic dataset is not representative of any real
  internal corpus.
- Only one retriever (BM25, top-3) is evaluated.
- No human evaluation is included; correctness is judged against
  programmatically generated ground truth.

## 7. Conclusion

We released a fully auditable mini-run that shows the shape of a small-team
RAG workflow end-to-end: topic, verified citations, deterministic experiment,
draft, and final verification report. The intent is to make the ThesisKit
pipeline's outputs inspectable, not to make a benchmark claim.

## References

[1] Lewis et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP
Tasks.* NeurIPS 2020. arXiv:2005.11401.

[2] Gao et al. *Retrieval-Augmented Generation for Large Language Models: A
Survey.* arXiv:2312.10997, 2023.

[3] Ram et al. *In-Context Retrieval-Augmented Language Models.* TACL 2023.
arXiv:2302.00083.
