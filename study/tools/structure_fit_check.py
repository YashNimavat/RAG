"""structure_fit_check: will structure-aware chunking work on MY PDFs, and with what settings?

What this is: a command-line tool (also importable) that reads your PDFs exactly as the course's v0 loader does
(PyMuPDF `page.get_text()`, no options, no cleaning, pages joined with "\\n"), recovers the headings from the typography
(and checks the outline and tags), cuts the text at its own sections, and writes a Markdown report:
  1 Fonts and body size   character-weighted font-size histogram; the body size
  2 Structure sources     outline (get_toc), tags (StructTreeRoot, MarkInfo), creator
  3 Headings              per level: size only vs size + bold; wrapped headings joined; filtered lines; repeated
                          lines (running headers); numbering vs levels; the headings size-only misses
  4 Layout                two-column pages (block x0), right-to-left jumps, tables (find_tables)
  5 Alignment and outline dict lines vs get_text(); every heading's exact offset; repeated titles; the outline print
  6 Chunks per split level section medians and the `auto` choice; chunk statistics for v0, the cross-page control and
                          every split level (with and without merge); the invariants
  7 Page breaks           orphaned headings and mid-sentence page cuts, and which arms keep them whole
  8 Eval set              with --evalset: per item, straddles_v0 and crosses_page (the bucket I2 targets)
  9 Inspection sample     --sample random chunks (seed --seed) with an automatic pre-check; --sheet writes the sheet
 10 Checklist             S1-S11: PASS, WARN, FAIL or MANUAL, the evidence, and how to check by hand
 11 Recommendation        first matching rule wins (see recommend()), then notes
What this is not: a retrieval evaluation. Whether the structure chunks retrieve better is an experiment (CE@k at fixed
k and at equal budget, by bucket); this tool says whether the structure can be recovered and what the chunks look like.

Rules (= sources/verification/I2/i2_structure.py, the course's reference mechanism; lesson I2):
  bold         span flags & 16, or char_flags & 8
  body size    the font size holding the most characters (stripped span text, sizes rounded to 0.01)
  levels       bold sizes above body + 0.5, largest first, get levels 1, 2, ...; an all-bold line at the body size
               (within 0.5) gets the next level ("size + bold"). "size only" skips that last rule
  filters      a heading line has <= 12 words, does not end in . ! ?, and does not repeat on >= 3 pages
  joining      consecutive heading lines of one level in one block are one heading (a wrapped heading)
  alignment    moving cursor + find in doc_text; a heading that is not found fails closed (no chunks are built)
  units        a boundary at every heading of level <= split level; a heading never ends a unit (it glues forward)
  balanced     a unit longer than the cap is cut into n = ceil(len / cap) pieces of about len / n, each cut at a
               sentence-ending line break within half a piece of the ideal point, else the nearest line break; no
               overlap; never inside or right after a heading
  merge        adjacent units both under --min-chars, with the same parent path and together <= cap, are merged
  auto level   the deepest level whose median section length >= --min-chars
  v0           the 07 recursive splitter per page, 1,000 characters, overlap 200 (the course's v0 index)
Checklist thresholds are project choices [P]: body size >= 50% of characters (S2); 1 heading per 3 pages to 15 per
page (S3); size-only misses < 10% (S4); outline titles matched >= 90% (S5); < 10% of chunks under --min-chars (S9);
>= 8 of 10 inspected chunks pass (S10).

No API calls, no network: standard library + PyMuPDF only.

Usage, from rag_learning/:
    uv run python study/tools/structure_fit_check.py --pdf my.pdf --out structure_report.md --sheet inspection.md
    uv run python study/tools/structure_fit_check.py --pdf "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" --doc-ids climate --evalset study/tools/examples/climate_seed_spans.jsonl --out report.md --sheet sheet.md
    uv run python study/tools/structure_fit_check.py --pdf docs/ --split-level 2 --cap 800 --json result.json
Eval set: JSONL in the 06 §6.7 / M1 seed format (qid, category, answerable, evidence_groups -> alternatives ->
segments {doc_id, page, char_start, char_end}, quote); offsets are page-relative on get_text(). With one PDF every
segment belongs to it; with several, segments are matched by doc_id (--doc-ids, default: file stems).
  straddles_v0   some evidence group has no alternative inside one v0 chunk (alt ⊆ [c.a, c.b), all its segments)
  crosses_page   an alternative's evidence starts and ends on different pages
Exit codes: 0 report written (whatever the verdicts); 2 bad input (missing file, not a PDF, bad options, bad eval set).

Import:
    from structure_fit_check import run_check, render_report, render_sheet
    res = run_check(["doc.pdf"], cap=1000, split_level="auto", min_chars=400)
    print(render_report(res))
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import math
import random
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import pymupdf
except ImportError:                                   # older PyMuPDF installs expose only "fitz"
    import fitz as pymupdf

PASS, WARN, FAIL, MANUAL = "PASS", "WARN", "FAIL", "MANUAL"
BOLD_FLAG = 16              # span["flags"] bit 4 (TEXT_FONT_BOLD)
BOLD_CHAR_FLAG = 8          # span["char_flags"] synthetic bold
SEPARATORS = ("\n\n", "\n", " ")
MAX_WORDS = 12              # [P] a heading line has at most 12 words
REPEAT_PAGES = 3            # [P] a line on >= 3 pages is a running header/footer, never a heading
END_PUNCT = ".!?"
SENT_END = ".!?:"           # a chunk "ends at a sentence" (inspection pre-check, page-break cuts)
V0_SIZE, V0_OVERLAP = 1000, 200
BODY_SHARE = 0.50           # S2
MIN_PER_PAGE, MAX_PER_PAGE = 1 / 3, 15   # S3
DISAGREE = 0.10             # S4
TOC_MATCH = 0.90            # S5
SMALL_SHARE = 0.10          # S9
INSPECT_PASS = 0.8          # S10: 8 of 10
IMAGE_ONLY_TEXT = 50        # a page with an image and fewer non-space characters than this has no usable text layer
LONG_BLOCK = 40             # a text block this long counts towards "two columns"
JUMP_FLAG = 2               # right-to-left jumps on one page that mean the reading order is broken
NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")
CHAPTER = re.compile(r"^chapter\s+\d+\b", re.I)


# ---------------------------------------------------------------------------------------------------------------- input
def find_pdfs(paths):
    """Files or folders (folders: *.pdf, recursive, sorted). Raises FileNotFoundError / ValueError."""
    files, seen = [], set()
    for p in map(Path, paths):
        if p.is_dir():
            found = sorted(q for q in p.rglob("*") if q.is_file() and q.suffix.lower() == ".pdf")
            if not found:
                raise ValueError(f"no .pdf files in folder: {p}")
        elif p.is_file():
            if p.suffix.lower() != ".pdf":
                raise ValueError(f"not a PDF: {p.name} (this tool reads .pdf files)")
            found = [p]
        else:
            raise FileNotFoundError(f"no such file or folder: {p}")
        for f in found:
            if f.resolve() not in seen:
                seen.add(f.resolve())
                files.append(f)
    if not files:
        raise ValueError("no PDF given")
    return files


def _quiet(fn, *a):
    """PyMuPDF's find_tables prints an advert for pymupdf_layout on stdout; keep it out of the report output."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def extract(path):
    """Everything the check needs from one PDF, read once."""
    try:
        doc = pymupdf.open(path)
    except Exception as e:  # noqa: BLE001  (PyMuPDF raises its own FileDataError etc.)
        raise ValueError(f"cannot open {Path(path).name} as a PDF ({e})") from None
    with doc:
        if not doc.is_pdf:
            raise ValueError(f"{Path(path).name} is not a PDF")
        if doc.needs_pass:
            raise ValueError(f"{Path(path).name} is encrypted (needs a password)")
        if len(doc) == 0:
            raise ValueError(f"{Path(path).name} has no pages")
        pages = [pg.get_text() for pg in doc]
        dicts = [pg.get_text("dict") for pg in doc]
        layout = []
        for pg, d in zip(doc, dicts):
            layout.append({"images": len(pg.get_images()), "two_columns": two_columns(pg), "rl_jumps": rl_jumps(d, pg.rect),
                           "tables": len(_quiet(lambda: pg.find_tables().tables))})
        toc = doc.get_toc()
        cat = doc.pdf_catalog()
        struct = doc.xref_get_key(cat, "StructTreeRoot")[0] not in ("null", None)
        mark = doc.xref_get_key(cat, "MarkInfo")
        meta = doc.metadata or {}
    return {"pages": pages, "dicts": dicts, "layout": layout, "toc": toc, "tagged": struct,
            "marked": "Marked true" in str(mark[1]), "creator": meta.get("creator") or "",
            "producer": meta.get("producer") or ""}


def load_evalset(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"eval set not found: {p}")
    items = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            it = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{p.name}, line {n}: not valid JSON ({e.msg})") from None
        if not isinstance(it, dict) or not isinstance(it.get("evidence_groups"), list):
            raise ValueError(f"{p.name}, line {n}: no \"evidence_groups\" list (expected the 06 §6.7 / M1 seed format)")
        it.setdefault("qid", f"line{n}")
        items.append(it)
    if not items:
        raise ValueError(f"{p.name}: the eval set is empty")
    return items


# ---------------------------------------------------------------------------------------------------------------- layout
def rl_jumps(d, rect):
    """Right-to-left jumps among body lines (top and bottom 10% excluded) (= parse_quality_check.rl_jumps)."""
    mid, h = rect.width / 2, rect.height
    ls = []
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            if "".join(s["text"] for s in ln["spans"]).strip():
                ls.append((ln["bbox"][0], ln["bbox"][1]))
    ls = [x for x in ls if 0.1 * h < x[1] < 0.9 * h]
    return sum(1 for a, b in zip(ls, ls[1:]) if a[0] >= mid and b[0] < mid)


def two_columns(page):
    """Long text blocks start in both halves of the page (= parse_quality_check.two_columns, C1)."""
    mid = page.rect.width / 2
    sides = set()
    for b in page.get_text("blocks"):
        if b[6] == 0 and len(b[4].strip()) >= LONG_BLOCK:
            sides.add("R" if b[0] >= mid else "L")
    return sides == {"L", "R"}


# ---------------------------------------------------------------------------------------------------------------- headings
def page_starts(pages):
    starts, pos = [], 0
    for t in pages:
        starts.append(pos)
        pos += len(t) + 1
    return starts


def page_of(starts, pos):
    """1-based page of a document offset (the join character belongs to the page before it)."""
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid] <= pos:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


def is_bold(span):
    return bool(span["flags"] & BOLD_FLAG) or bool(span.get("char_flags", 0) & BOLD_CHAR_FLAG)


def line_records(dicts):
    """One record per text line of get_text('dict'): page, block, line, raw text, max size, all-bold, span count."""
    out = []
    for pno, d in enumerate(dicts, 1):
        for bno, block in enumerate(d["blocks"]):
            for lno, line in enumerate(block.get("lines", [])):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                out.append({"page": pno, "block": bno, "line": lno, "raw": "".join(s["text"] for s in line["spans"]),
                            "size": round(max(s["size"] for s in spans), 2), "bold": all(is_bold(s) for s in spans),
                            "spans": len(spans)})
    return out


def size_histogram(dicts):
    """Characters (stripped span text) per (rounded size, bold), in reading order of first appearance."""
    h = Counter()
    for d in dicts:
        for block in d["blocks"]:
            for line in block.get("lines", []):
                for s in line["spans"]:
                    h[(round(s["size"], 2), is_bold(s))] += len(s["text"].strip())
    return h


def body_size(hist):
    per_size = Counter()
    for (size, _bold), n in hist.items():
        per_size[size] += n
    if not per_size or not sum(per_size.values()):
        return None
    return per_size.most_common(1)[0][0]


def heading_sizes(lines, b):
    return sorted({r["size"] for r in lines if r["size"] > b + 0.5 and r["bold"]}, reverse=True)


def detect_headings(lines, b, rule="size+bold", max_words=MAX_WORDS):
    """Heading lines -> headings with levels (rule "size" or "size+bold"; see the module docstring)."""
    if b is None:
        return []
    bigger = heading_sizes(lines, b)
    level_of = {s: i + 1 for i, s in enumerate(bigger)}
    body_level = len(bigger) + 1
    pages_of_text = defaultdict(set)
    for r in lines:
        pages_of_text[r["raw"].strip()].add(r["page"])

    def level(r):
        t = r["raw"].strip()
        if not r["bold"] or len(t.split()) > max_words or t[-1] in END_PUNCT:
            return None
        if len(pages_of_text[t]) >= REPEAT_PAGES:
            return None
        if r["size"] in level_of:
            return level_of[r["size"]]
        if rule == "size+bold" and abs(r["size"] - b) <= 0.5:
            return body_level
        return None

    heads = []
    for r in lines:
        lv = level(r)
        if lv is None:
            continue
        prev = heads[-1] if heads else None
        if (prev and prev["level"] == lv and prev["page"] == r["page"] and prev["block"] == r["block"]
                and prev["last_line"] == r["line"] - 1):
            prev["lines"].append(r["raw"])
            prev["last_line"] = r["line"]
            prev["title"] = " ".join(x.strip() for x in prev["lines"])
            continue
        heads.append({"page": r["page"], "block": r["block"], "last_line": r["line"], "level": lv,
                      "size": r["size"], "lines": [r["raw"]], "title": r["raw"].strip()})
    return heads


def align(doc_text, heads):
    """Moving cursor + find. Returns (aligned headings with start/end, failures). Any failure = fail closed."""
    cur, ok, failed = 0, [], []
    for h in heads:
        pos = doc_text.find(h["lines"][0], cur)
        if pos < 0:
            failed.append({"title": h["title"], "page": h["page"], "why": f"not found after offset {cur}"})
            continue
        end, bad = pos + len(h["lines"][0]), False
        for ln in h["lines"][1:]:
            nxt = doc_text.find(ln, end)
            if nxt < 0 or doc_text[end:nxt].strip():
                bad = True
                break
            end = nxt + len(ln)
        if bad:
            failed.append({"title": h["title"], "page": h["page"], "why": "wrapped heading line not adjacent"})
            continue
        ok.append({**h, "start": pos, "end": end})
        cur = end
    return ok, failed


def add_paths(heads):
    """Section path (breadcrumb): the titles on the stack of open headings."""
    stack = []
    for h in heads:
        while stack and stack[-1]["level"] >= h["level"]:
            stack.pop()
        stack.append(h)
        h["path"] = [x["title"] for x in stack]
    return heads


def section_ranges(heads, n, level):
    """Section of h at a level: [start(h), start(next heading with level <= level(h)))."""
    out = []
    for i, h in enumerate(heads):
        if h["level"] != level:
            continue
        end = n
        for g in heads[i + 1:]:
            if g["level"] <= h["level"]:
                end = g["start"]
                break
        out.append((h["start"], end, h))
    return out


def numbering(heads):
    """Numbered headings ("Chapter 3", "2.1 ...") and whether numbering depth agrees with the typographic level."""
    rows = []
    for h in heads:
        t = h["title"]
        if CHAPTER.match(t):
            rows.append((1, h["level"]))
        else:
            m = NUMBERED.match(t)
            if m:
                rows.append((m.group(1).count(".") + 1, h["level"]))
    by_depth = defaultdict(set)
    for dep, lv in rows:
        by_depth[dep].add(lv)
    one_each = all(len(v) == 1 for v in by_depth.values())
    ordered = [min(by_depth[d]) for d in sorted(by_depth)]
    consistent = one_each and all(x < y for x, y in zip(ordered, ordered[1:]))
    return {"n": len(rows), "depth_to_levels": {d: sorted(v) for d, v in sorted(by_depth.items())}, "consistent": consistent}


# ---------------------------------------------------------------------------------------------------------------- chunking
def _split_spans(text, start, end, seps, size):
    """07 H.1: recursively cut [start, end) into pieces of <= size chars, preferring early separators."""
    if end - start <= size:
        return [(start, end)]
    if not seps:
        return [(s, s + 1) for s in range(start, end)]
    sep, rest = seps[0], seps[1:]
    pieces, i = [], start
    while i < end:
        j = text.find(sep, i, end)
        if j == -1:
            pieces.append((i, end))
            break
        pieces.append((i, j + len(sep)))
        i = j + len(sep)
    out = []
    for a, b in pieces:
        out.extend([(a, b)] if b - a <= size else _split_spans(text, a, b, rest, size))
    return out


def recursive_spans(text, size, overlap):
    """07 H.1 recursive_chunks: greedy merge up to size; the next chunk restarts with whole trailing pieces <= overlap."""
    if not text:
        return []
    spans, cur = [], []
    for p in _split_spans(text, 0, len(text), SEPARATORS, size):
        if cur and p[1] - cur[0][0] > size:
            spans.append((cur[0][0], cur[-1][1]))
            keep = []
            for q in reversed(cur):
                if cur[-1][1] - q[0] <= overlap:
                    keep.insert(0, q)
                else:
                    break
            cur = keep
            while cur and p[1] - cur[0][0] > size:
                cur.pop(0)
        cur.append(p)
    if cur:
        spans.append((cur[0][0], cur[-1][1]))
    return spans


def page_segments(starts, n, a, b):
    segs = []
    ends = [s - 1 for s in starts[1:]] + [n]          # page p covers [start_p, start_{p+1}) incl. its join char
    for p, (s, e) in enumerate(zip(starts, ends), 1):
        e_incl = e + 1 if p < len(starts) else e
        lo, hi = max(a, s), min(b, e_incl)
        if lo < hi:
            segs.append((p, lo, hi))
    return segs


def v0_chunks(pages, starts, size=V0_SIZE, overlap=V0_OVERLAP):
    """v0: the recursive splitter per page, as document offsets."""
    n = sum(len(p) for p in pages) + len(pages) - 1
    out = []
    for pi, page in enumerate(pages):
        for a, b in recursive_spans(page, size, overlap):
            if page[a:b].strip():
                out.append({"a": starts[pi] + a, "b": starts[pi] + b, "text": page[a:b], "path": [], "merged": False,
                            "piece": 0, "pieces": 1, "page_segments": page_segments(starts, n, starts[pi] + a, starts[pi] + b)})
    return out


def recursive_doc_chunks(doc_text, starts, size=V0_SIZE, overlap=V0_OVERLAP):
    """The cross-page control: the same recursive splitter over the whole doc_text."""
    return [{"a": a, "b": b, "text": doc_text[a:b], "path": [], "merged": False, "piece": 0, "pieces": 1,
             "page_segments": page_segments(starts, len(doc_text), a, b)}
            for a, b in recursive_spans(doc_text, size, overlap) if doc_text[a:b].strip()]


def _best_cut(text, prev, b, ideal, cap, forbidden, room, slack):
    """End of the piece that starts at prev: a line break (a space if none fits) that keeps the piece within the cap,
    leaves at most `room` characters, and is not inside or right after a heading. A line break after a sentence end
    within `slack` of the ideal point wins; otherwise the nearest line break."""
    for sep in ("\n", " "):
        cands, i = [], prev
        while True:
            j = text.find(sep, i, b)
            if j < 0:
                break
            p = j + 1
            if prev < p < b and p - prev <= cap and b - p <= room and p not in forbidden:
                cands.append(p)
            i = j + 1
        if cands:
            clean = [p for p in cands if sep == "\n" and text[:p].rstrip()[-1:] in ".!?" and abs(p - ideal) <= slack]
            pool = clean or cands
            return min(pool, key=lambda p: (abs(p - ideal), p))
    return min(prev + cap, b)                  # no usable separator at all: a hard cut


def heading_guard(text, heads):
    """Cut positions that would end a chunk inside a heading or right after one (before its body starts)."""
    bad = set()
    for h in heads:
        e = h["end"]
        while e < len(text) and text[e].isspace():
            e += 1
        bad.update(range(h["start"] + 1, e + 1))
    return bad


def balanced_split(text, a, b, cap, forbidden=frozenset()):
    """n = ceil(len / cap) pieces of about len / n; if a piece would still exceed the cap, try n + 1."""
    length = b - a
    if length <= cap:
        return [(a, b)]
    n = math.ceil(length / cap)
    while n <= length:
        cuts = [a]
        for i in range(1, n):
            cuts.append(_best_cut(text, cuts[-1], b, a + length * i / n, cap, forbidden, (n - i) * cap, length / (2 * n)))
        cuts.append(b)
        pieces = list(zip(cuts, cuts[1:]))
        if all(0 < y - x <= cap for x, y in pieces):
            return pieces
        n += 1
    return [(x, min(x + cap, b)) for x in range(a, b, cap)]       # safety net (never reached on real text)


def units(doc_text, heads, split_level):
    """Split-level units: a boundary at every heading of level <= split_level, except a heading that directly
    follows another heading (only whitespace between): a heading never ends a unit, it glues forward."""
    bounds = [0]
    prev_end = None
    for h in heads:
        if h["level"] > split_level:
            prev_end = h["end"]
            continue
        glued = prev_end is not None and not doc_text[prev_end:h["start"]].strip()
        if not glued and h["start"] > 0:
            bounds.append(h["start"])
        prev_end = h["end"]
    bounds.append(len(doc_text))
    out = []
    for a, b in zip(bounds, bounds[1:]):
        if b > a:
            inside = [h for h in heads if a <= h["start"] < b]
            last_split = [h for h in inside if h["level"] <= split_level]
            owner = last_split[-1] if last_split else None
            if owner is None:
                before = [h for h in heads if h["start"] < a]
                owner = before[-1] if before else None
            out.append({"a": a, "b": b, "path": list(owner["path"]) if owner else [], "merged": False})
    return out


def merge_small(us, cap, min_chars, split_level):
    """While two adjacent units are both below min_chars, share their parent path and fit the cap, merge them."""
    changed = True
    us = [dict(u) for u in us]
    while changed:
        changed = False
        for i in range(len(us) - 1):
            x, y = us[i], us[i + 1]
            parent_x, parent_y = x["path"][:split_level - 1], y["path"][:split_level - 1]
            if (x["b"] - x["a"] < min_chars and y["b"] - y["a"] < min_chars and parent_x == parent_y
                    and y["b"] - x["a"] <= cap):
                us[i] = {"a": x["a"], "b": y["b"], "path": parent_x if parent_x else x["path"], "merged": True}
                del us[i + 1]
                changed = True
                break
    return us


def structure_chunks(doc_text, heads, starts, split_level, cap=1000, min_chars=0):
    """The structure chunks at one split level (min_chars > 0 adds the merge rule)."""
    us = units(doc_text, heads, split_level)
    if min_chars:
        us = merge_small(us, cap, min_chars, split_level)
    guard = heading_guard(doc_text, heads)
    chunks = []
    for u in us:
        pieces = balanced_split(doc_text, u["a"], u["b"], cap, guard)
        for k, (a, b) in enumerate(pieces):
            if not doc_text[a:b].strip():
                continue
            chunks.append({"a": a, "b": b, "text": doc_text[a:b], "path": u["path"], "merged": u["merged"],
                           "piece": k, "pieces": len(pieces), "page_segments": page_segments(starts, len(doc_text), a, b)})
    return chunks


def _only_headings(doc_text, heads, a, b):
    covered = [(h["start"], h["end"]) for h in heads if a <= h["start"] and h["end"] <= b]
    rest, pos = [], a
    for s, e in sorted(covered):
        rest.append(doc_text[pos:s])
        pos = e
    rest.append(doc_text[pos:b])
    return not "".join(rest).strip()


def check_invariants(doc_text, chunks, heads, split_level, cap):
    """Violations per invariant (all lists empty = pass): round trip, cap, gaps, crossing, page segments."""
    bad = {"round_trip": [], "cap": [], "gaps": [], "crossing": [], "segments": []}
    for i, c in enumerate(chunks):
        if doc_text[c["a"]:c["b"]] != c["text"]:
            bad["round_trip"].append(i)
        if c["b"] - c["a"] > cap:
            bad["cap"].append(i)
        segs = c["page_segments"]
        if not segs or segs[0][1] != c["a"] or segs[-1][2] != c["b"] or any(s[2] != t[1] for s, t in zip(segs, segs[1:])):
            bad["segments"].append(i)
    for x, y in zip(chunks, chunks[1:]):
        if y["a"] != x["b"] and doc_text[x["b"]:y["a"]].strip():
            bad["gaps"].append((x["b"], y["a"]))
    if chunks and doc_text[:chunks[0]["a"]].strip():
        bad["gaps"].append((0, chunks[0]["a"]))
    if chunks and doc_text[chunks[-1]["b"]:].strip():
        bad["gaps"].append((chunks[-1]["b"], len(doc_text)))
    bounds = sorted(h["start"] for h in heads if h["level"] <= split_level)
    for i, c in enumerate(chunks):
        if c["merged"]:
            continue
        for s in (s for s in bounds if c["a"] < s < c["b"]):
            if any(h["start"] >= c["a"] and h["end"] <= s for h in heads) and _only_headings(doc_text, heads, c["a"], s):
                continue
            bad["crossing"].append(i)
            break
    return bad


# ---------------------------------------------------------------------------------------------------------------- measures
def _median(xs):
    m = st.median(xs)
    return int(m) if float(m).is_integer() else round(float(m), 1)


def chunk_stats(chunks, cap, min_chars):
    ln = [c["b"] - c["a"] for c in chunks]
    if not ln:
        return {"n": 0, "min": None, "median": None, "max": None, "mean": None, "multi_page": 0, "hist": [], "width": 0,
                "under_min": 0, "under_min_pieces": 0, "over_cap": 0, "merged": 0, "split_units": 0}
    width = max(1, math.ceil(cap / 10))
    bins = [0] * 10
    for x in ln:
        bins[min(max(x - 1, 0) // width, 9)] += 1
    return {"n": len(ln), "min": min(ln), "median": _median(ln), "max": max(ln), "mean": round(sum(ln) / len(ln), 1),
            "multi_page": sum(1 for c in chunks if len({p for p, _, _ in c["page_segments"]}) > 1), "hist": bins, "width": width,
            "under_min": sum(1 for x in ln if x < min_chars),
            "under_min_pieces": sum(1 for c in chunks if c["b"] - c["a"] < min_chars and c["pieces"] > 1), "over_cap": sum(1 for x in ln if x > cap),
            "merged": sum(1 for c in chunks if c["merged"]), "split_units": sum(1 for c in chunks if c["pieces"] > 1 and c["piece"] == 0)}


def _held(chunks, a, b):
    return any(c["a"] <= a and b <= c["b"] for c in chunks)


def page_breaks(pages, starts, T, H):
    """Orphaned headings (a page ends in a detected heading) and mid-sentence cuts (no end mark, next page lower case),
    each with the span that must sit inside one chunk for the break to be repaired."""
    orphans, cuts, nonterm = [], [], 0
    for p in range(len(pages) - 1):
        tail = pages[p].rstrip()
        if tail[-1:] not in '.!?:"':
            nonterm += 1
        last_line = tail.split("\n")[-1].strip()
        hit = [x for x in H if x["page"] == p + 1 and x["title"].endswith(last_line) and T[x["end"]:starts[p + 1]].strip() == ""]
        body = next((i for i in range(starts[p + 1], len(T)) if not T[i].isspace()), None)
        if hit and tail:
            orphans.append({"break": f"{p + 1}->{p + 2}", "title": hit[-1]["title"],
                            "span": (hit[-1]["start"], body + 1) if body is not None else None})
        nxt = pages[p + 1].lstrip()
        if tail and tail[-1] not in '.!?:"' and nxt[:1].islower():
            cuts.append({"break": f"{p + 1}->{p + 2}", "span": (starts[p] + len(tail) - 1, body + 1)})
    return orphans, cuts, nonterm


def _gold(T, starts, pages, item, doc_id, single):
    """Evidence groups of one eval item as document offsets, or None if the item belongs to another document."""
    groups, mine = [], False
    for g in item.get("evidence_groups") or []:
        alts = []
        for alt in g.get("alternatives") or []:
            segs = []
            for sg in alt.get("segments") or []:
                if not single and str(sg.get("doc_id")) != doc_id:
                    continue
                try:
                    page, cs, ce = int(sg["page"]), int(sg["char_start"]), int(sg["char_end"])
                except (KeyError, TypeError, ValueError):
                    raise ValueError(f"{item['qid']}: a segment needs page, char_start, char_end") from None
                if not (1 <= page <= len(pages) and 0 <= cs < ce <= len(pages[page - 1])):
                    raise ValueError(f"{item['qid']}: segment page {page} [{cs}, {ce}) is outside the page text")
                segs.append((starts[page - 1] + cs, starts[page - 1] + ce))
                mine = True
            if segs:
                alts.append({"segs": segs, "quote": alt.get("quote")})
        if alts:
            groups.append(alts)
    return groups if mine else None


def _inside_one(segs, chunks):
    """alt ⊆ [c.a, c.b) for some chunk c: every segment of the alternative inside the same chunk."""
    return any(all(c["a"] <= x and y <= c["b"] for x, y in segs) for c in chunks)


def eval_rows(T, starts, pages, items, doc_id, single, v0, chosen):
    rows, other, unans, quotes = [], [], [], [0, 0]
    for it in items:
        if it.get("answerable") is False or not it.get("evidence_groups"):
            unans.append(it["qid"])
            continue
        groups = _gold(T, starts, pages, it, doc_id, single)
        if groups is None:
            other.append(it["qid"])
            continue
        for g in groups:
            for alt in g:
                if len(alt["segs"]) == 1 and alt["quote"]:
                    a, b = alt["segs"][0]
                    quotes[1] += 1
                    quotes[0] += " ".join(T[a:b].split()) == " ".join(str(alt["quote"]).split())
        straddle = any(not any(_inside_one(alt["segs"], v0) for alt in g) for g in groups)
        crosses = any(len({page_of(starts, x) for x, _ in alt["segs"]} | {page_of(starts, y - 1) for _, y in alt["segs"]}) > 1
                      for g in groups for alt in g)
        whole = all(any(_inside_one(alt["segs"], chosen) for alt in g) for g in groups) if chosen is not None else None
        rows.append({"qid": it["qid"], "category": it.get("category") or "-", "groups": len(groups),
                     "pages": sorted({page_of(starts, x) for g in groups for alt in g for x, _ in alt["segs"]}),
                     "straddles_v0": straddle, "crosses_page": crosses, "whole_in_structure": whole})
    return {"rows": rows, "other_doc": other, "unanswerable": unans, "quotes_ok": quotes[0], "quotes": quotes[1]}


def snapshot_id(doc_id, doc_text):
    """06 §5.3 recipe for one document (parser pymupdf, options {}, cleaning none, page join \\n)."""
    parts = ["snapshot-v1", f"parser=pymupdf@{pymupdf.VersionBind}", "options=" + json.dumps({}, sort_keys=True),
             "cleaning=none", "page_join=\\n", f"{doc_id}:{hashlib.sha256(doc_text.encode()).hexdigest()}"]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def _norm(t):
    return " ".join(str(t).split()).casefold()


# ---------------------------------------------------------------------------------------------------------------- the check
def analyse(path, doc_id, cap=1000, split_level="auto", min_chars=400, sample=10, seed=0, evalset=None, single=True):
    x = extract(path)
    pages, dicts = x["pages"], x["dicts"]
    starts = page_starts(pages)
    T = "\n".join(pages)
    n_pages = len(pages)
    r = {"name": Path(path).name, "doc_id": doc_id, "pages": n_pages, "chars": len(T), "snapshot_id": snapshot_id(doc_id, T),
         "toc": x["toc"], "tagged": x["tagged"], "marked": x["marked"], "creator": x["creator"], "producer": x["producer"]}

    # 1 fonts and the text layer
    hist = size_histogram(dicts)
    total = sum(hist.values())
    b = body_size(hist)
    per_size = Counter()
    for (size, _bold), n in hist.items():
        per_size[size] += n
    spans_by_size = Counter()
    for d in dicts:
        for blk in d["blocks"]:
            for line in blk.get("lines", []):
                for s in line["spans"]:
                    if s["text"].strip():
                        spans_by_size[round(s["size"], 2)] += 1
    r["fonts"] = [{"size": s, "bold": bo, "chars": n} for (s, bo), n in sorted(hist.items(), key=lambda kv: (-kv[0][0], not kv[0][1]))]
    r["body"] = b
    r["body_chars"] = per_size.get(b, 0) if b is not None else 0
    r["total_chars"] = total
    r["spans_by_size"] = dict(sorted(spans_by_size.items()))
    r["no_text"] = []
    for p, (t, lay) in enumerate(zip(pages, x["layout"]), 1):
        nonspace = len("".join(t.split()))
        if nonspace == 0 or (lay["images"] and nonspace < IMAGE_ONLY_TEXT):
            r["no_text"].append({"page": p, "images": lay["images"]})
    r["layout"] = {"two_col_pages": [p for p, lay in enumerate(x["layout"], 1) if lay["two_columns"]],
                   "jump_pages": {p: lay["rl_jumps"] for p, lay in enumerate(x["layout"], 1) if lay["rl_jumps"] >= JUMP_FLAG},
                   "max_jumps": max((lay["rl_jumps"] for lay in x["layout"]), default=0),
                   "tables": {p: lay["tables"] for p, lay in enumerate(x["layout"], 1) if lay["tables"]}}

    # 3 headings
    lines = line_records(dicts)
    bold_lines = [ln for ln in lines if ln["bold"]]
    pages_of_text = defaultdict(set)
    masked_pages, masked_count = defaultdict(set), Counter()
    for ln in lines:
        pages_of_text[ln["raw"].strip()].add(ln["page"])
        key = re.sub(r"\d+", "#", ln["raw"].strip())
        masked_pages[key].add(ln["page"])
        masked_count[key] += 1
    header_pages = max(REPEAT_PAGES, math.ceil((n_pages - len(r["no_text"])) / 2))
    repeated = sorted(t for t, ps in pages_of_text.items() if len(ps) >= REPEAT_PAGES)
    det = {rule: detect_headings(lines, b, rule) for rule in ("size", "size+bold")}
    sizes = heading_sizes(lines, b) if b is not None else []
    r["lines"] = {"text": len(lines), "bold": len(bold_lines), "bold_multi_span": sum(ln["spans"] > 1 for ln in bold_lines)}
    r["level_sizes"] = sizes
    r["levels"] = {rule: dict(sorted(Counter(h["level"] for h in hs).items())) for rule, hs in det.items()}
    r["n_heads"] = {rule: len(hs) for rule, hs in det.items()}
    r["wrapped"] = [{"page": h["page"], "title": h["title"], "lines": len(h["lines"])} for h in det["size+bold"] if len(h["lines"]) > 1]
    r["filtered_long"] = [ln["raw"].strip() for ln in bold_lines if len(ln["raw"].split()) > MAX_WORDS or ln["raw"].strip()[-1] in END_PUNCT]
    r["repeated_lines"] = [{"text": t, "pages": len(pages_of_text[t]), "bold": any(ln["bold"] for ln in lines if ln["raw"].strip() == t)}
                           for t in repeated]
    r["masked_repeats"] = []                   # running-header shape: once per page, on >= half the pages, only a number changes
    for h in det["size+bold"]:
        key = re.sub(r"\d+", "#", h["title"])
        if key != h["title"] and len(masked_pages[key]) >= header_pages and masked_count[key] == len(masked_pages[key]):
            r["masked_repeats"].append(h["title"])
    r["numbering"] = numbering(det["size+bold"])
    size_keys = {(h["page"], h["block"], h["last_line"]) for h in det["size"]}
    r["missed_by_size"] = [{"page": h["page"], "level": h["level"], "title": h["title"]} for h in det["size+bold"]
                           if (h["page"], h["block"], h["last_line"]) not in size_keys]

    # 5 alignment
    rebuilt = []
    for p, d in enumerate(dicts):
        built = "".join("".join(s["text"] for s in ln["spans"]) + "\n" for blk in d["blocks"] for ln in blk.get("lines", []))
        rebuilt.append(built == pages[p])
    r["rebuild_ok"] = sum(rebuilt)
    r["rebuild_differ"] = [p for p, ok in enumerate(rebuilt, 1) if not ok]
    H, failed = align(T, det["size+bold"])
    add_paths(H)
    r["aligned"], r["align_failed"] = len(H), failed
    r["on_own_page"] = sum(1 for h in H if page_of(starts, h["start"]) == h["page"])
    built = not failed
    titles = Counter(h["title"] for h in H)
    r["repeated_titles"] = [{"title": h["title"], "page": h["page"], "level": h["level"], "path": h["path"]}
                            for t in sorted(t for t, n in titles.items() if n > 1) for h in H if h["title"] == t]
    r["n_repeated_titles"] = len({x["title"] for x in r["repeated_titles"]})
    r["outline"] = [{"level": h["level"], "title": h["title"], "page": h["page"], "start": h["start"], "end": h["end"],
                     "path": h["path"]} for h in H]
    toc_titles = [_norm(t[1]) for t in x["toc"]]
    head_titles = {_norm(h["title"]) for h in H}
    r["toc_matched"] = sum(1 for t in toc_titles if t in head_titles)

    # 6 levels, auto, arms
    present = sorted({h["level"] for h in H})
    r["sections"] = {}
    for lv in present:
        ln = [e - s for s, e, _ in section_ranges(H, len(T), lv)]
        r["sections"][lv] = {"n": len(ln), "min": min(ln), "median": _median(ln), "max": max(ln), "mean": round(sum(ln) / len(ln), 1)}
    if split_level == "auto":
        ok = [lv for lv in present if r["sections"][lv]["median"] >= min_chars]
        chosen = max(ok) if ok else (min(present) if present else None)
        r["auto"] = True
    else:
        chosen = int(split_level)
        r["auto"] = False
    r["split_level"] = chosen
    v0 = v0_chunks(pages, starts)
    arms = {"v0 per-page 1000/200": v0, "cross-page recursive 1000/200": recursive_doc_chunks(T, starts)}
    struct_names = {}
    if built:
        levels = sorted(set(present) | ({chosen} if chosen else set())) or [1]
        for lv in levels:
            arms[f"L{lv}"] = structure_chunks(T, H, starts, lv, cap, 0)
            struct_names[f"L{lv}"] = (lv, H)
            if lv >= 2 and min_chars:
                arms[f"L{lv} + merge<{min_chars}"] = structure_chunks(T, H, starts, lv, cap, min_chars)
                struct_names[f"L{lv} + merge<{min_chars}"] = (lv, H)
        if chosen and det["size"]:
            Hs, fs = align(T, det["size"])
            if not fs:
                add_paths(Hs)
                arms[f"L{chosen}, size-only headings"] = structure_chunks(T, Hs, starts, chosen, cap, 0)
                struct_names[f"L{chosen}, size-only headings"] = (chosen, Hs)
    chosen_name = (f"L{chosen}" if chosen else "L1") if built else None
    r["chosen_arm"] = chosen_name
    r["arms"] = {name: chunk_stats(ch, cap, min_chars) for name, ch in arms.items()}
    r["invariants"] = {name: {k: len(v) for k, v in check_invariants(T, arms[name], hh, lv, cap).items()}
                       for name, (lv, hh) in struct_names.items()}
    so = f"L{chosen}, size-only headings"
    r["size_only_same"] = ([(c["a"], c["b"]) for c in arms[so]] == [(c["a"], c["b"]) for c in arms[chosen_name]]) if so in arms else None
    chosen_chunks = arms.get(chosen_name) if chosen_name else None

    # 7 page breaks
    orphans, cuts, nonterm = page_breaks(pages, starts, T, H)
    r["orphans"] = [o["break"] for o in orphans]
    r["cuts"] = [c["break"] for c in cuts]
    r["nonterminal_breaks"] = nonterm
    r["kept_whole"] = {name: {"orphans": sum(1 for o in orphans if o["span"] and _held(ch, *o["span"])),
                              "cuts": sum(1 for c in cuts if c["span"] and _held(ch, *c["span"]))}
                       for name, ch in arms.items()}

    # 8 eval set
    r["evalset"] = eval_rows(T, starts, pages, evalset, doc_id, single, v0, chosen_chunks) if evalset is not None else None

    # 9 inspection sample
    r["sample"] = []
    if chosen_chunks:
        head_starts = {h["start"] for h in H}
        for i in sorted(random.Random(seed).sample(range(len(chosen_chunks)), min(sample, len(chosen_chunks)))):
            c = chosen_chunks[i]
            starts_head = c["a"] in head_starts
            clean_cont = c["piece"] > 0 and T[:c["a"]].rstrip()[-1:] in SENT_END
            ends = c["text"].rstrip()[-1:] in SENT_END
            r["sample"].append({"id": i, "a": c["a"], "b": c["b"], "chars": c["b"] - c["a"],
                                "pages": [p for p, _, _ in c["page_segments"]], "path": c["path"], "piece": c["piece"] + 1,
                                "pieces": c["pieces"], "merged": c["merged"], "starts_heading": starts_head,
                                "clean_continuation": clean_cont, "ends_sentence": ends,
                                "auto_ok": (starts_head or clean_cont) and ends, "text": c["text"]})
    r["_arms"] = arms
    r["_heads"] = H
    r["checklist"] = checklist(r, cap, min_chars)
    r["recommendation"] = recommend(r, min_chars)
    return r


def run_check(pdfs, cap=1000, split_level="auto", min_chars=400, sample=10, seed=0, evalset=None, doc_ids=None):
    """Check one or more PDFs. Raises FileNotFoundError / ValueError on bad input."""
    if not isinstance(cap, int) or cap <= 0:
        raise ValueError("--cap must be a positive whole number of characters")
    if min_chars < 0:
        raise ValueError("--min-chars must be >= 0")
    if sample < 0:
        raise ValueError("--sample must be >= 0")
    if split_level != "auto" and str(split_level) not in ("1", "2", "3", "4"):
        raise ValueError("--split-level must be auto, 1, 2, 3 or 4")
    files = find_pdfs(pdfs)
    if doc_ids and len(doc_ids) != len(files):
        raise ValueError(f"--doc-ids gives {len(doc_ids)} ids for {len(files)} PDF(s)")
    ids = list(doc_ids) if doc_ids else [f.stem for f in files]
    if len(set(ids)) != len(ids):
        raise ValueError("two PDFs have the same id; pass --doc-ids")
    items = load_evalset(evalset) if evalset else None
    res = {"settings": {"cap": cap, "split_level": str(split_level), "min_chars": min_chars, "sample": sample, "seed": seed,
                        "evalset": Path(evalset).name if evalset else None, "pymupdf": pymupdf.VersionBind},
           "files": [analyse(f, i, cap, split_level, min_chars, sample, seed, items, len(files) == 1) for f, i in zip(files, ids)]}
    return res


# ---------------------------------------------------------------------------------------------------------------- checklist
CHECKS = {
    "S1": ("Text layer on every page (no scans)",
           "Count non-space characters per page; a page with none, or with an image and under 50, has no usable text "
           "layer. Open it: a scan needs OCR or a layout parser (S2) before any structure can be read."),
    "S2": ("Body size is clear (one size holds >= 50% of characters)",
           "Read the font histogram (section 1): the body size should dominate. If two sizes share the text, "
           "levels by size rank are unreliable."),
    "S3": ("At least two heading levels; a plausible heading count",
           "Read the per-level counts (section 3): between 1 heading per 3 pages and 15 per page; if headings are "
           "numbered, the numbering depth should map to one level each."),
    "S4": ("Size only vs size + bold: the difference is small or explained",
           "Read the list of bold body-size headings size-only misses (section 3): real sub-headings, or bold "
           "phrases that are not headings? Size + bold keeps them; size only would merge them into the body."),
    "S5": ("Outline (get_toc) present and matching the headings (>= 90%)",
           "Compare the outline titles with the detected headings; if they match, the outline is the cleaner source. "
           "Without an outline, a tagged PDF can be compared by eye in a viewer's tag panel."),
    "S6": ("Every heading aligns to an exact snapshot offset",
           "Every heading line must be found in doc_text with a moving cursor (section 5); one miss stops the build "
           "(fail closed). Check that dict lines rebuild get_text() on every page."),
    "S7": ("Single column, or columns handled before detection (C1)",
           "Two-column pages (long blocks in both halves) and right-to-left jumps (section 4); open one page by eye. "
           "Fix reading order (C1 column clipping) before trusting headings or chunks."),
    "S8": ("No running headers or footers detected as headings",
           "Lines on >= 3 pages are excluded; also look for headings that repeat with only a number changed "
           "(page numbers) and for headings at the very top or bottom of every page."),
    "S9": ("Chunk sizes: none over the cap, < 10% under the minimum",
           "Chunk statistics at the chosen split level (section 6); count tokens with your embedder's tokenizer "
           "(embed_fit_check.py) so no chunk passes its limit."),
    "S10": ("10 random chunks pass the inspection sheet",
            "Fill the sheet (--sheet): each chunk starts at a heading or a clean continuation, has the right path, and "
            "ends at a sentence unless the cap forced the cut. 8 of 10 or better before measuring."),
    "S11": ("Tables detected and kept whole, or flagged for C7/S2",
            "find_tables() counts ruled tables per page (section 4); open those pages and check that a table is not cut "
            "across chunks. Tables without ruling lines are not found: glance at the pages."),
}


def checklist(r, cap, min_chars):
    out = []

    def add(cid, verdict, evidence):
        title, how = CHECKS[cid]
        out.append({"id": cid, "check": title, "verdict": verdict, "evidence": evidence, "how": how})

    n_pages, nt = r["pages"], r["no_text"]
    img = [x["page"] for x in nt if x["images"]]
    blank = [x["page"] for x in nt if not x["images"]]
    ev = f"{n_pages - len(nt)} of {n_pages} pages have a text layer" + (
        f"; image-only: {_pp(img)}" if img else "") + (f"; blank: {_pp(blank)}" if blank else "")
    add("S1", FAIL if len(nt) * 2 > n_pages else (WARN if nt else PASS), ev)

    tot = r["total_chars"]
    if r["body"] is None or not tot:
        add("S2", FAIL, "no characters in any span")
    else:
        share = r["body_chars"] / tot
        add("S2", PASS if share >= BODY_SHARE else WARN, f"body size {r['body']}: {r['body_chars']:,} of {tot:,} characters ({100 * share:.1f}%)")

    n_h = r["n_heads"]["size+bold"]
    lv = r["levels"]["size+bold"]
    lo, hi = n_pages * MIN_PER_PAGE, n_pages * MAX_PER_PAGE
    num = r["numbering"]
    ev = (f"{n_h} headings on {n_pages} page(s) ({n_h / n_pages:.1f} per page), {len(lv)} level(s): "
          + (", ".join(f"L{k} {v}" for k, v in lv.items()) or "none"))
    if num["n"]:
        ev += (f"; numbered headings {num['n']}, numbering depth -> level "
               + ", ".join(f"{d}->{'/'.join(f'L{x}' for x in v)}" for d, v in num["depth_to_levels"].items())
               + (" (consistent)" if num["consistent"] else " (does not match the levels)"))
    if not n_h:
        add("S3", FAIL, ev)
    else:
        add("S3", PASS if len(lv) >= 2 and lo <= n_h <= hi and (num["consistent"] or not num["n"]) else WARN, ev)

    miss = len(r["missed_by_size"])
    if not n_h:
        add("S4", PASS, "no headings found by either detector")
    else:
        share = miss / n_h
        ev = f"size only {r['n_heads']['size']}, size + bold {n_h}: size only misses {miss} of {n_h} ({100 * share:.1f}%)"
        if r["size_only_same"] is not None:
            ev += f"; at L{r['split_level']} size only gives {'the same' if r['size_only_same'] else 'different'} chunks"
        add("S4", PASS if share < DISAGREE else MANUAL, ev + ("" if share < DISAGREE else "; read the list in section 3"))

    toc = r["toc"]
    tags = "tagged (StructTreeRoot" + (", MarkInfo Marked true" if r["marked"] else "") + ")" if r["tagged"] else "not tagged"
    if toc:
        share = r["toc_matched"] / len(toc)
        add("S5", PASS if share >= TOC_MATCH else WARN, f"outline {len(toc)} entries; {r['toc_matched']} ({100 * share:.0f}%) match a detected heading; {tags}")
    else:
        add("S5", MANUAL if r["tagged"] else WARN, f"no outline (get_toc() = []); {tags}" +
            ("; compare a few tagged headings by eye" if r["tagged"] else "; typography is the only heading source"))

    total_h = r["aligned"] + len(r["align_failed"])
    ev = f"aligned {r['aligned']} of {total_h}; dict lines rebuild get_text() on {r['rebuild_ok']} of {n_pages} pages"
    if r["align_failed"]:
        f0 = r["align_failed"][0]
        ev += f"; first miss: {f0['title']!r} p.{f0['page']} ({f0['why']}); no structure chunks built"
    add("S6", FAIL if r["align_failed"] else PASS, ev)

    L = r["layout"]
    ev = f"two-column pages: {_pp(L['two_col_pages']) or 'none'}; most right-to-left jumps on a page: {L['max_jumps']}"
    if L["jump_pages"]:
        ev += f" (>= {JUMP_FLAG} on {_pp(sorted(L['jump_pages']))})"
    add("S7", FAIL if L["jump_pages"] else (WARN if L["two_col_pages"] else PASS), ev)

    rep = r["repeated_lines"]
    ev = f"{len(rep)} line(s) repeat on >= {REPEAT_PAGES} pages and are excluded" + (
        ": " + "; ".join(f"{x['text'][:40]!r} ({x['pages']} pages)" for x in rep[:3]) if rep else "")
    if r["masked_repeats"]:
        ev += f"; headings that repeat with only a number changed: {', '.join(repr(t) for t in r['masked_repeats'][:3])}"
    add("S8", WARN if r["masked_repeats"] else PASS, ev)

    name = r["chosen_arm"]
    if not name:
        add("S9", FAIL, "no structure chunks were built (S6)")
    else:
        s = r["arms"][name]
        inv = sum(r["invariants"][name].values())
        merge = f"L{r['split_level']} + merge<{min_chars}"
        ev = (f"{name}: {s['n']} chunks, {s['min']}/{s['median']}/{s['max']} characters; over the cap {cap}: {s['over_cap']}; "
              f"under {min_chars}: {s['under_min']} ({100 * s['under_min'] / max(s['n'], 1):.1f}%)")
        if merge in r["arms"]:
            m = r["arms"][merge]
            ev += f"; with merge: {m['under_min']} of {m['n']} ({100 * m['under_min'] / max(m['n'], 1):.1f}%)"
        ev += f"; invariant violations {inv}; tokens not counted here"
        verdict = FAIL if s["over_cap"] or inv else (WARN if s["n"] and s["under_min"] / s["n"] >= SMALL_SHARE else PASS)
        add("S9", verdict, ev)

    smp = r["sample"]
    if not smp:
        add("S10", MANUAL, "no sample (no chunks, or --sample 0)")
    else:
        ok = sum(x["auto_ok"] for x in smp)
        ev = (f"automatic pre-check: {ok} of {len(smp)} start at a heading or a clean continuation and end at a sentence "
              f"(chunks {', '.join(str(x['id']) for x in smp)}); paths and content need your eye")
        add("S10", WARN if ok < INSPECT_PASS * len(smp) else MANUAL, ev)

    tb = L["tables"]
    add("S11", WARN if tb else PASS, (f"find_tables(): {sum(tb.values())} table(s) on {_pp(sorted(tb))}" if tb else "find_tables(): no ruled table found"))
    return out


def _pp(pages):
    if not pages:
        return ""
    return ("p." if len(pages) == 1 else "pp.") + ", ".join(str(p) for p in pages[:12]) + (f" … ({len(pages)} pages)" if len(pages) > 12 else "")


def recommend(r, min_chars):
    """The main route (first matching rule wins), then notes."""
    c = {x["id"]: x["verdict"] for x in r["checklist"]}
    lv = r["split_level"]
    sec = r["sections"].get(lv) if lv else None
    why = (f"the deepest level whose median section >= {min_chars} characters (median {sec['median']:,})" if r["auto"] and sec
           else ("chosen with --split-level" if not r["auto"] else "no level reaches the minimum; the shallowest level"))
    if c["S1"] == FAIL:
        main = "No structure: use v1.0 recursive (or OCR / a layout parser, S2)."
    elif c["S7"] == FAIL:
        main = "Fix reading order first (C1): the text runs across the columns, so headings and chunks would be wrong."
    elif c["S6"] == FAIL:
        main = "Do not use yet: a heading could not be aligned to the snapshot (fail closed). Fix the extraction (S6), then re-run."
    elif c["S5"] == PASS:
        main = f"Use the outline as the heading source (it matches the typography); split at L{lv} ({why})."
    elif c["S2"] == PASS and c["S3"] == PASS and c["S4"] in (PASS, MANUAL):
        main = f"Typography route (size + bold) at split level L{lv}: {why}."
    else:
        bad = ", ".join(k for k in ("S2", "S3", "S4") if c[k] not in (PASS, MANUAL))
        main = (f"Structure unclear ({bad}): read the heading list; if the headings are numbered, use the numbering depth as "
                "the level; otherwise keep v1.0 recursive.")
    notes = []
    if c["S1"] == WARN:
        notes.append("Some pages have no text layer: they are invisible to every chunker (OCR them, S2).")
    if c["S7"] == WARN:
        notes.append("Two-column pages read column by column here; check one page by eye (C1).")
    if c["S4"] == MANUAL:
        notes.append("Read the bold body-size headings: size-only detection (pymupdf4llm-style) would miss them.")
    if r["n_repeated_titles"]:
        notes.append(f"Duplicate titles found ({r['n_repeated_titles']}): keep `section_path`; consider I5 headers.")
    if c["S8"] == WARN:
        notes.append("A heading repeats with only a number changed: probably a running header; exclude it before chunking.")
    if c["S9"] == WARN:
        s = r["arms"][r["chosen_arm"]]
        m = r["arms"].get(f"{r['chosen_arm']} + merge<{min_chars}")
        if m and m["n"] and m["under_min"] / m["n"] < SMALL_SHARE:
            notes.append(f"{s['under_min']} of {s['n']} chunks are under {min_chars} characters; with merge, {m['under_min']} of "
                         f"{m['n']}: consider the merge rule at L{r['split_level']}.")
        else:
            notes.append(f"{s['under_min']} of {s['n']} chunks are under {min_chars} characters ({s['under_min_pieces']} of them are "
                         "pieces of split sections, which merge cannot join): accept them, or compare a shallower level or a larger cap.")
    if c["S10"] == WARN:
        notes.append("Do not measure yet: parsing errors will show up as false negatives (06 v1.1).")
    elif c["S10"] == MANUAL and r["sample"]:
        notes.append(f"Fill the inspection sheet; fewer than {int(INSPECT_PASS * 10)} of 10 passing means do not measure yet.")
    if c["S11"] == WARN:
        notes.append("Tables found: keep them whole, or flag them for C7/S2.")
    ev = r["evalset"]
    if ev is not None and ev["rows"]:
        bucket = sum(1 for x in ev["rows"] if x["straddles_v0"] or x["crosses_page"])
        if not bucket:
            notes.append(f"Eval set: 0 of {len(ev['rows'])} items straddle a v0 chunk or cross a page, so a retrieval comparison "
                         "cannot show what structure chunking fixes; add such items (M1) and expect \"inconclusive\" until then.")
        else:
            notes.append(f"Eval set: {bucket} of {len(ev['rows'])} items straddle a v0 chunk or cross a page; report CE@k for that "
                         "bucket separately, at fixed k and at equal budget.")
    return {"main": main, "notes": notes}


# ---------------------------------------------------------------------------------------------------------------- report
def _f(x):
    if x is None:
        return "-"
    return f"{x:,}" if isinstance(x, int) else (f"{x:,.1f}" if isinstance(x, float) else str(x))


def _path(p):
    return " > ".join(p) if p else "(before the first heading)"


def render_report(res):
    st_ = res["settings"]
    multi = len(res["files"]) > 1
    o = ["# Structure fit check", "",
         "**What this is:** an automatic check of whether structure-aware chunking (cut at the document's own headings) "
         "works on these PDFs, and with what split level, measured on your own files.",
         "**What this is not:** a retrieval evaluation. Whether the structure chunks retrieve better is an experiment "
         "(CE@k at fixed k and at equal budget, by bucket).", ""]
    for r in res["files"]:
        cl = " ".join(f"{x['id']} {x['verdict']}" for x in r["checklist"])
        o.append(f"**Recommendation{' for `' + r['name'] + '`' if multi else ''}:** {r['recommendation']['main'].rstrip('.')} "
                 f"(section 11). Checklist: {cl}.")
        o.append("")
    o += [f"Settings: cap {st_['cap']:,} characters, no overlap inside a unit · split level {st_['split_level']} · "
          f"min-chars {st_['min_chars']} · sample {st_['sample']}, seed {st_['seed']}"
          + (f" · eval set `{st_['evalset']}`" if st_["evalset"] else "")
          + f" · baseline v0 = per-page recursive {V0_SIZE}/{V0_OVERLAP} · pymupdf {st_['pymupdf']}, `page.get_text()`, "
          "pages joined with `\"\\n\"`. No API call.",
          "Documents: " + "; ".join(f"`{r['name']}` (id `{r['doc_id']}`, {r['pages']} page(s), {r['chars']:,} characters, "
                                    f"snapshot_id `{r['snapshot_id']}`)" for r in res["files"]) + ".", ""]
    for r in res["files"]:
        o += _file_sections(r, st_, multi)
    o += ["", "Lesson: `study/lessons/I2_structure_chunking.html`. This report checks whether the structure can be "
          "recovered and what the chunks look like; it is not a retrieval result."]
    return "\n".join(o) + "\n"


def _h(n, title, r, multi):
    return f"## {n} {title}" + (f" · `{r['name']}`" if multi else "")


def _file_sections(r, st_, multi):
    cap, mc = st_["cap"], st_["min_chars"]
    o = []
    # 1
    o += [_h(1, "Fonts and body size", r, multi), "", "| Size | Bold | Characters | Share |", "|---|---|---|---|"]
    tot = r["total_chars"] or 1
    for f in r["fonts"]:
        o.append(f"| {f['size']:.2f} | {'yes' if f['bold'] else 'no'} | {f['chars']:,} | {100 * f['chars'] / tot:.1f}% |")
    o += ["", f"Body size: **{r['body']}** (the size with the most characters: {r['body_chars']:,} of {r['total_chars']:,}). "
          f"Spans per size: {', '.join(f'{k} → {v:,}' for k, v in r['spans_by_size'].items()) or 'none'}. "
          f"Pages without a text layer: {_pp([x['page'] for x in r['no_text']]) or 'none'}.", ""]
    # 2
    o += [_h(2, "Structure sources", r, multi), "",
          f"- Outline (`get_toc()`): {len(r['toc'])} entries" + (f"; {r['toc_matched']} match a detected heading" if r["toc"] else " (no outline)") + ".",
          f"- Tags: StructTreeRoot {'present' if r['tagged'] else 'absent'}; MarkInfo Marked {'true' if r['marked'] else 'not set'} "
          "(read-only: this tool does not use the tags).",
          f"- Creator: {r['creator'] or '-'}; producer: {r['producer'] or '-'}.", ""]
    # 3
    lv_s, lv_b = r["levels"]["size"], r["levels"]["size+bold"]
    levels = sorted(set(lv_s) | set(lv_b))
    o += [_h(3, "Headings", r, multi), "",
          f"Text lines {r['lines']['text']:,} · all-bold lines {r['lines']['bold']:,} · bold lines with more than one span {r['lines']['bold_multi_span']}.", "",
          "| Level | Font | Size only | Size + bold |", "|---|---|---|---|"]
    sizes = r["level_sizes"]
    for lv in levels:
        font = f"{sizes[lv - 1]:.2f} bold" if lv <= len(sizes) else f"{r['body']} bold (body size)"
        o.append(f"| L{lv} | {font} | {lv_s.get(lv, 0)} | {lv_b.get(lv, 0)} |")
    n_b = r["n_heads"]["size+bold"]
    miss = r["missed_by_size"]
    o += [f"| all | | **{r['n_heads']['size']}** | **{n_b}** |", "",
          f"Size only misses **{len(miss)} of {n_b}**" + (f" ({100 * len(miss) / n_b:.1f}%)" if n_b else "") + ": bold lines at the body size.",
          f"Wrapped headings joined: {len(r['wrapped'])}" + (": " + "; ".join(f"p.{w['page']} {w['title']!r} ({w['lines']} lines)" for w in r["wrapped"][:5]) if r["wrapped"] else "") + ".",
          f"Bold lines removed by the filters (> {MAX_WORDS} words or a final . ! ?): {len(r['filtered_long'])}"
          + (": " + "; ".join(repr(t[:50]) for t in r["filtered_long"][:5]) if r["filtered_long"] else "") + ".",
          f"Lines repeated on >= {REPEAT_PAGES} pages (never headings): {len(r['repeated_lines'])}"
          + (": " + "; ".join(f"{x['text'][:50]!r} ({x['pages']} pages{', bold' if x['bold'] else ''})" for x in r["repeated_lines"][:5]) if r["repeated_lines"] else "") + ".",
          f"Numbered headings: {r['numbering']['n']}" + (
              f"; numbering depth → level: {', '.join(f'{d} → ' + '/'.join(f'L{x}' for x in v) for d, v in r['numbering']['depth_to_levels'].items())} "
              f"({'consistent' if r['numbering']['consistent'] else 'not consistent with the levels'})" if r["numbering"]["n"] else "") + ".", ""]
    if miss:
        o += [f"The headings size only misses (first {min(30, len(miss))} of {len(miss)}; read them for S4):", ""]
        o += [f"- p.{m['page']} L{m['level']} {m['title']}" for m in miss[:30]]
        if len(miss) > 30:
            o.append(f"- … {len(miss) - 30} more (`--json` lists all headings)")
        o.append("")
    # 4
    L = r["layout"]
    o += [_h(4, "Layout: columns and tables", r, multi), "",
          f"- Two-column pages (text blocks of {LONG_BLOCK}+ characters starting in both halves): {_pp(L['two_col_pages']) or 'none'}.",
          f"- Right-to-left jumps (a line in the right half followed by one in the left half): most on one page {L['max_jumps']}"
          + (f"; {JUMP_FLAG} or more on {_pp(sorted(L['jump_pages']))}" if L["jump_pages"] else "") + ".",
          f"- Ruled tables (`find_tables()`): " + (", ".join(f"p.{p}: {n}" for p, n in L["tables"].items()) if L["tables"] else "none") + ".", ""]
    # 5
    o += [_h(5, "Alignment and the outline", r, multi), "",
          f"`dict` lines, each + `\"\\n\"`, rebuild `get_text()` on **{r['rebuild_ok']} of {r['pages']}** pages"
          + (f" (differ: {_pp(r['rebuild_differ'])})" if r["rebuild_differ"] else "") + ". "
          f"Aligned **{r['aligned']} of {r['aligned'] + len(r['align_failed'])}** headings (cursor + find); "
          f"{r['on_own_page']} lie on their own page."]
    if r["align_failed"]:
        o += ["", "Not found (fail closed, no structure chunks):", ""] + [f"- p.{f['page']} {f['title']!r}: {f['why']}" for f in r["align_failed"][:10]]
    o.append("")
    if r["repeated_titles"]:
        o += [f"Repeated titles: **{r['n_repeated_titles']}** (the path, not the title, identifies a section).", "",
              "| Title | Page | Level | Parent path |", "|---|---|---|---|"]
        o += [f"| {x['title']} | {x['page']} | L{x['level']} | {_path(x['path'][:-1])} |" for x in r["repeated_titles"]]
        o.append("")
    else:
        o += ["Repeated titles: none.", ""]
    lv = r["split_level"]
    if r["outline"] and lv:
        H = r["outline"]
        o += [f"The outline down to the split level L{lv} (offset, page, section length; deeper headings counted):", "", "```text"]
        for i, h in enumerate(H):
            if h["level"] > lv:
                continue
            nxt = next((g["start"] for g in H[i + 1:] if g["level"] <= h["level"]), r["chars"])
            j = i + 1
            sub = 0
            while j < len(H) and H[j]["level"] > h["level"]:
                sub += H[j]["level"] > lv
                j += 1
            o.append(f"{'  ' * (h['level'] - 1)}L{h['level']} {h['title']}  @{h['start']:,}  p.{h['page']}  {nxt - h['start']:,} chars"
                     + (f"  (+{sub} deeper)" if sub and h["level"] == lv else ""))
        o += ["```", ""]
    # 6
    o += [_h(6, "Chunks per split level", r, multi), ""]
    if r["sections"]:
        o += ["| Level | Sections | Length min / median / max | Mean | Median >= min-chars |", "|---|---|---|---|---|"]
        for k, s in r["sections"].items():
            o.append(f"| L{k} | {s['n']} | {s['min']:,} / {_f(s['median'])} / {s['max']:,} | {s['mean']:,.1f} | {'yes' if s['median'] >= mc else 'no'} |")
        o += ["", f"Split level: **L{lv}**" + (f" (auto: the deepest level whose median section >= {mc})" if r["auto"] else " (--split-level)") + ".", ""]
    else:
        o += ["No headings: every structure arm is one unit cut by the balanced split.", ""]
    w = next(iter(r["arms"].values()))["width"] or 1
    o += [f"| Arm | Chunks | Length min / median / max | Mean | On 2+ pages | Units split | Merged | Under {mc} | Over cap | Histogram ({w}-char bins) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for name, s in r["arms"].items():
        mark = "**" if name == r["chosen_arm"] else ""
        cap_cell = s["over_cap"] if not name.startswith(("v0", "cross")) else "-"
        o.append(f"| {mark}{name}{mark} | {s['n']} | {_f(s['min'])} / {_f(s['median'])} / {_f(s['max'])} | {_f(s['mean'])} | "
                 f"{s['multi_page']} | {s['split_units'] if not name.startswith(('v0', 'cross')) else '-'} | {s['merged']} | "
                 f"{s['under_min']} | {cap_cell} | {','.join(map(str, s['hist']))} |")
    o += ["", "v0 and the cross-page control are per-page / whole-text recursive 1000/200 (with overlap), for comparison. "
          "Structure arms have no overlap; a merged chunk joins small sibling units.", ""]
    if r["size_only_same"] is not None:
        o += [f"At L{lv}, the size-only headings give {'**the same chunks**' if r['size_only_same'] else '**different chunks**'} as size + bold.", ""]
    if r["invariants"]:
        o += ["Invariants (round trip `doc_text[a:b] == text`, cap, gaps, crossing a split-level boundary, page segments):", "",
              "| Arm | Round trip | Cap | Gaps | Crossing | Segments |", "|---|---|---|---|---|---|"]
        o += [f"| {n} | {v['round_trip']} | {v['cap']} | {v['gaps']} | {v['crossing']} | {v['segments']} |" for n, v in r["invariants"].items()]
        o.append("")
    # 7
    o += [_h(7, "Page breaks", r, multi), "",
          f"Orphaned headings (a page ends in a heading): **{len(r['orphans'])}**" + (f": {', '.join(r['orphans'])}" if r["orphans"] else "") + ".",
          f"Mid-sentence page cuts (no end mark, next page starts lower case): **{len(r['cuts'])}**" + (f": {', '.join(r['cuts'])}" if r["cuts"] else "") + ".",
          f"Page breaks not ending in . ! ? : or a quote: {r['nonterminal_breaks']} of {max(r['pages'] - 1, 0)}.", ""]
    if r["orphans"] or r["cuts"]:
        o += ["Kept whole in one chunk (heading + first body character; the last character before a cut + the first after):", "",
              "| Arm | Orphans kept with their body | Cuts kept whole |", "|---|---|---|"]
        o += [f"| {n} | {v['orphans']} of {len(r['orphans'])} | {v['cuts']} of {len(r['cuts'])} |" for n, v in r["kept_whole"].items()]
        o.append("")
    # 8
    ev = r["evalset"]
    o += [_h(8, "Eval set", r, multi), ""]
    if ev is None:
        o += ["No eval set given (use `--evalset` with M1 / seed JSONL).", ""]
    else:
        rows = ev["rows"]
        o += [f"{len(rows)} answerable item(s) on this document; {len(ev['unanswerable'])} unanswerable skipped"
              + (f"; {len(ev['other_doc'])} on other documents" if ev["other_doc"] else "")
              + f". Single-segment quotes that match the snapshot: {ev['quotes_ok']} of {ev['quotes']}.", ""]
        if rows:
            o += [f"| Item | Category | Groups | Pages | straddles_v0 | crosses_page | Whole in an L{lv} chunk |", "|---|---|---|---|---|---|---|"]
            o += [f"| {x['qid']} | {x['category']} | {x['groups']} | {', '.join(map(str, x['pages']))} | {_yn(x['straddles_v0'])} | "
                  f"{_yn(x['crosses_page'])} | {_yn(x['whole_in_structure'])} |" for x in rows]
            o += ["", f"**straddles_v0: {sum(x['straddles_v0'] for x in rows)} of {len(rows)} · crosses_page: "
                  f"{sum(x['crosses_page'] for x in rows)} of {len(rows)}.** straddles_v0 = some evidence group has no alternative that "
                  "lies inside one v0 chunk; crosses_page = an alternative's evidence runs over a page break. These are the items structure "
                  "chunking can change.", ""]
    # 9
    o += [_h(9, "Inspection sample", r, multi), ""]
    if r["sample"]:
        o += [f"{len(r['sample'])} random L{lv} chunks (`random.Random({st_['seed']}).sample`), with the automatic pre-check. "
              "The text and the verdict boxes are in the inspection sheet (`--sheet`).", "",
              "| Chunk | [a, b) | Chars | Pages | Piece | Path | Starts at heading | Ends at sentence |", "|---|---|---|---|---|---|---|---|"]
        o += [f"| {x['id']} | [{x['a']:,}, {x['b']:,}) | {x['chars']} | {', '.join(map(str, x['pages']))} | {x['piece']}/{x['pieces']} | "
              f"{_path(x['path'])} | {_yn(x['starts_heading']) + (' (continuation)' if x['clean_continuation'] and not x['starts_heading'] else '')} | "
              f"{_yn(x['ends_sentence'])} |" for x in r["sample"]]
        o.append("")
    else:
        o += ["No sample.", ""]
    # 10, 11
    o += [_h(10, "Checklist", r, multi), "", "| Check | Verdict | Evidence | How to check |", "|---|---|---|---|"]
    o += [f"| {x['id']} {x['check']} | {x['verdict']} | {x['evidence']} | {x['how']} |" for x in r["checklist"]]
    o += ["", "PASS fine · WARN look before you rely on it · FAIL fix first · MANUAL needs your eye (the evidence helps).", "",
          _h(11, "Recommendation", r, multi), "", r["recommendation"]["main"], ""]
    o += [f"- {n}" for n in r["recommendation"]["notes"]]
    o += ["", "Order of the rules: S1 text layer → S7 reading order → S6 alignment → S5 outline → S2–S4 typography → unclear.", ""]
    return o


def _lv(r):
    return f"L{r['split_level']}" if r["split_level"] else "none (no headings)"


def _yn(x):
    return "-" if x is None else ("yes" if x else "no")


def render_sheet(res):
    st_ = res["settings"]
    o = ["# Inspection sheet: structure chunks", "",
         "**What this is:** random chunks from the chosen split level, to read by eye (checklist S10). The automatic "
         "pre-check only looks at the first and last characters; the path and the content need you.",
         f"**How:** for each chunk tick what holds, then write pass or fail. 8 of 10 or better before you measure "
         f"retrieval; fewer means parsing errors would show up as false negatives. Settings: cap {st_['cap']:,}, split level "
         f"{st_['split_level']}, seed {st_['seed']}.", ""]
    for r in res["files"]:
        o += [f"## `{r['name']}` · split level {_lv(r)} · snapshot_id `{r['snapshot_id']}`", ""]
        if not r["sample"]:
            o += ["No chunks to inspect.", ""]
            continue
        for x in r["sample"]:
            pages = ", ".join(map(str, x["pages"]))
            o += [f"### Chunk {x['id']} · [{x['a']:,}, {x['b']:,}) · {x['chars']} characters · page{'s' if len(x['pages']) > 1 else ''} {pages} · "
                  f"piece {x['piece']}/{x['pieces']}" + (" · merged" if x["merged"] else ""), "",
                  f"Path: {_path(x['path'])}", "",
                  f"Pre-check: starts at a heading {_yn(x['starts_heading'])}"
                  + (", clean continuation yes" if x["clean_continuation"] else "") + f"; ends at a sentence {_yn(x['ends_sentence'])}.", "",
                  "```text", x["text"].rstrip("\n"), "```", "",
                  "- [ ] Starts at a heading, or continues cleanly from the previous piece",
                  "- [ ] The path is right for this text",
                  "- [ ] Ends at a sentence end (or the cap forced the cut)",
                  "- [ ] Holds no text from another section (unless merged)", "",
                  "Verdict: pass / fail · Note:", ""]
        o += [f"**Passed: ___ of {len(r['sample'])}** (S10 needs {math.ceil(INSPECT_PASS * len(r['sample']))} or more).", ""]
    return "\n".join(o) + "\n"


def to_json(res):
    def clean(r):
        out = {k: v for k, v in r.items() if not k.startswith("_")}
        out["sample"] = [{k: v for k, v in x.items() if k != "text"} for x in r["sample"]]
        out["sections"] = {f"L{k}": v for k, v in r["sections"].items()}
        out["levels"] = {rule: {f"L{k}": v for k, v in d.items()} for rule, d in r["levels"].items()}
        out["chunks"] = [{"a": c["a"], "b": c["b"], "pages": [p for p, _, _ in c["page_segments"]], "path": c["path"],
                          "piece": c["piece"] + 1, "pieces": c["pieces"], "merged": c["merged"]}
                         for c in (r["_arms"].get(r["chosen_arm"]) or [])] if r["chosen_arm"] else []
        return out
    return json.dumps({"settings": res["settings"], "files": [clean(r) for r in res["files"]]}, indent=1, ensure_ascii=False, default=str) + "\n"


# ---------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Will structure-aware chunking work on my PDFs, and with what settings? "
                                             "Reads the headings from the typography, chunks at a split level, and writes a "
                                             "Markdown report with the S1-S11 checklist. No API calls.")
    ap.add_argument("--pdf", nargs="+", required=True, help="one or more PDF files or folders")
    ap.add_argument("--doc-ids", default="", help="comma-separated document ids (default: file stems); used for the snapshot_id and the eval set's doc_id")
    ap.add_argument("--cap", type=int, default=1000, help="maximum chunk length in characters (default 1000)")
    ap.add_argument("--split-level", default="auto", choices=("auto", "1", "2", "3", "4"),
                    help="heading level to cut at; auto = the deepest level whose median section >= --min-chars")
    ap.add_argument("--min-chars", type=int, default=400, help="minimum useful chunk length: auto level, merge rule, S9 (default 400)")
    ap.add_argument("--sample", type=int, default=10, help="chunks in the inspection sample (default 10)")
    ap.add_argument("--seed", type=int, default=0, help="random seed of the sample (default 0)")
    ap.add_argument("--evalset", help="M1 / seed JSONL with evidence_groups: reports straddles_v0 and crosses_page per item")
    ap.add_argument("--out", help="write the Markdown report here (default: print it)")
    ap.add_argument("--sheet", help="write the inspection sheet (Markdown) here")
    ap.add_argument("--json", help="write the full result as JSON here ('-' = print it instead of the report)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    try:
        res = run_check(a.pdf, cap=a.cap, split_level=a.split_level, min_chars=a.min_chars, sample=a.sample, seed=a.seed,
                        evalset=a.evalset, doc_ids=[x.strip() for x in a.doc_ids.split(",") if x.strip()] or None)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = render_report(res)
    for path, content in ((a.out, text), (a.sheet, render_sheet(res) if a.sheet else None),
                          (a.json if a.json and a.json != "-" else None, to_json(res) if a.json else None)):
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(content, encoding="utf-8", newline="\n")
    if a.json == "-":
        sys.stdout.write(to_json(res))
    elif a.out:
        for r in res["files"]:
            print(f"{r['name']}: {r['pages']} pages, {r['n_heads']['size+bold']} headings, split level {_lv(r)}, "
                  f"{r['arms'][r['chosen_arm']]['n'] if r['chosen_arm'] else 0} chunks")
            for x in r["checklist"]:
                print(f"  {x['id']:4s} {x['verdict']:6s} {x['check']}")
            print(f"  recommendation: {r['recommendation']['main']}")
        print(f"report: {a.out}" + (f" · sheet: {a.sheet}" if a.sheet else "") + (f" · json: {a.json}" if a.json else ""))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
