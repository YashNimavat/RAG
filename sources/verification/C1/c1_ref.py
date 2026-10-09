"""C1 reference implementation: page-level PyMuPDF extraction, the frozen-text snapshot (06 §5.3), page lookup,
an artifact inventory, and logged cleaning rules with full provenance.

This file IS a solution for labs/C1_parsing_lab.ipynb. The tutor shows it only after an attempt plus a hint (CR-04).
Names and formats follow 06 §2-§3 and §5.3 exactly: Page(doc_id, page, text, parser); pages joined with "\n";
page_table rows {page, doc_char_start, doc_char_end, text_sha256}; the snapshot_id recipe of 06 §5.3.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass

import pymupdf as fitz

PAGE_JOIN = "\n"
CLEANING_NONE = {"version": "none", "steps": []}


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Page:
    doc_id: str
    page: int        # 1-based PDF page
    text: str        # raw page.get_text(); v0: no cleaning
    parser: str      # "pymupdf <version>"


def parser_info() -> dict:
    """The manifest's parser block (06 §5.3)."""
    return {"backend": "pymupdf", "version": fitz.VersionBind, "call": "page.get_text()", "options": {}}


def load_pages(pdf_path: str, doc_id: str) -> list[Page]:
    with fitz.open(pdf_path) as d:
        return [Page(doc_id, i, p.get_text(), f"pymupdf {fitz.VersionBind}") for i, p in enumerate(d, 1)]


def build_page_table(page_texts: list[str]) -> tuple[str, list[dict]]:
    rows, pos = [], 0
    for i, t in enumerate(page_texts, 1):
        rows.append({"page": i, "doc_char_start": pos, "doc_char_end": pos + len(t), "text_sha256": sha256_hex(t)})
        pos += len(t) + len(PAGE_JOIN)
    return PAGE_JOIN.join(page_texts), rows


def snapshot_id(backend: str, version: str, options: dict, cleaning_version: str, doc_text_sha256: dict) -> str:
    """06 §5.3 'Exact snapshot_id formula', transcribed. "page_join=\\n" is a literal backslash + n."""
    parts = ["snapshot-v1", f"parser={backend}@{version}", "options=" + json.dumps(options, sort_keys=True),
             f"cleaning={cleaning_version}", "page_join=\\n"]
    parts += [f"{doc_id}:{doc_text_sha256[doc_id]}" for doc_id in sorted(doc_text_sha256)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def build_manifest(corpus: str, corpus_version: str, docs: list[dict], parser: dict, cleaning: dict,
                   created_utc: str) -> dict:
    """docs: [{doc_id, pdf_sha256, bytes, pages, doc_text_sha256, page_table}] (06 §5.3 field order)."""
    sid = snapshot_id(parser["backend"], parser["version"], parser["options"], cleaning["version"],
                      {d["doc_id"]: d["doc_text_sha256"] for d in docs})
    return {"snapshot_id": sid, "corpus": corpus, "corpus_version": corpus_version, "created_utc": created_utc,
            "parser": parser, "cleaning": cleaning, "encoding": "utf-8", "newline": "\n", "page_join": "\n",
            "docs": docs}


def validate_snapshot(manifest: dict, doc_texts: dict[str, str]) -> None:
    """Fail closed (06 §5.3 rule 4, structural part): raise ValueError on any mismatch."""
    hashes = {}
    for d in manifest["docs"]:
        text, rows = doc_texts[d["doc_id"]], d["page_table"]
        if sha256_hex(text) != d["doc_text_sha256"]:
            raise ValueError(f"{d['doc_id']}: doc_text_sha256 mismatch")
        if [r["page"] for r in rows] != list(range(1, len(rows) + 1)) or rows[0]["doc_char_start"] != 0:
            raise ValueError(f"{d['doc_id']}: pages must be 1..n and start at 0")
        for a, b in zip(rows, rows[1:]):
            if b["doc_char_start"] != a["doc_char_end"] + len(PAGE_JOIN):
                raise ValueError(f"{d['doc_id']} p.{b['page']}: start != previous end + len(page_join)")
        if rows[-1]["doc_char_end"] != len(text):
            raise ValueError(f"{d['doc_id']}: last doc_char_end != len(doc_text)")
        for r in rows:
            if sha256_hex(text[r["doc_char_start"]:r["doc_char_end"]]) != r["text_sha256"]:
                raise ValueError(f"{d['doc_id']} p.{r['page']}: text_sha256 mismatch")
        hashes[d["doc_id"]] = d["doc_text_sha256"]
    p = manifest["parser"]
    if snapshot_id(p["backend"], p["version"], p["options"], manifest["cleaning"]["version"], hashes) != manifest["snapshot_id"]:
        raise ValueError("snapshot_id does not match the recomputed recipe")


def page_of(doc_offset: int, page_table: list[dict]) -> tuple[int, int]:
    """Document offset -> (1-based page, page-relative offset). The join character after page p belongs to p."""
    starts = [r["doc_char_start"] for r in page_table]
    p = bisect.bisect_right(starts, doc_offset)
    return p, doc_offset - starts[p - 1]


# ----------------------------------------------------------------------------------------------- artifacts
LIGATURES = "ﬀﬁﬂﬃﬄﬅﬆ"
HYPHEN_BREAK = re.compile(r"([A-Za-z]+)-\n([a-z]+)")


def line_key(line: str) -> str:
    """A line's identity for the header/footer rule: stripped, digits masked (so 'Page 7' == 'Page 1')."""
    return re.sub(r"\d+", "#", line.strip())


def repeated_lines(page_texts: list[str]) -> tuple[int, dict[str, int]]:
    """Lines whose key appears on >= max(3, ceil(n_text_pages / 2)) pages. Returns (threshold, {key: pages})."""
    n_text = sum(1 for t in page_texts if t.strip())
    threshold = max(3, math.ceil(n_text / 2))
    c = Counter(k for t in page_texts for k in {line_key(x) for x in t.split("\n") if x.strip()})
    return threshold, {k: v for k, v in sorted(c.items()) if v >= threshold}


def artifact_counts(page_texts: list[str]) -> dict:
    lines = [m.group(0)[:-1] for t in page_texts for m in re.finditer(r"[^\n]*\n", t)]   # newline-terminated lines
    return {
        "pages": len(page_texts),
        "empty_pages": [i for i, t in enumerate(page_texts, 1) if not t.strip()],
        "hyphen_breaks": [(i, m.group(0)) for i, t in enumerate(page_texts, 1) for m in HYPHEN_BREAK.finditer(t)],
        "ligatures": sum(t.count(ch) for t in page_texts for ch in LIGATURES),
        "soft_hyphens": sum(t.count("\xad") for t in page_texts),
        "tabs": sum(t.count("\t") for t in page_texts),
        "double_newlines": sum(t.count("\n\n") for t in page_texts),
        "lines": len(lines),
        "lines_ending_space": sum(1 for ln in lines if ln.endswith(" ")),
        "non_ascii": dict(sorted(Counter(ch for t in page_texts for ch in t if ord(ch) > 127).items())),
    }


# ------------------------------------------------------------------------------------- logged cleaning
def plan_edits(doc_id: str, page_texts: list[str]) -> list[dict]:
    """Rules (each edit is logged; none is applied in v0):
    R1 header_footer: drop a whole line (with its "\n") whose line_key is in repeated_lines;
    R2 dehyphenate: "frag-\nment" -> "fragment" ONLY if "fragment" occurs elsewhere in the document;
    R3 ligature: one ligature character -> its NFKC letters (U+FB01 -> "fi")."""
    import unicodedata
    _, rep = repeated_lines(page_texts)
    vocab = Counter(w.lower() for t in page_texts for w in re.findall(r"[A-Za-z]+", t))
    edits = []
    for pno, t in enumerate(page_texts, 1):
        for m in re.finditer(r"[^\n]*\n|[^\n]+$", t):          # each line WITH its "\n"
            if m.group(0).strip() and line_key(m.group(0)) in rep:
                edits.append({"doc_id": doc_id, "page": pno, "rule": "R1_header_footer", "start": m.start(),
                              "end": m.end(), "before": m.group(0), "after": ""})
        for m in HYPHEN_BREAK.finditer(t):
            joined = (m.group(1) + m.group(2)).lower()
            if vocab[joined] > 0:                           # minimal edit: delete only "-\n", letters keep offsets
                edits.append({"doc_id": doc_id, "page": pno, "rule": "R2_dehyphenate", "start": m.end(1),
                              "end": m.end(1) + 2, "before": "-\n", "after": ""})
        for i, ch in enumerate(t):
            if ch in LIGATURES:
                edits.append({"doc_id": doc_id, "page": pno, "rule": "R3_ligature", "start": i, "end": i + 1,
                              "before": ch, "after": unicodedata.normalize("NFKC", ch)})
    edits.sort(key=lambda e: (e["page"], e["start"]))
    for e in edits:                                         # a short raw snippet for the human-readable log
        t = page_texts[e["page"] - 1]
        e["context"] = t[max(0, e["start"] - 12):e["end"] + 12]
    for a, b in zip(edits, edits[1:]):
        if a["page"] == b["page"] and b["start"] < a["end"]:
            raise ValueError(f"overlapping edits on page {a['page']}: {a['rule']} and {b['rule']}")
    return edits


def apply_edits(page_text: str, edits: list[dict]) -> tuple[str, list[int]]:
    """Return (cleaned text, src) where src[i] is the RAW page offset of cleaned character i
    (an inserted character maps to the start of the raw span it replaced). Every raw character is either
    copied (and mapped) or recorded in an edit's 'before': provenance is kept for every character."""
    out, src, pos = [], [], 0
    for e in sorted(edits, key=lambda e: e["start"]):
        out.append(page_text[pos:e["start"]])
        src.extend(range(pos, e["start"]))
        out.append(e["after"])
        src.extend([e["start"]] * len(e["after"]))
        pos = e["end"]
    out.append(page_text[pos:])
    src.extend(range(pos, len(page_text)))
    return "".join(out), src


def undo_edits(cleaned: str, src: list[int], edits: list[dict], raw_len: int) -> str:
    """Rebuild the raw page text from the cleaned text + map + log (the provenance round trip)."""
    raw = [None] * raw_len
    for i, j in enumerate(src):
        if raw[j] is None:
            raw[j] = cleaned[i]
    for e in edits:
        raw[e["start"]:e["end"]] = list(e["before"])
    if any(c is None for c in raw):
        raise ValueError("some raw character has no provenance")
    return "".join(raw)


def extract_columns(page) -> str:
    """Two-column fix (a parser OPTION, so a new snapshot): left half top to bottom, then right half."""
    r = page.rect
    left = page.get_text(clip=fitz.Rect(r.x0, r.y0, r.x0 + r.width / 2, r.y1))
    right = page.get_text(clip=fitz.Rect(r.x0 + r.width / 2, r.y0, r.x1, r.y1))
    return left + right
