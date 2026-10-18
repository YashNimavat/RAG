"""parse_quality_check: which pages of MY PDFs did the parser get wrong, and do my questions touch them?

What this is: a command-line tool (also importable) that extracts your documents exactly as the course's v0 loader does
(PyMuPDF `page.get_text()`, no options, no cleaning, 1-based pages joined with "\\n"), computes per-page signals, and
writes a Markdown report:
  0 Snapshot          the would-be snapshot_id (06 §5.3 recipe: options {}, cleaning "none")
  1 Corpus summary    documents, pages, characters, images, flagged pages
  2 Per document      page table, hashes, repeated lines, hyphens, ligatures, order, tables, page breaks
  3 Flagged pages     each flagged page with its reasons; pages with notes only (hyphens, ligatures, equations, cuts)
  4 Hand-check sample a stratified sample (document x flag) to read side by side with the page image (--html)
  5 Questions         where each question's `expect` text sits (offset -> page through the page table); questions on
                      flagged pages; expect texts found on no page
  6 Checklist         PQ1-PQ12 with a verdict (✓ fine, ✗ problem found, ? check by hand), the evidence, how to check
  7 Recommendation    first matching rule wins (see recommend())
Also --pages-jsonl: one row per page with every signal (a short snippet, never the page text).
What this is not: a measure of harm. A flag shows RISK. Whether a flagged page hurts you shows only in retrieval
metrics (Hit@k, CE@k) on the questions whose expect text sits on flagged pages, compared with the rest. Answer quality
is a separate measurement again.

Per-page signals (research C1 §8):
  text vs images   chars; images (get_images); image area share (get_image_info). Flag: fewer than 50 non-space-stripped
                   characters and >= 1 image -> image-only (needs OCR or captioning); no text and no image -> blank
  non-word share   share of tokens (edge punctuation removed) with no letter, or with a character outside [A-Za-z0-9-']
                   after digits are removed. Flag: above the document's median + 3 x MAD over its text pages, and at
                   least 0.05 above the median (a floor, so a document whose MAD is 0 does not flag every page); needs
                   >= 3 text pages
  encoding         U+FFFD and "(cid:N)" strings. Flag: any
  repeated lines   rule R1 (digits masked; a line on >= max(3, ceil(n/2)) text pages). Flag: header/footer (shown,
                   never deleted)
  line-end hyphens [A-Za-z]-\\n[a-z]; split by R2 into "joined form occurs elsewhere in the document" vs not (a note)
  ligatures/NFKC   U+FB00-FB06 count; characters NFKC would change and the length delta (a note; never NFKC in place)
  columns, order   long text blocks (>= 40 characters) in both halves = two-column; right->left jumps: a body line
                   starting in the right half followed by one starting in the left half, top and bottom 10% excluded.
                   Flag: jumps >= 2
  tables           find_tables() (ruling lines): count, rows x columns, empty-cell share. Flag: table found; or
                   "suspected flattened table": no table found and >= 4 lines that hold a number alone
  equation-like    lines with > 30% non-alphanumeric, non-space characters (a note)
  page-break cut   the page does not end in . ! ? : " ) ' and the next page starts lower-case (a note: a C2 problem)
  two parsers      --second-parser pdfplumber|pypdf: word-set Jaccard per page. Flag: < 0.9. Used only if the
                   library is importable; otherwise the report says "not installed, skipped"

No API calls, no network. Standard library + pymupdf (pinned 1.26.7 in this project); numpy only for medians.
.txt and .md files pass through as one page each (no parser; no image, table or order signals).

Usage, from rag_learning/:
    uv run python study/tools/parse_quality_check.py --docs my_pdfs/ --questions q.jsonl --report parse_report.md
    uv run python study/tools/parse_quality_check.py --docs a.pdf b.pdf --doc-ids a,b --questions q.jsonl \\
        --sample 8 --html sample.html --pages-jsonl pages.jsonl --report parse_report.md
Questions: .jsonl with {"q": "...", "expect": "text on the right page" or ["text", "other text"], "id": "..." (optional)}.
"expect" is matched case-insensitively with whitespace normalised (a line break counts as a space).

Import:
    from parse_quality_check import run_check, render_report, HOW
    res = run_check(["doc.pdf"], "questions.jsonl")
    print(render_report(res))
"""
from __future__ import annotations

import argparse
import base64
import bisect
import hashlib
import html
import importlib.util
import json
import math
import re
import shlex
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pymupdf

pymupdf.no_recommend_layout()          # the pymupdf_layout advice cannot be followed next to the 1.26.7 pin

EXTS = (".pdf", ".txt", ".md")
OK, BAD, ASK = "✓", "✗", "?"
PAGE_JOIN = "\n"
LIGATURES = "\ufb00\ufb01\ufb02\ufb03\ufb04\ufb05\ufb06"
HYPHEN_BREAK = re.compile(r"([A-Za-z]+)-\n([a-z]+)")        # = c1_ref.HYPHEN_BREAK
CID = re.compile(r"\(cid:\d+\)")
ENDS = '.!?:")\''
PURE_NUMBER = re.compile(r"^[-+±]?\d[\d.,%]*$")
MIN_TEXT = 50              # fewer characters than this + an image = image-only
JUMP_FLAG = 2              # right->left jumps on a page that raise a flag
FLAT_NUM_LINES = 4         # lines holding a number alone, with no table found = suspected flattened table
EQ_SHARE = 0.30            # an equation-like line has more than this share of symbols
NONWORD_FLOOR = 0.05       # minimum distance above the median for a non-word flag
JACCARD_FLAG = 0.9
LONG_BLOCK = 40            # characters in a text block that counts towards "two columns"
SNIPPET = 60

RISK_FLAGS = ("image-only", "blank", "encoding", "reading order", "table found", "suspected flattened table",
              "non-word outlier", "header/footer", "parsers disagree")


# ---------------------------------------------------------------------------------------------------------------- input
def load_documents(paths, doc_ids=None):
    """Files or folders (.pdf, .txt, .md; folders are searched recursively, in sorted order). Pages are 1-based."""
    files, seen = [], set()
    for p in map(Path, paths):
        if p.is_dir():
            found = sorted(q for q in p.rglob("*") if q.is_file() and q.suffix.lower() in EXTS)
        elif p.is_file():
            if p.suffix.lower() not in EXTS:
                raise ValueError(f"unsupported file type: {p.name} (use .pdf, .txt or .md)")
            found = [p]
        else:
            raise FileNotFoundError(f"no such file or folder: {p}")
        for f in found:
            if f.resolve() not in seen:
                seen.add(f.resolve())
                files.append(f)
    if not files:
        raise ValueError("no .pdf, .txt or .md documents found")
    if doc_ids and len(doc_ids) != len(files):
        raise ValueError(f"--doc-ids gives {len(doc_ids)} ids for {len(files)} documents")
    docs = []
    for n, f in enumerate(files):
        is_pdf = f.suffix.lower() == ".pdf"
        if is_pdf:
            with pymupdf.open(f) as d:
                pages = [pg.get_text() for pg in d]                      # v0: raw get_text(), no options, no strip
        else:
            pages = [f.read_text(encoding="utf-8", errors="replace")]
        docs.append({"doc_id": doc_ids[n] if doc_ids else f.stem, "name": f.name, "path": str(f), "is_pdf": is_pdf,
                     "pages": pages, "parser": f"pymupdf {pymupdf.VersionBind}" if is_pdf else "text file (no parser)"})
    if len({d["doc_id"] for d in docs}) != len(docs):
        raise ValueError("two documents have the same id; pass --doc-ids")
    return docs


def load_questions(source):
    """A .jsonl path or a list of dicts. Returns [{"id", "q", "expect": [str, ...] or None}]."""
    if source is None:
        return []
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"questions file not found: {source}")
        items = []
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path.name}, line {n}: not valid JSON ({e})") from None
    else:
        items = list(source)
    out = []
    for n, it in enumerate(items, 1):
        it = dict(it)
        if not str(it.get("q", "")).strip():
            raise ValueError(f"question {n}: missing \"q\"")
        exp = it.get("expect") or None
        if isinstance(exp, str):
            exp = [exp]
        out.append({"id": str(it.get("id") or f"Q{n}"), "q": str(it["q"]), "expect": exp})
    return out


# ---------------------------------------------------------------------------------------------------------------- page table
def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_page_table(page_texts):
    """doc_text = "\\n".join(pages); rows {page, doc_char_start, doc_char_end, text_sha256}; start = previous end + 1."""
    rows, pos = [], 0
    for i, t in enumerate(page_texts, 1):
        rows.append({"page": i, "doc_char_start": pos, "doc_char_end": pos + len(t), "text_sha256": sha256_hex(t)})
        pos += len(t) + len(PAGE_JOIN)
    return PAGE_JOIN.join(page_texts), rows


def page_of(doc_offset, rows):
    """Document offset -> (1-based page, page offset). The join character after page p belongs to page p."""
    starts = [r["doc_char_start"] for r in rows]
    p = bisect.bisect_right(starts, doc_offset)
    return p, doc_offset - starts[p - 1]


def snapshot_id(backend, version, options, cleaning_version, doc_text_sha256):
    """06 §5.3 recipe (= c1_ref.snapshot_id). "page_join=\\n" is a literal backslash + n."""
    parts = ["snapshot-v1", f"parser={backend}@{version}", "options=" + json.dumps(options, sort_keys=True),
             f"cleaning={cleaning_version}", "page_join=\\n"]
    parts += [f"{d}:{doc_text_sha256[d]}" for d in sorted(doc_text_sha256)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------------------------------------------- signals
def line_key(line):
    return re.sub(r"\d+", "#", line.strip())


def repeated_lines(page_texts):
    """R1 (= c1_ref.repeated_lines): keys on >= max(3, ceil(n_text_pages / 2)) pages -> (threshold, {key: pages})."""
    n_text = sum(1 for t in page_texts if t.strip())
    threshold = max(3, math.ceil(n_text / 2))
    c = Counter(k for t in page_texts for k in {line_key(x) for x in t.split("\n") if x.strip()})
    return threshold, {k: v for k, v in sorted(c.items()) if v >= threshold}


def line_starts(page):
    """(x0, y0, text) of every text line, in the order PyMuPDF's default extraction walks them (= c1_kit_measure)."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"]).strip()
            if t:
                out.append((ln["bbox"][0], ln["bbox"][1], t))
    return out


def rl_jumps(page):
    """Right-to-left jumps among body lines (top and bottom 10% excluded) (= c1_kit_measure.rl_jumps)."""
    mid, h = page.rect.width / 2, page.rect.height
    ls = [l for l in line_starts(page) if 0.1 * h < l[1] < 0.9 * h]
    return sum(1 for a, b in zip(ls, ls[1:]) if a[0] >= mid and b[0] < mid)


def two_columns(page):
    mid = page.rect.width / 2
    sides = set()
    for b in page.get_text("blocks"):
        if b[6] == 0 and len(b[4].strip()) >= LONG_BLOCK:
            sides.add("R" if b[0] >= mid else "L")
    return sides == {"L", "R"}


def nfkc_changes(text):
    ch = [c for c in text if unicodedata.normalize("NFKC", c) != c]
    return len(ch), len(unicodedata.normalize("NFKC", text)) - len(text)


def nonword_stats(text):
    toks = [t.strip(".,;:!?()[]{}\"'`") for t in text.split()]
    toks = [t for t in toks if t]
    if not toks:
        return None, None
    bad = sum(1 for t in toks if not re.search(r"[A-Za-z]", t) or re.search(r"[^A-Za-z0-9\-']", re.sub(r"\d", "", t)))
    words = [t for t in toks if re.search(r"[A-Za-z]", t)]
    return bad / len(toks), (sum(len(w) for w in words) / len(words) if words else None)


def equation_lines(text):
    n = 0
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for ln in lines:
        chars = [c for c in ln if not c.isspace()]
        if chars and sum(1 for c in chars if not c.isalnum()) / len(chars) > EQ_SHARE:
            n += 1
    return n, len(lines)


def table_info(page):
    out = []
    for t in page.find_tables().tables:
        cells = [c for row in t.extract() for c in row]
        empty = sum(1 for c in cells if c is None or not str(c).strip())
        out.append({"rows": t.row_count, "cols": t.col_count, "empty_share": round(empty / len(cells), 3) if cells else None})
    return out


def second_parser_pages(name, path, n_pages):
    """Per-page text from pdfplumber or pypdf, or None if the library is not importable."""
    if name in (None, "none") or importlib.util.find_spec(name) is None:
        return None
    if name == "pdfplumber":
        import pdfplumber
        with pdfplumber.open(path) as d:
            return [(p.extract_text() or "") for p in d.pages[:n_pages]]
    from pypdf import PdfReader
    return [(p.extract_text() or "") for p in PdfReader(path).pages[:n_pages]]


def jaccard(a, b):
    A, B = set(a.lower().split()), set(b.lower().split())
    return 1.0 if not A and not B else len(A & B) / len(A | B)


def snippet(t):
    s = " ".join(t.split())
    return s[:SNIPPET] + ("…" if len(s) > SNIPPET else "")


def page_signals(doc, second=None):
    """One dict per page: every signal of the table above. Flags are set later (they need document statistics)."""
    texts = doc["pages"]
    vocab = Counter(w.lower() for t in texts for w in re.findall(r"[A-Za-z]+", t))
    thr, rep = repeated_lines(texts)
    rows = []
    pdf = pymupdf.open(doc["path"]) if doc["is_pdf"] else None
    try:
        for i, t in enumerate(texts, 1):
            pg = pdf[i - 1] if pdf else None
            nw, mwl = nonword_stats(t)
            hy = [(m.group(1), m.group(2)) for m in HYPHEN_BREAK.finditer(t)]
            eq, n_lines = equation_lines(t)
            keys = {line_key(x) for x in t.split("\n") if x.strip()}
            r = {"doc": doc["name"], "doc_id": doc["doc_id"], "page": i, "chars": len(t), "text_chars": len(t.strip()),
                 "lines": n_lines, "images": 0, "image_area_share": 0.0, "nonword_share": None if nw is None else round(nw, 4),
                 "mean_word_len": None if mwl is None else round(mwl, 2), "fffd": t.count("\ufffd"), "cid": len(CID.findall(t)),
                 "repeated_lines": sorted(k for k in keys if k in rep),
                 "hyphen_breaks": [f"{a}-|{b}" for a, b in hy],
                 "hyphen_r2": [f"{a}-|{b}" for a, b in hy if vocab[(a + b).lower()] > 0],
                 "ligatures": sum(t.count(c) for c in LIGATURES), "nfkc_changes": nfkc_changes(t)[0], "nfkc_delta": nfkc_changes(t)[1],
                 "two_columns": False, "rl_jumps": 0, "tables": [], "number_lines": sum(1 for ln in t.split("\n") if PURE_NUMBER.match(ln.strip())),
                 "equation_lines": eq, "ends_open": False, "cut_to_next": False, "jaccard": None, "snippet": snippet(t)}
            if pg is not None:
                r["images"] = len(pg.get_images())
                area = abs(pg.rect)
                ia = sum(abs(pymupdf.Rect(x["bbox"]) & pg.rect) for x in pg.get_image_info())
                r["image_area_share"] = round(min(1.0, ia / area), 3) if area else 0.0
                r["two_columns"] = two_columns(pg)
                r["rl_jumps"] = rl_jumps(pg)
                r["tables"] = table_info(pg)
            if i < len(texts):
                end = t.rstrip()
                r["ends_open"] = bool(end) and end[-1] not in ENDS
                r["cut_to_next"] = r["ends_open"] and texts[i].lstrip()[:1].islower()
            if second is not None:
                r["jaccard"] = round(jaccard(t, second[i - 1]), 4) if i - 1 < len(second) else 0.0
            rows.append(r)
    finally:
        if pdf:
            pdf.close()
    return rows, thr, rep


def set_flags(rows):
    """Flags (risk) and notes (reported only) per page, using the document's own non-word statistics."""
    vals = [r["nonword_share"] for r in rows if r["nonword_share"] is not None and r["text_chars"] >= MIN_TEXT]
    stats = None
    if len(vals) >= 3:
        med = float(np.median(vals))
        mad = float(np.median(np.abs(np.array(vals) - med)))
        stats = {"median": round(med, 4), "mad": round(mad, 4), "limit": round(max(med + 3 * mad, med + NONWORD_FLOOR), 4)}
    for r in rows:
        f, n = [], []
        if r["text_chars"] < MIN_TEXT and r["images"] >= 1:
            f.append("image-only")
        elif r["text_chars"] == 0 and r["images"] == 0:
            f.append("blank")
        if r["fffd"] or r["cid"]:
            f.append("encoding")
        if r["repeated_lines"]:
            f.append("header/footer")
        if r["rl_jumps"] >= JUMP_FLAG:
            f.append("reading order")
        if r["tables"]:
            f.append("table found")
        elif r["number_lines"] >= FLAT_NUM_LINES:
            f.append("suspected flattened table")
        if stats and r["nonword_share"] is not None and r["text_chars"] >= MIN_TEXT and r["nonword_share"] > stats["limit"]:
            f.append("non-word outlier")
        if r["jaccard"] is not None and r["jaccard"] < JACCARD_FLAG:
            f.append("parsers disagree")
        if r["hyphen_breaks"]:
            n.append(f"{len(r['hyphen_breaks'])} line-end hyphen(s), {len(r['hyphen_r2'])} R2 candidate(s)")
        if r["ligatures"] or r["nfkc_delta"]:
            n.append(f"{r['ligatures']} ligature(s), NFKC delta {r['nfkc_delta']:+d}")
        if r["equation_lines"]:
            n.append(f"{r['equation_lines']} equation-like line(s)")
        if r["cut_to_next"]:
            n.append("sentence cut at the page break")
        if r["two_columns"]:
            n.append("two columns")
        r["flags"], r["notes"] = f, n
    return stats


# ---------------------------------------------------------------------------------------------------------------- questions
def norm_map(text):
    """Lower-case, whitespace runs -> one space; returns (normalised text, raw offset of each normalised character)."""
    out, src, prev_space = [], [], False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_space:
                out.append(" ")
                src.append(i)
            prev_space = True
            continue
        prev_space = False
        for c in ch.lower():
            out.append(c)
            src.append(i)
    return "".join(out), src


def cleaned_map(text, keep_hyphen):
    """A probe only (never a snapshot): ligatures decomposed, line-end hyphens joined ("-\\n" -> "" or -> "-")."""
    out, src, i = [], [], 0
    while i < len(text):
        ch = text[i]
        if ch in LIGATURES:
            for c in unicodedata.normalize("NFKC", ch):
                out.append(c)
                src.append(i)
            i += 1
            continue
        if text.startswith("-\n", i) and i > 0 and text[i - 1].isalpha() and i + 2 < len(text) and text[i + 2].islower():
            if keep_hyphen:
                out.append("-")
                src.append(i)
            i += 2
            continue
        out.append(ch)
        src.append(i)
        i += 1
    return "".join(out), src


def find_all(hay, needle):
    pos, out = 0, []
    while needle:
        j = hay.find(needle, pos)
        if j < 0:
            break
        out.append(j)
        pos = j + len(needle)
    return out


def locate_questions(qs, docs, page_rows):
    """For each expect text: every (doc, page) it sits on; and whether a cleaned probe would find a missing one."""
    prepared = []
    for d in docs:
        nt, src = norm_map(d["doc_text"])
        probes = []
        for keep in (False, True):
            ct, csrc = cleaned_map(d["doc_text"], keep)
            nct, nsrc = norm_map(ct)
            probes.append((nct, [csrc[j] for j in nsrc]))
        prepared.append((d, nt, src, probes))
    out = []
    for q in qs:
        items = []
        for e in q["expect"] or []:
            ne = " ".join(e.split()).lower()
            hits, probe_hits = [], []
            for d, nt, src, probes in prepared:
                for j in find_all(nt, ne):
                    a, b = src[j], src[j + len(ne) - 1]
                    p1, p2 = page_of(a, d["rows"])[0], page_of(b, d["rows"])[0]
                    hits.append({"doc": d["name"], "pages": list(range(p1, p2 + 1)), "doc_offset": a})
                if not hits:
                    for nct, cmap in probes:
                        for j in find_all(nct, ne):
                            a = cmap[j]
                            probe_hits.append({"doc": d["name"], "pages": [page_of(a, d["rows"])[0]], "doc_offset": a})
                        if probe_hits:
                            break
            items.append({"expect": e, "hits": hits, "after_cleaning": probe_hits})
        flagged = []
        for it in items:
            for h in it["hits"]:
                for p in h["pages"]:
                    fl = page_rows[(h["doc"], p)]["flags"]
                    if fl and (h["doc"], p, tuple(fl)) not in flagged:
                        flagged.append((h["doc"], p, tuple(fl)))
        out.append({**q, "items": items, "flagged": [{"doc": a, "page": p, "flags": list(f)} for a, p, f in flagged],
                    "not_found": [it["expect"] for it in items if not it["hits"]],
                    "found_after_cleaning": [it["expect"] for it in items if not it["hits"] and it["after_cleaning"]]})
    return out


# ---------------------------------------------------------------------------------------------------------------- sample
def stratified_sample(rows, n):
    """Strata = (document, first flag or 'no flag'); round-robin over sorted strata; inside a stratum a fixed
    pseudo-random order (sha256 of 'doc|page'). Deterministic."""
    strata = {}
    for r in rows:
        strata.setdefault((r["doc"], r["flags"][0] if r["flags"] else "no flag"), []).append(r)
    for k in strata:
        strata[k].sort(key=lambda r: hashlib.sha256(f"{r['doc']}|{r['page']}".encode()).hexdigest())
    keys = sorted(strata, key=lambda k: (k[1] == "no flag", k))           # flagged strata first
    picked, depth = [], 0
    while len(picked) < min(n, len(rows)):
        for k in keys:
            if depth < len(strata[k]) and len(picked) < n:
                picked.append((strata[k][depth], k[1]))
        depth += 1
    return sorted(({"doc": r["doc"], "page": r["page"], "stratum": s} for r, s in picked), key=lambda x: (x["doc"], x["page"]))


# ---------------------------------------------------------------------------------------------------------------- the check
def run_check(docs, questions=None, sample=8, second_parser="none", doc_ids=None, command=None):
    docs = load_documents(docs, doc_ids) if not (docs and isinstance(docs[0], dict)) else docs
    qs = load_questions(questions)
    sp_status = "not used"
    if second_parser not in (None, "none"):
        sp_status = "used" if importlib.util.find_spec(second_parser) is not None else "not installed, skipped"
    all_rows, per_doc = [], []
    for d in docs:
        d["doc_text"], d["rows"] = build_page_table(d["pages"])
        second = second_parser_pages(second_parser, d["path"], len(d["pages"])) if (d["is_pdf"] and sp_status == "used") else None
        rows, thr, rep = page_signals(d, second)
        stats = set_flags(rows)
        rt = all(d["doc_text"][r["doc_char_start"]:r["doc_char_end"]] == t for r, t in zip(d["rows"], d["pages"]))
        starts_ok = all(page_of(r["doc_char_start"], d["rows"]) == (r["page"], 0) for r in d["rows"])
        per_doc.append({"name": d["name"], "doc_id": d["doc_id"], "parser": d["parser"], "is_pdf": d["is_pdf"], "pages": len(d["pages"]),
                        "page_chars": sum(len(t) for t in d["pages"]), "doc_text_chars": len(d["doc_text"]),
                        "utf8_bytes": len(d["doc_text"].encode("utf-8")), "doc_text_sha256": sha256_hex(d["doc_text"]),
                        "rows": [(r["page"], r["doc_char_start"], r["doc_char_end"]) for r in d["rows"]],
                        "page_numbers": [r["page"] for r in d["rows"]], "round_trip": rt and starts_ok,
                        "repeat_threshold": thr, "repeated": rep, "nonword": stats,
                        "images": sum(r["images"] for r in rows), "flagged": sum(1 for r in rows if r["flags"]),
                        "hyphens": sum(len(r["hyphen_breaks"]) for r in rows), "hyphen_r2": sum(len(r["hyphen_r2"]) for r in rows),
                        "ligatures": sum(r["ligatures"] for r in rows), "nfkc_changes": nfkc_changes(d["doc_text"])[0],
                        "nfkc_delta": nfkc_changes(d["doc_text"])[1], "max_jumps": max((r["rl_jumps"] for r in rows), default=0),
                        "two_col_pages": sum(r["two_columns"] for r in rows), "tables": sum(len(r["tables"]) for r in rows),
                        "suspected_tables": sum("suspected flattened table" in r["flags"] for r in rows),
                        "equation_lines": sum(r["equation_lines"] for r in rows),
                        "ends_open": sum(r["ends_open"] for r in rows), "cuts": sum(r["cut_to_next"] for r in rows),
                        "fffd": sum(r["fffd"] for r in rows), "cid": sum(r["cid"] for r in rows)})
        all_rows.extend(rows)
    page_rows = {(r["doc"], r["page"]): r for r in all_rows}
    located = locate_questions(qs, docs, page_rows)
    sid = snapshot_id("pymupdf", pymupdf.VersionBind, {}, "none", {d["doc_id"]: d["doc_text_sha256"] for d in per_doc})
    res = {"command": command, "settings": {"pymupdf": pymupdf.VersionBind, "call": "page.get_text()", "options": {},
                                            "cleaning": "none", "sample": sample, "second_parser": second_parser or "none",
                                            "second_parser_status": sp_status},
           "docs": per_doc, "pages": all_rows, "snapshot_id": sid, "questions": located,
           "sample": stratified_sample(all_rows, sample)}
    res["checklist"] = checklist(res)
    res["recommendations"] = recommend(res)
    res["recommendation"] = res["recommendations"][0]
    return res


# ---------------------------------------------------------------------------------------------------------------- checklist
HOW = {
    "PQ1": "Count characters and images per page: fewer than 50 characters with an image means image-only (OCR or "
           "captioning needed); no text and no image means blank. Open each such page and decide if text was expected.",
    "PQ2": "Search the extracted text for U+FFFD and \"(cid:\" strings; any hit means the font has no usable Unicode map.",
    "PQ3": "Build the page table (start = previous end + 1), check that page numbers run 1..n and that "
           "doc_text[start:end] equals each page's text.",
    "PQ4": "List lines that repeat on at least max(3, ceil(n/2)) pages with digits masked (R1); open two of those pages "
           "and mark each line as noise or a real heading. Never delete them from the snapshot.",
    "PQ5": "For each line-end hyphen, check whether the joined word occurs elsewhere in the document (R2 candidate) "
           "or not (most likely a real compound such as well-being).",
    "PQ6": "Count ligatures (U+FB00-FB06) and the characters NFKC would change; any non-zero delta means every later "
           "offset would move, so never normalise the snapshot in place.",
    "PQ7": "Count right-to-left jumps between body lines; on pages with 2 or more, open the page image and read the "
           "first lines of the extracted text in order.",
    "PQ8": "List find_tables() results and pages with many lines that hold a number alone; compare one table with the "
           "rendered page (the --html page) row by row.",
    "PQ9": "Count pages with images; for each question, ask whether its answer is in a figure, which the text "
           "extractor cannot see.",
    "PQ10": "Locate each expect text with the page table (offset to page) and count the questions that sit on flagged "
            "pages, plus the expect texts found on no page.",
    "PQ11": "Open the --html page and read each sampled page next to its image; note every word that is missing, "
            "merged or out of order.",
    "PQ12": "Record the snapshot_id (06 §5.3 recipe) with the report, so a later run can tell whether the text changed.",
}


def _pages(rows, pred, n=10):
    xs = [f"{r['doc']} p.{r['page']}" for r in rows if pred(r)]
    return ", ".join(xs[:n]) + (f" … (+{len(xs) - n})" if len(xs) > n else "")


def checklist(res):
    rows, docs, qs = res["pages"], res["docs"], res["questions"]
    items = []

    def add(cid, check, verdict, evidence):
        items.append({"id": cid, "check": check, "verdict": verdict, "evidence": evidence, "how": HOW[cid]})

    img = [r for r in rows if "image-only" in r["flags"]]
    blank = [r for r in rows if "blank" in r["flags"]]
    add("PQ1", "Every page has a text layer", BAD if img or blank else OK,
        (f"image-only: {_pages(img, lambda r: True) or 'none'}; blank: {_pages(blank, lambda r: True) or 'none'}" if img or blank
         else f"all {len(rows)} pages have text"))
    enc = [r for r in rows if "encoding" in r["flags"]]
    add("PQ2", "No encoding failures (U+FFFD, (cid:…))", BAD if enc else OK,
        f"U+FFFD {sum(r['fffd'] for r in rows)}, (cid:…) {sum(r['cid'] for r in rows)}" + (f" on {_pages(enc, lambda r: True)}" if enc else ""))
    ok3 = all(d["round_trip"] and d["page_numbers"] == list(range(1, d["pages"] + 1)) for d in docs)
    add("PQ3", "Pages are 1-based and every page round-trips through the page table", OK if ok3 else BAD,
        "; ".join(f"{d['name']}: pages 1–{d['pages']}, round trip {'yes' if d['round_trip'] else 'NO'}" for d in docs))
    rep = [(d["name"], k, v) for d in docs for k, v in d["repeated"].items()]
    add("PQ4", "Repeated header/footer lines are listed and each is confirmed as noise or a real heading", ASK if rep else OK,
        ("; ".join(f"{n}: \"{k}\" on {v} pages" for n, k, v in rep[:6]) + " — confirm each by hand") if rep
        else "no repeated lines (" + ", ".join(f"{d['name']} threshold {d['repeat_threshold']}" for d in docs) + ")")
    nh, n2 = sum(d["hyphens"] for d in docs), sum(d["hyphen_r2"] for d in docs)
    add("PQ5", "Line-end hyphens: R2 candidates vs real compounds", ASK if n2 else OK,
        f"{nh} line-end hyphen(s), {n2} whose joined form occurs elsewhere (R2 candidates)"
        + (": " + ", ".join(f"p.{r['page']} {h}" for r in rows for h in r["hyphen_r2"])[:200] if n2 else
           ("; all look like real compounds: do not join them" if nh else "")))
    nl, nd, nc = sum(d["ligatures"] for d in docs), sum(d["nfkc_delta"] for d in docs), sum(d["nfkc_changes"] for d in docs)
    add("PQ6", "Ligatures and NFKC deltas recorded; nothing normalised in place", ASK if (nl or nc) else OK,
        f"{nl} ligature(s); NFKC would change {nc} character(s), length delta {nd:+d}; this tool normalises nothing"
        + ("; any delta moves every later offset, so map ligatures with R3 edits if needed" if (nl or nc) else ""))
    jp = [r for r in rows if "reading order" in r["flags"]]
    worst = max(rows, key=lambda r: (r["rl_jumps"], -r["page"])) if rows else None
    two = sum(r["two_columns"] for r in rows)
    add("PQ7", "Two-column pages read column by column (right→left jumps ≤ 1 per page)", BAD if jp else (ASK if two else OK),
        (f"jumps ≥ {JUMP_FLAG} on {_pages(jp, lambda r: True)} (worst: {worst['doc']} p.{worst['page']}, {worst['rl_jumps']} jumps)" if jp
         else f"{two} two-column page(s); most jumps on a page: {worst['rl_jumps'] if worst else 0}"
         + (f" ({worst['doc']} p.{worst['page']}): look at that page once" if two and worst else "")))
    tf = [r for r in rows if "table found" in r["flags"]]
    st = [r for r in rows if "suspected flattened table" in r["flags"]]
    add("PQ8", "Tables: found and suspected tables listed; one checked against the rendered page", ASK if tf or st else OK,
        (f"tables found: {_pages(tf, lambda r: True) or 'none'}"
         + (" (" + "; ".join(f"p.{r['page']} " + ", ".join(f"{t['rows']}×{t['cols']}, {t['empty_share']:.0%} empty" for t in r["tables"]) for r in tf[:5]) + ")" if tf else "")
         + f"; suspected flattened tables: {_pages(st, lambda r: True) or 'none'}") if tf or st else "no table found and none suspected")
    ip = [r for r in rows if r["images"]]
    add("PQ9", "Figures with no extracted text: do any questions need them?", ASK if ip else OK,
        f"{sum(r['images'] for r in rows)} image(s) on {len(ip)} page(s)" + (f" ({_pages(ip, lambda r: True)}); the extractor sees no text in a figure" if ip else ""))
    labelled = [q for q in qs if q["expect"]]
    if not labelled:
        add("PQ10", "Questions on flagged pages", ASK, "no questions with an expect text given (use --questions)")
    else:
        onf = [q for q in labelled if q["flagged"]]
        nf = [q for q in labelled if q["not_found"]]
        add("PQ10", "Questions on flagged pages", BAD if onf or nf else OK,
            f"{len(onf)} of {len(labelled)} question(s) have an expect text on a flagged page"
            + (f" ({', '.join(q['id'] for q in onf)})" if onf else "")
            + f"; {len(nf)} with an expect text found on no page" + (f" ({', '.join(q['id'] for q in nf)})" if nf else ""))
    add("PQ11", "A stratified hand sample was read side by side with the page image", ASK,
        f"{len(res['sample'])} page(s) sampled by document × flag: " + ", ".join(f"{s['doc']} p.{s['page']}" for s in res["sample"])
        + "; open the --html page and read them")
    add("PQ12", "The would-be snapshot_id is recorded with the report", OK,
        f"`{res['snapshot_id']}` (pymupdf {res['settings']['pymupdf']}, options {{}}, cleaning none, doc ids "
        + ", ".join(d["doc_id"] for d in docs) + ")")
    return items


# ---------------------------------------------------------------------------------------------------------------- recommendation
REC_NO_QUESTIONS = "Not enough data: the flags show risk, not harm. Add questions with an expect text (--questions)."
REC_OCR = ("Some questions need pages with no usable text: these pages need OCR or captioning; exclude or flag them "
           "before labelling.")
REC_ARM = ("Try a comparison arm (Docling, or a per-column clip) as a new snapshot, and compare Hit@k on the questions "
           "that touch the flagged pages with Hit@k on the rest.")
REC_CLEAN = "A cleaning version (R2 de-hyphenation and R3 ligatures, as logged edits) is worth an experiment."
REC_FINE = "v0 parsing is fine for this corpus; do not clean."
REC_LOOK = ("Check by hand: some questions touch flagged pages. Measure Hit@k on those questions against the rest "
            "before changing the parser.")


def recommend(res):
    """Research C1 §8 points 1-5, in this order; returns every rule that applies, the first one is the recommendation."""
    qs = [q for q in res["questions"] if q["expect"]]
    if not qs:
        return [REC_NO_QUESTIONS]
    rows = {(r["doc"], r["page"]): r for r in res["pages"]}
    on = lambda q, names: any(set(f["flags"]) & set(names) for f in q["flagged"])
    out = []
    no_text = [r for r in res["pages"] if set(r["flags"]) & {"image-only", "blank", "encoding"}]
    missing = [q for q in qs if q["not_found"] and not q["found_after_cleaning"]]
    if any(on(q, ("image-only", "blank", "encoding")) for q in qs) or (no_text and missing):
        out.append(REC_OCR)
    if any(on(q, ("reading order", "table found", "suspected flattened table", "parsers disagree")) for q in qs):
        out.append(REC_ARM)
    touch_clean = any(q["found_after_cleaning"] for q in qs) or any(
        (rows[(h["doc"], p)]["hyphen_r2"] or rows[(h["doc"], p)]["ligatures"])
        for q in qs for it in q["items"] for h in it["hits"] for p in h["pages"])
    if touch_clean and any(r["hyphen_r2"] or r["ligatures"] for r in res["pages"]):
        out.append(REC_CLEAN)
    if not out:
        out.append(REC_FINE if not any(q["flagged"] or q["not_found"] for q in qs) else REC_LOOK)
    return out


# ---------------------------------------------------------------------------------------------------------------- report
def _span(pages):
    return str(pages[0]) if len(pages) == 1 else f"{pages[0]}–{pages[-1]}"


def _flags(r):
    return ", ".join(r["flags"]) or "-"


def render_report(res):
    st, docs, rows = res["settings"], res["docs"], res["pages"]
    cl = " ".join(f"{x['id']} {x['verdict']}" for x in res["checklist"])
    flagged = [r for r in rows if r["flags"]]
    L = ["# Parse quality check", ""]
    if res.get("command"):
        L += ["Command (from `rag_learning/`):", "", "```bash", res["command"], "```", ""]
    L += ["**What this is:** per-page signals of how PyMuPDF's plain `get_text()` (the v0 loader) extracted these documents, "
          "and which of your questions sit on flagged pages.",
          "**What this is not:** a measure of harm. A flag shows risk; harm shows only in retrieval metrics (Hit@k, CE@k) on "
          "the questions whose expect text sits on flagged pages, compared with the rest. Answer quality is a separate "
          "measurement again.", "",
          f"**Recommendation:** {res['recommendation']} (section 7). Checklist: {cl}.", "",
          f"Settings: pymupdf {st['pymupdf']} · `{st['call']}` · options {{}} · cleaning none · pages 1-based, joined with "
          f"`\"\\n\"` · sample {st['sample']} · second parser: {st['second_parser']}"
          + (f" ({st['second_parser_status']})" if st["second_parser"] != "none" else "") + ". No API call.", "",
          "## 0 Snapshot", "",
          f"Would-be `snapshot_id`: **`{res['snapshot_id']}`** (06 §5.3 recipe: parser pymupdf@{st['pymupdf']}, options `{{}}`, "
          "cleaning `none`, page join `\\n`, one `doc_id:doc_text_sha256` per document, sorted by doc id). "
          "Any change to the text, the parser version, the options or the cleaning gives a new id.", ""]
    if any(not d["is_pdf"] for d in docs):
        L += ["Note: `.txt`/`.md` files pass through unparsed as one page; their text enters the id as read.", ""]
    L += ["## 1 Corpus summary", "", "| Measure | Value |", "|---|---|",
          f"| Documents | {len(docs)} |", f"| Pages | {len(rows)} |",
          f"| Characters (pages joined with `\\n`) | {sum(d['doc_text_chars'] for d in docs):,} |",
          f"| Images | {sum(d['images'] for d in docs)} |",
          f"| Flagged pages | {len(flagged)} |",
          f"| Pages with notes only | {sum(1 for r in rows if r['notes'] and not r['flags'])} |", "",
          "## 2 Per document", "",
          "| Document | doc_id | Pages | Sum of page lengths | `doc_text` length | UTF-8 bytes | `doc_text_sha256` (first 12) | Images | Flagged pages |",
          "|---|---|---|---|---|---|---|---|---|"]
    for d in docs:
        L.append(f"| `{d['name']}` | `{d['doc_id']}` | {d['pages']} | {d['page_chars']:,} | {d['doc_text_chars']:,} | {d['utf8_bytes']:,} | "
                 f"`{d['doc_text_sha256'][:12]}` | {d['images']} | {d['flagged']} |")
    L += ["", "| Document | Repeated lines (R1 threshold) | Line-end hyphens (R2 candidates) | Ligatures | NFKC changes (delta) | "
          "Two-column pages | Max right→left jumps | Tables found | Suspected flattened tables | Equation-like lines | "
          "Pages ending open / sentence cut | U+FFFD / (cid:) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in docs:
        L.append(f"| `{d['name']}` | {len(d['repeated'])} ({d['repeat_threshold']}) | {d['hyphens']} ({d['hyphen_r2']}) | {d['ligatures']} | "
                 f"{d['nfkc_changes']} ({d['nfkc_delta']:+d}) | {d['two_col_pages']} | {d['max_jumps']} | {d['tables']} | {d['suspected_tables']} | "
                 f"{d['equation_lines']} | {d['ends_open']} / {d['cuts']} | {d['fffd']} / {d['cid']} |")
    L.append("")
    for d in docs:
        rws = d["rows"]
        show = rws if len(rws) <= 4 else rws[:3] + [rws[-1]]
        L.append(f"Page table of `{d['name']}`: " + "; ".join(f"p.{p} [{s:,}, {e:,})" for p, s, e in show)
                 + (" …" if len(rws) > 4 else "") + f". Round trip `doc_text[start:end] == page`: {'yes' if d['round_trip'] else 'NO'}.")
        if d["repeated"]:
            L.append(f"Repeated lines in `{d['name']}` (digits shown as #): " + "; ".join(f"\"{k}\" ({v} pages)" for k, v in d["repeated"].items())
                     + ". Shown, never deleted: confirm each as noise or a real heading.")
        if d["nonword"]:
            nw = d["nonword"]
            L.append(f"Non-word share in `{d['name']}`: median {nw['median']:.4f}, MAD {nw['mad']:.4f}, flag above {nw['limit']:.4f}.")
        else:
            L.append(f"Non-word share in `{d['name']}`: not judged (fewer than 3 text pages).")
    L += ["", "## 3 Flagged pages", ""]
    if not flagged:
        L += ["No page is flagged.", ""]
    else:
        L += ["| Document | Page | Characters | Images | Flags | Notes | Start of text |", "|---|---|---|---|---|---|---|"]
        for r in flagged:
            extra = []
            if r["rl_jumps"]:
                extra.append(f"{r['rl_jumps']} jumps")
            for t in r["tables"]:
                extra.append(f"table {t['rows']}×{t['cols']}")
            if "suspected flattened table" in r["flags"]:
                extra.append(f"{r['number_lines']} number-only lines")
            if r["repeated_lines"]:
                extra.append("repeats: " + ", ".join(f"\"{k}\"" for k in r["repeated_lines"]))
            fl = _flags(r) + (f" ({'; '.join(extra)})" if extra else "")
            L.append(f"| `{r['doc']}` | {r['page']} | {r['chars']} | {r['images']} | {fl} | {'; '.join(r['notes']) or '-'} | {r['snippet'] or '(empty)'} |")
        L.append("")
    notes_only = [r for r in rows if r["notes"] and not r["flags"]]
    if notes_only:
        L += ["Pages with notes only (reported, not flagged):", "", "| Document | Page | Notes |", "|---|---|---|"]
        for r in notes_only[:40]:
            L.append(f"| `{r['doc']}` | {r['page']} | {'; '.join(r['notes'])} |")
        if len(notes_only) > 40:
            L.append(f"| … | | {len(notes_only) - 40} more in `--pages-jsonl` |")
        L.append("")
    hy = [(r, h) for r in rows for h in r["hyphen_breaks"]]
    if hy:
        L.append("Line-end hyphens (R2 joins only those marked *, whose joined form occurs elsewhere): "
                 + ", ".join(f"p.{r['page']} {h}{'*' if h in r['hyphen_r2'] else ''}" for r, h in hy[:30]) + ".")
        L.append("")
    L += ["## 4 Sample for the hand check", "",
          "Strata: document × first flag (or 'no flag'); flagged strata first, then a fixed pseudo-random order. "
          "Read each page next to its rendered image (`--html`).", "", "| Document | Page | Stratum |", "|---|---|---|"]
    for s in res["sample"]:
        L.append(f"| `{s['doc']}` | {s['page']} | {s['stratum']} |")
    L += ["", "## 5 Questions", ""]
    qs = res["questions"]
    if not qs:
        L += ["No questions given (use --questions with `q` and `expect`).", ""]
    else:
        L += ["Each expect text is located in `doc_text` (case-insensitive, whitespace normalised) and its offset turned into a "
              "1-based page through the page table.", "",
              "| Question | Expect text (start) | Found on | Flags there |", "|---|---|---|---|"]
        for q in qs:
            if not q["items"]:
                L.append(f"| {q['id']}: {q['q'][:60]} | (no expect) | - | - |")
            for it in q["items"]:
                where = "; ".join(f"`{h['doc']}` p.{_span(h['pages'])}" for h in it["hits"][:4]) + (
                    f" (+{len(it['hits']) - 4} more)" if len(it["hits"]) > 4 else "")
                if not it["hits"]:
                    where = "**found on no page**" + (" (found after joining line-end hyphens / decomposing ligatures: "
                                                      + ", ".join(f"`{h['doc']}` p.{h['pages'][0]}" for h in it["after_cleaning"][:3]) + ")"
                                                      if it["after_cleaning"] else "")
                fl = sorted({f for h in it["hits"] for p in h["pages"] for f in next(r for r in rows if r["doc"] == h["doc"] and r["page"] == p)["flags"]})
                L.append(f"| {q['id']}: {q['q'][:60]} | {it['expect'][:50]} | {where} | {', '.join(fl) or '-'} |")
        L.append("")
        onf = [q for q in qs if q["flagged"]]
        L.append(f"Questions with an expect text on a flagged page: **{len(onf)}**"
                 + (": " + "; ".join(f"{q['id']} (" + ", ".join(f"p.{f['page']} {'/'.join(f['flags'])}" for f in q["flagged"]) + ")" for q in onf) if onf else "") + ".")
        nf = [(q["id"], e) for q in qs for e in q["not_found"]]
        L.append(f"Expect texts found on no page: **{len(nf)}**" + (": " + "; ".join(f"{i} \"{e[:40]}\"" for i, e in nf) if nf else "") + ".")
        L += ["", "To learn whether a flag does harm, compare Hit@k (and CE@k) of the questions above with the other questions, "
              "for the v0 snapshot and for any comparison arm. That is a retrieval measurement; answer quality is measured separately.", ""]
    L += ["## 6 Checklist", "", "| Check | Verdict | Evidence | How to check |", "|---|---|---|---|"]
    for x in res["checklist"]:
        L.append(f"| {x['id']} {x['check']} | {x['verdict']} | {x['evidence']} | {x['how']} |")
    L += ["", "✓ fine · ✗ problem found · ? check by hand.", "", "## 7 Recommendation", "", f"**{res['recommendation']}**", ""]
    if len(res["recommendations"]) > 1:
        L += ["Also applies:", ""] + [f"- {x}" for x in res["recommendations"][1:]] + [""]
    L += ["Order of the rules: no questions → text missing on question pages (PQ1/PQ2) → order or tables on question pages "
          "(PQ7/PQ8) → cleaning candidates that questions quote (PQ5/PQ6) → nothing on question pages.", "",
          "Flags show risk, not harm. Lesson: `study/lessons/C1_parsing.html` (steps 7 and 11)."]
    return "\n".join(L) + "\n"


def render_html(res, docs):
    """A self-contained page: for each sampled page, the rendered image next to the extracted text.
    docs: the loaded documents (load_documents). The page text is the user's own; nothing leaves this computer."""
    by = {(r["doc"], r["page"]): r for r in res["pages"]}
    dd = {d["name"]: d for d in docs}
    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>Parse hand check</title><style>",
             ":root{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#ddd;--flag:#b3261e}",
             "@media (prefers-color-scheme: dark){:root:not([data-theme='light']){--bg:#161616;--fg:#eee;--muted:#aaa;--line:#444;--flag:#f2b8b5}}",
             "body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;margin:0 auto;max-width:1200px;padding:16px}",
             ".pair{display:grid;grid-template-columns:1fr 1fr;gap:16px;border-top:1px solid var(--line);padding:16px 0}",
             "@media (max-width:760px){.pair{grid-template-columns:1fr}}",
             "img{max-width:100%;border:1px solid var(--line);background:#fff}pre{white-space:pre-wrap;word-break:break-word;font-size:13px;margin:0}",
             ".flag{color:var(--flag)}.muted{color:var(--muted)}</style></head><body>",
             f"<h1>Parse hand check</h1><p class='muted'>snapshot_id {res['snapshot_id']} · pymupdf {res['settings']['pymupdf']} · "
             "read each page next to its image and note missing, merged or out-of-order words.</p>"]
    for s in res["sample"]:
        r = by[(s["doc"], s["page"])]
        img = "<p class='muted'>(text file: no page image)</p>"
        d = dd[s["doc"]]
        if d["is_pdf"]:
            with pymupdf.open(d["path"]) as pdf:
                png = pdf[s["page"] - 1].get_pixmap(dpi=72).tobytes("png")
            img = f"<img alt='page {s['page']} of {html.escape(s['doc'])}' src='data:image/png;base64,{base64.b64encode(png).decode()}'>"
        text = d["pages"][s["page"] - 1]
        parts.append(f"<section class='pair'><div><h2>{html.escape(s['doc'])} p.{s['page']}</h2>"
                     f"<p class='flag'>{html.escape(_flags(r))}</p><p class='muted'>{html.escape('; '.join(r['notes']))}</p>{img}</div>"
                     f"<div><h2>Extracted text ({r['chars']} characters)</h2><pre>{html.escape(text)}</pre></div></section>")
    parts.append("</body></html>")
    return "\n".join(parts)


def pages_jsonl(res):
    keep = [k for k in res["pages"][0] if k not in ("doc",)] if res["pages"] else []
    return "".join(json.dumps({"doc": r["doc"], **{k: r[k] for k in keep}}, ensure_ascii=False) + "\n" for r in res["pages"])


# ---------------------------------------------------------------------------------------------------------------- CLI
def _cmd(argv):
    return "uv run python study/tools/parse_quality_check.py " + " ".join(shlex.quote(a) for a in argv)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description="Which pages did the parser get wrong, and do my questions touch them? "
                                             "Per-page signals of PyMuPDF get_text() (v0), a Markdown report. No API calls.")
    ap.add_argument("--docs", nargs="+", required=True, help="files or folders (.pdf; .txt/.md pass through as one page)")
    ap.add_argument("--doc-ids", default="", help="comma-separated document ids (default: file stems); they enter the snapshot_id")
    ap.add_argument("--questions", help=".jsonl with \"q\" and \"expect\" (a string or a list of strings)")
    ap.add_argument("--sample", type=int, default=8, help="pages in the stratified hand-check sample (default 8)")
    ap.add_argument("--second-parser", choices=("none", "pdfplumber", "pypdf"), default="none",
                    help="diff against a second parser, only if it is importable (nothing is installed)")
    ap.add_argument("--html", help="write a side-by-side page (image | extracted text) for the sampled pages")
    ap.add_argument("--report", help="write the Markdown report here (default: print it)")
    ap.add_argument("--pages-jsonl", help="write one row per page with every signal (short snippets only)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    if a.sample < 0:
        print("error: --sample must be >= 0", file=sys.stderr)
        return 2
    try:
        docs = load_documents(a.docs, [x.strip() for x in a.doc_ids.split(",") if x.strip()] or None)
        res = run_check(docs, a.questions, sample=a.sample, second_parser=a.second_parser, command=_cmd(argv))
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.second_parser != "none" and res["settings"]["second_parser_status"] != "used":
        print(f"second parser {a.second_parser}: not installed, skipped", file=sys.stderr)
    text = render_report(res)
    if a.html:
        Path(a.html).parent.mkdir(parents=True, exist_ok=True)
        Path(a.html).write_text(render_html(res, docs), encoding="utf-8", newline="\n")
    if a.pages_jsonl:
        Path(a.pages_jsonl).parent.mkdir(parents=True, exist_ok=True)
        Path(a.pages_jsonl).write_text(pages_jsonl(res), encoding="utf-8", newline="\n")
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8", newline="\n")
        print(f"pages {len(res['pages'])}, flagged {sum(1 for r in res['pages'] if r['flags'])}, snapshot_id {res['snapshot_id']}")
        for i in res["checklist"]:
            print(f"{i['id']:5s} {i['verdict']}  {i['check']}")
        print(f"recommendation: {res['recommendation']}")
        print(f"report: {a.report}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
