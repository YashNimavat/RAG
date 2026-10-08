"""Round-2 residual edits by the orchestrator (2026-10-08), after the R-01..R-07 workflow.
Run from the workspace root: python -I sources/verification/corrections/round2_residual_edits.py
Each replacement must match exactly once; existing line endings are preserved."""
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
            print("!! count", n, fn, ascii(a[:70]))
            continue
        t = t.replace(a, b)
        print("ok", fn, ascii(a[:60]))
    if crlf:
        t = t.replace("\n", "\r\n")
    p.write_bytes(t.encode("utf-8"))


edit("06_RAG_PROJECT_AND_EVALUATION_PLAN.md", [
    # R-02: real snapshot_id (computed by contracts_check.py with the exact recipe below)
    ('"snapshot_id": "<12 hex; exact formula below the manifest>",',
     '"snapshot_id": "ea07572562ac",'),
    # R-02: remove the \\n ambiguity in the recipe
    ('         f"cleaning={cleaning_version}", "page_join=\\\\n"]',
     '         f"cleaning={cleaning_version}", "page_join=\\\\n"]   # literal backslash + "n" (2 characters), NOT a newline'),
    ("Any change to the parser, its version or options, the cleaning version, or any document's text therefore gives a new id. The `snap()` helper",
     "Any change to the parser, its version or options, the cleaning version, or any document's text therefore gives a new id. "
     "For Corpus D (PyMuPDF 1.26.7, options `{}`, cleaning `none`) the recipe gives **`ea07572562ac`**; computed 2026-10-08 by `sources/verification/corrections/contracts_check.py`, which executes this exact block. "
     "Reading `\\\\n` as a real newline gives a different id, which is why the comment above fixes it.\n\n"
     "**Snapshot text storage [N].** `<snapshot_id>/<doc_id>.txt` holds the document text, pages joined with `page_join`. Each page text is the slice `doc_text[doc_char_start:doc_char_end]` of the page table, and its `text_sha256` is checked on that slice. A shifted table therefore cannot keep a page's hash, and the structural checks in rule 4 reject it in any case.\n\n"
     f"> Revised 2026-10-08 (Codex re-review R-02): real Corpus D snapshot_id, unambiguous recipe, page-text storage stated. See [corrections log]({LOG}#r-02).\n\n"
     "The `snap()` helper"),
    # R-02: negative tests promised by rule 4 are now in the §9.6 sketch
    ("def test_per_page_and_cross_page_chunks_score_identically(p2_item, p12_13_item, per_page_run, cross_page_run):",
     "def test_wrong_manifest_digest_is_rejected(eval_header, manifest_bytes, page_texts):   # R-02\n"
     "    with pytest.raises(SnapshotMismatch):\n"
     "        validate_binding({**eval_header, \"snapshot_manifest_sha256\": \"deliberately-wrong\"}, manifest_bytes, page_texts)\n\n"
     "def test_shifted_page_table_is_rejected():                                            # R-02\n"
     "    pages = [\"abc\", \"def\"]                                       # doc text \"abc\\ndef\"; page 2 = [4, 7)\n"
     "    header, manifest_bytes = make_binding(pages, shift_page2_by=+1)  # page 2 claimed as [5, 8): hash and length unchanged\n"
     "    with pytest.raises(SnapshotMismatch):\n"
     "        validate_binding(header, manifest_bytes, pages)          # valid table maps page-2 [0,1) -> [4,5) = \"d\"\n\n"
     "def test_per_page_and_cross_page_chunks_score_identically(p2_item, p12_13_item, per_page_run, cross_page_run):"),
    # pre-existing table rendering bug in the M-02 metric table: escape pipes inside code spans
    ("| **Precision@k** | `|{i ≤ k: rel(c_i) = 1}| / k` |",
     "| **Precision@k** | `\\|{i ≤ k: rel(c_i) = 1}\\| / k` |"),
    ("| **Context precision@k** (rank-aware) | `Σ_{i=1..k} P@i · rel(c_i) / |{i ≤ k: rel(c_i)=1}|` (0 if no relevant chunk) |",
     "| **Context precision@k** (rank-aware) | `Σ_{i=1..k} P@i · rel(c_i) / \\|{i ≤ k: rel(c_i)=1}\\|` (0 if no relevant chunk) |"),
])
