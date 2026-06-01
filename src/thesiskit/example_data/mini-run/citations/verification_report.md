# Citation Verification Report — mini-run

**Topic:** retrieval-augmented generation for small research teams
**Citations checked:** 3
**Verification layers:** arXiv ID resolves · DOI resolves (`10.48550/arXiv.*`) · author list matches arXiv metadata · title matches arXiv metadata · abstract excerpt verifiable on the arXiv landing page.

> This report is part of an example artifact set. Source URLs are the canonical
> arXiv abstract pages, which anyone can open to audit the citation manually.
> ThesisKit's current verification code checks arXiv records and Semantic
> Scholar metadata, including DOI fields when available. This checked-in
> mini-run keeps the same evidence in plain text so it can be audited without
> re-running network calls.

## Summary

| # | arXiv ID    | DOI                              | arXiv ID resolves | DOI resolves | Title match | Authors match | Status   |
|---|-------------|----------------------------------|-------------------|--------------|-------------|---------------|----------|
| 1 | 2005.11401  | 10.48550/arXiv.2005.11401        | yes               | yes          | yes         | yes           | verified |
| 2 | 2312.10997  | 10.48550/arXiv.2312.10997        | yes               | yes          | yes         | yes           | verified |
| 3 | 2302.00083  | 10.48550/arXiv.2302.00083        | yes               | yes          | yes         | yes           | verified |

**Citation coverage of the draft:** 3 / 3 in-text references resolve to entries in `references.bib` (100%).
**Hallucinated references removed:** 0.

## Per-citation detail

### [1] Lewis et al. 2020 — "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"

- **arXiv:** https://arxiv.org/abs/2005.11401
- **DOI:** https://doi.org/10.48550/arXiv.2005.11401
- **Venue:** NeurIPS 2020
- **Title-match:** exact (arXiv `title` field byte-equal to `papers.json[0].title`).
- **Author-match:** all 12 authors present in arXiv metadata, in order.
- **Abstract-match:** key phrase "combine pre-trained parametric and non-parametric memory" present in the arXiv abstract.
- **Used in draft:** Section 2 (Background), Section 3 (Method baseline definition).

### [2] Gao et al. 2023 — "Retrieval-Augmented Generation for Large Language Models: A Survey"

- **arXiv:** https://arxiv.org/abs/2312.10997
- **DOI:** https://doi.org/10.48550/arXiv.2312.10997
- **Venue:** arXiv preprint (survey; cited as positioning reference).
- **Title-match:** exact.
- **Author-match:** all 10 authors present.
- **Abstract-match:** "Naive RAG", "Advanced RAG", and "Modular RAG" taxonomy terms present in the abstract.
- **Used in draft:** Section 2 (Background), Section 5 (Discussion — taxonomy positioning).

### [3] Ram et al. 2023 — "In-Context Retrieval-Augmented Language Models"

- **arXiv:** https://arxiv.org/abs/2302.00083
- **DOI:** https://doi.org/10.48550/arXiv.2302.00083
- **Venue:** TACL 2023.
- **Title-match:** exact.
- **Author-match:** all 7 authors present.
- **Abstract-match:** "In-Context RALM" and "perplexity gains" present in the arXiv abstract.
- **Used in draft:** Section 3 (Method — in-context retrieval variant), Section 4 (Results discussion).

## Notes

- All three sources were chosen because they are widely cited, openly accessible, and easy to manually re-verify.
- No paywalled or preprint-only-with-restricted-access sources were used.
- The mini-run does not introduce additional citations beyond these three; this keeps the example auditable.
