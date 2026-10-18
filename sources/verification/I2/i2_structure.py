"""I2 reference mechanism: structure-aware chunking on a frozen PyMuPDF snapshot (stdlib + PyMuPDF only).

Every number in I2_FACTS comes from this file, run by i2_measure.py. The lesson, the verify notebook and the apply-it
tool re-implement the same rules and are tested against it.

Coordinates: doc_text = the page texts (page.get_text()) joined with "\n" (06 §5.3). A chunk is a slice [a, b) of
doc_text; the page-join character belongs to the page before it (06 §2.3, chunk_segment_to_doc).
"""
import math
import re
from collections import Counter, defaultdict

BOLD_FLAG = 16          # span["flags"] bit 4 (PyMuPDF TEXT_FONT_BOLD)
BOLD_CHAR_FLAG = 8      # span["char_flags"] bit for synthetic bold (what pymupdf4llm also checks)
SEPARATORS = ("\n\n", "\n", " ")    # the v0 / 07 H.1 recursive separators
MAX_WORDS = 12          # [P] a heading line has at most 12 words
REPEAT_PAGES = 3        # [P] a line on >= 3 pages is a running header/footer, never a heading
END_PUNCT = ".!?"


def page_texts(doc):
    return [p.get_text() for p in doc]


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


def line_records(doc):
    """One record per text line of get_text('dict'): page, block, line, raw text, max size, all-bold, span count."""
    out = []
    for pno, page in enumerate(doc, 1):
        for bno, block in enumerate(page.get_text("dict")["blocks"]):
            for lno, line in enumerate(block.get("lines", [])):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                out.append({"page": pno, "block": bno, "line": lno,
                            "raw": "".join(s["text"] for s in line["spans"]),
                            "size": round(max(s["size"] for s in spans), 2),
                            "bold": all(is_bold(s) for s in spans),
                            "spans": len(spans)})
    return out


def size_histogram(doc):
    """Characters (stripped span text) per (rounded size, bold): the evidence for the body size."""
    h = Counter()
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for s in line["spans"]:
                    h[(round(s["size"], 2), is_bold(s))] += len(s["text"].strip())
    return h


def body_size(doc):
    """b = the size holding the most characters (character-weighted, not span-weighted)."""
    per_size = Counter()
    for (size, _bold), n in size_histogram(doc).items():
        per_size[size] += n
    return per_size.most_common(1)[0][0]


def detect_headings(doc, rule="size+bold", max_words=MAX_WORDS):
    """Heading lines -> headings with levels.

    rule "size":      levels only for sizes above the body size (largest = level 1), like pymupdf4llm IdentifyHeaders.
    rule "size+bold": the same, plus all-bold lines at the body size get the next level.
    Filters: <= max_words words, no final . ! ?, not repeated on >= REPEAT_PAGES pages.
    Joining: consecutive heading lines of the same level in the same block are one heading (the Chapter 5 wrap).
    """
    lines = line_records(doc)
    b = body_size(doc)
    bigger = sorted({r["size"] for r in lines if r["size"] > b + 0.5 and r["bold"]}, reverse=True)
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
    """Moving cursor + find: give every heading an exact [start, end) in doc_text. Fail closed if one is missing."""
    cur = 0
    for h in heads:
        pos = doc_text.find(h["lines"][0], cur)
        if pos < 0:
            raise ValueError(f"heading not found after offset {cur}: {h['title']!r}")
        end = pos + len(h["lines"][0])
        for ln in h["lines"][1:]:
            nxt = doc_text.find(ln, end)
            if nxt < 0 or doc_text[end:nxt].strip():
                raise ValueError(f"wrapped heading line not adjacent: {h['title']!r}")
            end = nxt + len(ln)
        h["start"], h["end"] = pos, end
        cur = end
    return heads


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
    """Section of h at a given level: [start(h), start(next heading with level <= level(h)))."""
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


def _pack(atoms, limit):
    out, a, b = [], None, None
    for x, y in atoms:
        if a is None:
            a, b = x, y
        elif y - a <= limit:
            b = y
        else:
            out.append((a, b))
            a, b = x, y
    if a is not None:
        out.append((a, b))
    return out


def _best_cut(text, prev, b, ideal, cap, forbidden, room, slack):
    """Where to end the piece that starts at prev. Candidates are line breaks (a space if none fits); the piece must
    fit the cap, the rest must fit `room` characters, and the cut may not fall inside or right after a heading.
    A line break after a sentence end (". \n") within `slack` of the ideal point wins; otherwise the nearest line break."""
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
    """n = ceil(len/cap) pieces of about len/n each; each cut at a sentence-ending line break within half a piece of
    the ideal point, else the nearest line break; no overlap.
    If a piece would still exceed the cap, try n + 1."""
    length = b - a
    if length <= cap:
        return [(a, b)]
    n = math.ceil(length / cap)
    while True:
        cuts = [a]
        for i in range(1, n):
            cuts.append(_best_cut(text, cuts[-1], b, a + length * i / n, cap, forbidden, (n - i) * cap, length / (2 * n)))
        cuts.append(b)
        pieces = list(zip(cuts, cuts[1:]))
        if all(0 < y - x <= cap for x, y in pieces):
            return pieces
        n += 1


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
            if owner is None:                              # unit opens with deeper headings or body text
                before = [h for h in heads if h["start"] < a]
                owner = before[-1] if before else None
            out.append({"a": a, "b": b, "path": list(owner["path"]) if owner else [], "merged": False})
    return out


def merge_small(doc_text, us, cap, min_chars, split_level):
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


def page_segments(starts, n, a, b):
    segs = []
    ends = [s - 1 for s in starts[1:]] + [n]          # page p covers [start_p, start_{p+1}) incl. its join char
    for p, (s, e) in enumerate(zip(starts, ends), 1):
        e_incl = e + 1 if p < len(starts) else e
        lo, hi = max(a, s), min(b, e_incl)
        if lo < hi:
            segs.append((p, lo, hi))
    return segs


def structure_chunks(doc_text, heads, starts, split_level, cap=1000, min_chars=0):
    us = units(doc_text, heads, split_level)
    if min_chars:
        us = merge_small(doc_text, us, cap, min_chars, split_level)
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


def v0_chunks(pages, starts, size=1000, overlap=200):
    """v0: the recursive splitter per page (97 chunks on Corpus D), as document offsets."""
    out = []
    for pi, page in enumerate(pages):
        for a, b in recursive_spans(page, size, overlap):
            if page[a:b].strip():
                out.append({"a": starts[pi] + a, "b": starts[pi] + b, "text": page[a:b], "page": pi + 1})
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


def recursive_doc_chunks(doc_text, size=1000, overlap=200):
    """The cross-page control: the same recursive splitter over the whole doc_text (no page scope)."""
    return [{"a": a, "b": b, "text": doc_text[a:b]} for a, b in recursive_spans(doc_text, size, overlap)
            if doc_text[a:b].strip()]


def check_invariants(doc_text, chunks, heads, split_level, cap):
    """Returns a dict of violations (all lists empty = pass)."""
    bad = {"round_trip": [], "cap": [], "gaps": [], "crossing": [], "segments": []}
    for i, c in enumerate(chunks):
        if doc_text[c["a"]:c["b"]] != c["text"]:
            bad["round_trip"].append(i)
        if c["b"] - c["a"] > cap:
            bad["cap"].append(i)
        segs = c["page_segments"]
        if not segs or segs[0][1] != c["a"] or segs[-1][2] != c["b"] or any(
                s[2] != t[1] for s, t in zip(segs, segs[1:])):
            bad["segments"].append(i)
    for x, y in zip(chunks, chunks[1:]):
        if y["a"] != x["b"] and doc_text[x["b"]:y["a"]].strip():
            bad["gaps"].append((x["b"], y["a"]))
    bounds = sorted(h["start"] for h in heads if h["level"] <= split_level)
    for i, c in enumerate(chunks):
        if c["merged"]:
            continue
        inside = [s for s in bounds if c["a"] < s < c["b"]]
        # a boundary inside a chunk is allowed only when the text before it is headings/whitespace (glue)
        for s in inside:
            pre = doc_text[c["a"]:s]
            if any(h["start"] >= c["a"] and h["end"] <= s for h in heads) and _only_headings(doc_text, heads, c["a"], s):
                continue
            bad["crossing"].append(i)
            break
    return bad


def _only_headings(doc_text, heads, a, b):
    covered = [(h["start"], h["end"]) for h in heads if a <= h["start"] and h["end"] <= b]
    rest, pos = [], a
    for s, e in sorted(covered):
        rest.append(doc_text[pos:s])
        pos = e
    rest.append(doc_text[pos:b])
    return not "".join(rest).strip()


def to_doc(starts, page, s, e):
    """gold_to_doc: page-relative gold span -> document offsets."""
    return starts[page - 1] + s, starts[page - 1] + e


def contained(alt, chunks):
    """Ids of chunks that contain the whole span alt = (a, b)."""
    return [i for i, c in enumerate(chunks) if c["a"] <= alt[0] and alt[1] <= c["b"]]
