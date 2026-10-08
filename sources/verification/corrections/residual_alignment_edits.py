"""Residual P0/P1 alignment edits applied by the orchestrator after the corrections workflow (2026-10-08).
Each replacement must match exactly once; line endings of each file are preserved.
Run from the workspace root: python -I sources/verification/corrections/residual_alignment_edits.py
"""
import pathlib

LOG = "reviews/CORRECTIONS_LOG_2026-10-08.md"


def edit(fn, pairs):
    p = pathlib.Path(fn)
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    t = raw.decode("utf-8").replace("\r\n", "\n")
    for a, b in pairs:
        n = t.count(a)
        if n != 1:
            print("!! count", n, fn, ascii(a[:80]))
            continue
        t = t.replace(a, b)
        print("ok", fn, ascii(a[:60]))
    if crlf:
        t = t.replace("\n", "\r\n")
    p.write_bytes(t.encode("utf-8"))


# 07: D.1 diagram + Part K index paths (M-01 / M-04)
edit("07_SAMPLE_LESSON.md", [
    ('A["PDF file<br/>(sha256)"] --> B["Pages<br/>list of (page_no, text)"]',
     'A["PDF file<br/>(sha256)"] --> B["Frozen text snapshot<br/>pages joined with newline<br/>(snapshot_id, page text hashes)"]'),
    ('D["Chunk records<br/>doc_id, chunk_id, text,<br/>char_start, char_end,<br/>page_start, page_end,<br/>params_hash"]',
     'D["Chunk records<br/>doc_id, snapshot_id, chunk_id, text,<br/>char_start, char_end (doc offsets),<br/>page_segments, text_sha256,<br/>params_hash"]'),
    ("- **Version every index.** Use `index/<corpus_sha>/<params_hash>/` with a manifest (chunker config, library versions, model revision). Never overwrite in place; keep v0 runnable (BACKBONE §4).\n"
     "- **Incremental updates.** With deterministic ids, re-chunk only changed documents (by file sha256), delete their old chunk ids, and add the new ones. Cross-document chunking would break this, which is a reason to keep chunking per document.",
     "- **Version every index.** Use `index/<snapshot_id>/<params_hash>/` with a manifest (snapshot manifest hash, chunker config, library versions, embedding model and revision). Never overwrite in place; keep v0 runnable (BACKBONE §4).\n"
     "- **Incremental updates.** Re-extract only changed documents (by file sha256). That produces a new snapshot, so their chunk ids change: delete the old ids and add the new ones. Embeddings are reused only through the content-keyed cache (`embedding_cache_key`), never by id. Cross-document chunking would break this, which is a reason to keep chunking per document.\n\n"
     f"> Revised 2026-10-08 (Codex M-01, M-04): the D.1 diagram and the index / incremental-update guidance now use the frozen snapshot, document offsets and content-keyed caching. See [corrections log]({LOG}#m-04)."),
])

# 06: Corpus T learner decision (§L)
edit("06_RAG_PROJECT_AND_EVALUATION_PLAN.md", [
    ('"snapshot_id": "<first 12 hex of sha256 over all docs\' doc_text_sha256 + parser/cleaning ids>",',
     '"snapshot_id": "<12 hex; exact formula below the manifest>",'),
    ("| **T** (main \"technical PDFs\") | 4–6 technical PDFs chosen by the learner. **Default proposal:** arXiv papers already in Source C: RAG (Lewis et al. 2020, #38), DPR (#19), HyDE (#32), Lost in the Middle (#39), RAPTOR (#40).",
     "| **T** (main \"technical PDFs\") | 5–6 technical PDFs. **Learner decision (2026-10-08, D-01/D-02):** the coach's suggested mix: 3–4 RAG papers from Source C (candidates: RAG (Lewis et al. 2020, #38), DPR (#19), HyDE (#32), Lost in the Middle (#39), RAPTOR (#40)) **plus 2 non-RAG technical papers**. The concrete list is proposed at C1, and the learner may swap any file."),
])

# 06: exact snapshot_id formula inserted after the manifest code block (M-01)
p = pathlib.Path("06_RAG_PROJECT_AND_EVALUATION_PLAN.md")
raw = p.read_bytes()
crlf = b"\r\n" in raw
t = raw.decode("utf-8").replace("\r\n", "\n")
anchor = '"snapshot_id": "<12 hex; exact formula below the manifest>",'
if "Exact `snapshot_id` formula" not in t and t.count(anchor) == 1:
    i = t.find(anchor)
    j = t.find("```", i)
    k = t.find("\n", j)
    ins = ("\n\n**Exact `snapshot_id` formula [N]** (so anyone recomputing it gets the same id):\n\n"
           "```python\n"
           "parts = [\"snapshot-v1\", f\"parser={backend}@{version}\", \"options=\" + json.dumps(options, sort_keys=True),\n"
           "         f\"cleaning={cleaning_version}\", \"page_join=\\\\n\"]\n"
           "parts += [f\"{doc_id}:{doc_text_sha256[doc_id]}\" for doc_id in sorted(doc_text_sha256)]\n"
           "snapshot_id = hashlib.sha256(\"|\".join(parts).encode(\"utf-8\")).hexdigest()[:12]\n"
           "```\n\n"
           "Any change to the parser, its version or options, the cleaning version, or any document's text therefore gives a new id. "
           "The `snap()` helper in [07 H.3](07_SAMPLE_LESSON.md) is a labelled test stand-in, not this formula.\n\n"
           f"> Revised 2026-10-08 (Codex M-01): the snapshot_id hash input is now fixed exactly. See [corrections log]({LOG}#m-01).")
    t = t[:k] + ins + t[k:]
    if crlf:
        t = t.replace("\n", "\r\n")
    p.write_bytes(t.encode("utf-8"))
    print("ok 06 snapshot formula inserted")
else:
    print("!! 06 snapshot formula not inserted (already present or anchor missing)")

# 02: authority statement (M-07), V3 + Gate 8→9 (M-06), V4 (M-06)
edit("02_RAG_MASTER_LEARNING_PLAN.md", [
    ("Every Phase 4–11 card also requires `gate{3→4}`, whether or not its Pre line says so. |",
     "Every Phase 4–11 card also requires `gate{3→4}`, whether or not its Pre line says so. **Authority:** the typed registry in [03 §2.1](03_RAG_CONCEPT_DEPENDENCY_MAP.md#21-edge-list-authoritative-the-diagram-is-generated-from-it) is the single unlock rule. A Pre line lists the key direct prerequisites, and every concept it names is validated to be an ancestor in that registry (`sources/verification/corrections/contracts_check.py`). Where 03 is stricter, 03 applies. |"),
    ("  - **calibrate** the threshold on a dev split and test it on held-out data;",
     "  - **calibrate** the threshold on a dev split and test it on held-out data, but make **no threshold claim until there are ≥ 15 unanswerable items with ≥ 5 in dev**. Even 6/6 correct has an exact 95% lower bound of only ≈ 0.54 ([06 §8.4](06_RAG_PROJECT_AND_EVALUATION_PLAN.md#84-calibration-against-human-labels));"),
    ("- [ ] The abstention policy is evaluated on the unanswerable set. Abstention precision/recall is reported, the threshold is chosen on a dev split and confirmed on held-out data, and the change in answerable accuracy is reported.",
     "- [ ] The abstention policy is evaluated on the unanswerable set, with ≥ 15 unanswerable items (≥ 5 in dev) before any threshold claim. Abstention precision/recall is reported with intervals, the threshold is chosen on dev and confirmed once on test, and the change in answerable accuracy (coverage and false abstention) is reported."),
    ("  - **compute** judge/detector agreement and error rate with intervals;",
     "  - **compute** the V2 grader's (detector's) agreement and error rate against your human labels and a labelled challenge set (fabricated claims, swapped citations, contradictions), with Wilson intervals. The automated **evaluation** judge (Cohere) is certified only in the final judge batch (D-10; [06 §8.4](06_RAG_PROJECT_AND_EVALUATION_PLAN.md#84-calibration-against-human-labels));"),
    ("- **Evidence:** an agreement report with a confidence interval, plus a list of the judge's systematic errors.",
     "- **Evidence:** an agreement report for the V2 grader with intervals and stated denominators, plus a list of its systematic errors.\n\n"
     f"> Revised 2026-10-08 (Codex M-06; learner decision D-10): V3 threshold claims need ≥ 15 unanswerables (≥ 5 in dev). V4 measures the in-pipeline grader against human labels in Phase 8; evaluation-judge certification moves to the final batch. See [corrections log]({LOG}#m-06)."),
])

# 04: V4 row (M-06)
edit("04_BOOK_TO_CODE_MAPPING.md", [
    ("| Two judges vs human labels; inter-judge agreement | 8.4 | U |",
     "| V2 grader vs human labels and a labelled challenge set (Phase 8, Wilson intervals); Cohere evaluation judge vs human and Codex labels only in the final judge batch (D-10; revised 2026-10-08, Codex M-06) | 8.4 | U |"),
])

# 03: metric map rows + 2x2 cell name (M-02 / M-06)
edit("03_RAG_CONCEPT_DEPENDENCY_MAP.md", [
    ("| gold answer; judge plus human spot-check |",
     "| gold answer; human labels (pilot) until the final judge batch, then the calibrated Cohere judge (D-10; 06 §8.4) |"),
    ("| `answerable` flag (≥ 6 unanswerable, Gate 3→4) |",
     "| `answerable` flag (≥ 6 unanswerable is the Gate 3→4 learning minimum; no threshold claim until ≥ 15 with ≥ 5 in dev) |"),
    ("The top-right cell would then hide retrieval failures.",
     "The bottom-left cell (CE@k = 0, answer correct) would then hide retrieval failures. (Corrected 2026-10-08 with the M-02 rewrite of this table; the earlier text named the wrong cell.)"),
])

# 08 + BACKBONE: DEC-3 split (Corpus H deferred by the learner) (B-01 / §L)
edit("08_GAP_ANALYSIS_AND_DECISIONS.md", [
    ("- [ ] DEC-3. Corpus T and H files are chosen, stored locally (not committed), hashed and frozen, and their snapshot manifests are created (D-17).",
     "- [ ] DEC-3. Corpus T files are chosen, stored locally (not committed), hashed and frozen, with snapshot manifests (D-17), before Phase 3. Corpus H is chosen and frozen later, before K1, and stays untouched until then (learner deferred the H choice, 2026-10-08)."),
])
