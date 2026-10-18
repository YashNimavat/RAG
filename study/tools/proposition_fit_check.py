"""proposition_fit_check: would proposition indexing help on MY documents, what would it cost, and are the propositions faithful?

What this is: a command-line tool (also importable) that numbers the units of your documents (headings and sentences,
with offsets), reads a propositions file that you wrote by hand or exported from a recorded run, checks every
proposition against its source units in code, forecasts what an LLM run over the whole collection would cost, and
writes a Markdown report:
  1 Settings and documents   what was read, the settings, where each number comes from
  2 Units                    sentences and headings per page (ids page:i); the splitter's known limits on your text
  3 Forecast                 calls, tokens (ASSUMED per-call sizes), $, days of the daily token quota, minutes at the
                             per-minute limit, index size, cost per 1k chunks; the rendered prompt on the sample pages
  4 Proposition checks       ids, span(p), align(p), unsupported words, pronoun starts, parents (v0 chunks), duplicates
  5 Coverage                 sentence_coverage per page and the uncovered sentences; gold_reachability (with gold)
  6 Per question             relevant chunks and propositions; with --dense: arm (a) vs the plain chunks (MRR@10, CE@k),
                             arm (b), the text check, distinct parents and distinct-facts@k
  7 Checklist                C1-C12 (lesson I4 / research I4 section 8) with a verdict (✓ fine, ✗ problem found,
                             ? check by hand), the evidence and how to check
  8 Recommendation           the first rule that matches (see recommend())
Also a labelling sheet (--labels-csv): one row per proposition with its source text, for the hand check (C5).
What this is not: an evaluation of proposition indexing. No LLM is called. The checks show whether a set of
propositions can be trusted and scored; a handful of questions shows the mechanism, not which index is better.

Definitions (the same code as sources/verification/I4/i4_kit_measure.py, so the numbers match I4_FACTS):
  unit            a heading line or a sentence of one page (split_page); id "page:i" for a PDF, "1:i" for a .txt/.md file
                  (one file = one page), "<file stem>#page:i" when several documents are given
  words(t)        content-word stems: lowercase [a-z0-9] runs (decimals kept), stop words removed, a crude suffix stem
  span(p)         [min a_i, max b_i) over the units i in source_ids, in document offsets (pages joined with "\\n")
  resolved        names the proposition brought in for a pronoun; each must occur earlier on the same page
  align(p)        |W(p) ∩ (W(sources) ∪ W(resolved names))| / |W(p)|, W = words(); the resolved names count only when
                  every one of them occurs earlier on the page. C4 lists every align < 1
  parents         the v0 chunks (07 recursive splitter, per page, 1,000 / 200) that contain span(p); if none contains it,
                  the chunks it overlaps. Primary parent = the first (lowest number)
  arm (a)         rank propositions, map each to its primary parent, keep the first occurrence of each parent;
                  MRR@10 on the parents; CE@k on the distinct parents of the top k propositions
  arm (b)         rel(p) = 1 iff span(p) overlaps a gold segment (any_overlap, non-whitespace); CE@k on ∪ span(p) of the top k
  text check      arm (b) counts p only if its text states an "expect" string (whole words, case-insensitive)
  distinct-facts@k  distinct normalised texts in the top k
  sentence_coverage = sentences with >= 1 indexed proposition / sentences (per page that has propositions)
  gold_reachability = gold alternatives overlapped by some span(p) / alternatives
  keep-good       kept ∧ good / good; catch-bad = dropped ∧ bad / bad (good = "supported", bad = "added" or "distorted")
  calls           pages (generate) + pages (batched grade) or + propositions (per-proposition grade)
  index size      n_props × dim × 4 bytes (float32)
CE@k is complete evidence: every evidence group has an alternative whose non-whitespace characters are all covered.

Inputs:
  --docs FILES      .pdf (PyMuPDF page.get_text()), .txt or .md; one document per file; folders are searched
  --props FILE      JSONL, one proposition per line: {"prop_id", "page" (optional), "text", "source_ids": ["10:7"],
                    "resolved": ["UNFCCC"] (optional), "kept": true|false (optional, the grader's decision)}
  --questions FILE  JSONL: {"id", "q", "expect": "text" or [..], "type", "gold": [06 evidence_groups]} (all optional
                    except q). The 06 §6.7 form ("qid", "question", "category", "evidence_groups") is read as well.
                    Gold segments are page-relative: {"doc_id", "page", "char_start", "char_end"}; with one document
                    the doc_id is not checked, with several it must be the file stem.
  --labels FILE     the labelling sheet with the "label" column filled in (supported / added / distorted)
No API calls. --provider groq|anthropic is reserved for when the course's study/llmops/ cache exists (record once,
replay offline); until then it refuses to run. Book text must never be sent to any API. Standard library + numpy +
pymupdf; sentence-transformers only with --dense (MiniLM from the local Hugging Face cache, HF_HUB_OFFLINE=1). When
it is missing, --dense is skipped with a message and section 6 shows only what needs no embedding.

Usage, from rag_learning/:
    uv run python study/tools/proposition_fit_check.py --docs my.pdf --props props.jsonl --questions q.jsonl \\
        --report prop_report.md --labels-csv prop_labels.csv
    uv run python study/tools/proposition_fit_check.py --docs my.pdf --render-prompt 10 > page10_prompt.txt
    uv run python study/tools/proposition_fit_check.py --docs my.pdf --props props.jsonl --labels prop_labels.csv --dense
Lesson: study/lessons/I4_propositions.html (steps 1-12; checklist in #apply).

Import:
    from proposition_fit_check import run_check, render_report
    res = run_check(["doc.pdf"], props="props.jsonl", questions="q.jsonl")
    print(render_report(res))
"""
from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")             # never download the dense model
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import argparse
import collections
import csv
import importlib.metadata as md
import io
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

OK, BAD, ASK = "✓", "✗", "?"
EXTS = (".pdf", ".txt", ".md")
SEPARATORS = ("\n\n", "\n", " ")
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
MAX_ROWS = 60                     # longest table in the report; the rest is counted
MIN_LABELLED = 10                 # fewer labelled questions = "mechanism only" for the ranking arms
MIN_FAITH = 30                    # C5: at least this many hand-labelled propositions
FAITH_BAR = 0.85                  # C5: Wilson lower bound to clear
COVER_BAR = 0.9                   # C6
FAIL_RATE = 0.02                  # C2
MANY_FLAGS = 0.10                 # recommendation: "many C4 flags" = this share of propositions or more (a tool setting)
GRADINGS = ("off", "batched", "per-prop")
LABELS = ("supported", "added", "distorted")

# Prices and limits (CITED: LLMOPS_FOUNDATION §6.2 and study/tools/examples/prices_2026-10-17.json; the free-tier plan
# row is UNVERIFIED). Per-call token sizes are ASSUMED (research phase_04 I4 §9), not measured: (input, output incl. reasoning).
PRICE_IN, PRICE_OUT = 0.075, 0.30                         # USD per 1M tokens, Groq openai/gpt-oss-20b
TPD, TPM = 200_000, 8_000
ASSUME = {"gen": (1050, 1600), "batched": (1800, 1600), "per-prop": (870, 300)}
DENSE_X_RATIO = 257 / 114                                 # propositions per sentence, factoid-wiki README (CITED)
TOK_PER_CHAR = 12840 / 72593                              # DERIVED: P1's o200k_harmony tokens / chars on the climate PDF
DIMS = ((384, "MiniLM"), (1536, "Cohere embed-v4.0 default"))

# The frozen prompt prop_gen_v1 (byte copy of sources/verification/I4/prop_gen_v1.txt, sha256 bdff5976...).
PROMPT_V1 = """prompt_version: prop_gen_v1
You rewrite one page of a document as propositions for a search index.

The page is given as numbered units. Each unit is a heading or a sentence, with an id such as [10:7].

Write a list of propositions. Each proposition must:
1. State one fact: one subject and one thing said about it.
2. Be understandable alone: replace pronouns and vague references ("it", "these policies") with the full name used earlier on the page.
3. Keep the page's own wording where you can, including numbers, dates and qualifiers such as "well below" or "about".
4. Add nothing that the units do not say. Do not use outside knowledge.
5. List in "source_ids" the id of every unit it comes from. A heading id may be listed only together with a sentence id.

Cover every sentence. A sentence that states no fact (for example a list of headings) may be skipped.

Return JSON only, in this shape:
{"propositions": [{"text": "...", "source_ids": ["10:7"]}]}

Example input:
[0:0] (heading) Town library
[0:1] The town library opened in 1998.
[0:2] It lends books and audio recordings.
[0:3] It also runs a weekly reading club for children.

Example output:
{"propositions": [
 {"text": "The town library opened in 1998.", "source_ids": ["0:1"]},
 {"text": "The town library lends books.", "source_ids": ["0:2"]},
 {"text": "The town library lends audio recordings.", "source_ids": ["0:2"]},
 {"text": "The town library runs a weekly reading club for children.", "source_ids": ["0:3"]}
]}

Page:
{units}
"""

# Question types that need a relation between facts (C11); other types are single-fact unless the wording says otherwise.
RELATION_TYPES = {"multi-span", "multi-hop", "compare", "comparison", "contrast", "synthesis", "summary", "summarise",
                  "summarize", "aggregation"}
SINGLE_TYPES = {"factual-single-span", "factual", "exact-term", "lookup", "single-fact", "numeric", "definition"}
RELATION_RE = re.compile(r"\b(compare|compared|comparison|contrast|contrasts|differ|differs|difference|differences|versus|"
                         r"vs|summari[sz]e|summary|overview|relationship|both)\b", re.I)


# ---------------------------------------------------------------------------------------------------------------- the I4 definitions
# Copied exactly from sources/verification/I4/i4_kit_measure.py (K3, K4, K10).
SENT_END = re.compile(r'[.!?]["”)\]]?(?=\s|$)')
LINE_END = re.compile(r'[.!?:]["”)\]]?\s*$')


def split_page(t):
    """Units of one page as (kind, a, b), page-relative offsets, whitespace trimmed. kind 'h' = heading line,
    's' = sentence. A heading is a short line (< 80 chars) that starts with a capital letter, has no end
    punctuation, and is not inside an unfinished sentence. A sentence ends at . ! ? followed by whitespace."""
    units, buf, pos = [], None, 0
    for ln in t.split("\n"):
        a, s = pos, ln.strip()
        pos += len(ln) + 1
        if not s:
            continue
        a2 = a + len(ln) - len(ln.lstrip())
        b2 = a + len(ln.rstrip())
        if buf is None and not LINE_END.search(s) and s[0].isupper() and len(s) < 80:
            units.append(("h", a2, b2))
            continue
        if buf is None:
            buf = a2
        for mt in SENT_END.finditer(ln):
            e = a + mt.end()
            if e <= buf:
                continue
            units.append(("s", buf, e))
            buf = None
            rest = ln[mt.end():]
            if rest.strip():
                buf = a + mt.end() + len(rest) - len(rest.lstrip())
    if buf is not None:
        units.append(("s", buf, len(t.rstrip())))
    return units


STOP = set("""a an the is are was were be been being of in on at to for and or but with by as from that this these those
it its their them they such which who whom whose than then there here into over under about also can may might will would
should could has have had do does did not no nor so very via per each every all both other another some any many much more
most less least only just up down out off our your his her he she we you i if while when where what how why""".split())


def stem(w):
    for suf in ("ing", "ed", "es", "s", "e"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def words(t):
    t = re.sub(r"-\s*\n\s*", "-", t.lower())
    return {stem(w) for w in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", t) if (len(w) > 1 or w.isdigit()) and w not in STOP}


PRONOUN_START = re.compile(r"^(it|its|they|their|them|this|these|those|that|he|she|his|her|such)\b", re.I)


def norm_text(t):
    """The normalised text used for duplicates and distinct-facts@k."""
    return " ".join(re.findall(r"[a-z0-9.]+", t.lower()))


def toks(t):
    return re.findall(r"[a-z0-9]+", t.lower())


def ngrams(t, n=8):
    w = toks(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def align_text(prop_text, source_text, resolved_names=()):
    """align and unsupported words of a proposition against a source text (e.g. upstream's astronaut example)."""
    W = words(prop_text)
    allowed = words(source_text).union(*(words(nm) for nm in resolved_names)) if resolved_names else words(source_text)
    return (len(W & allowed) / len(W) if W else None), sorted(W - allowed)


def wilson(x, n, z=1.959963984540054):
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


# ---------------------------------------------------------------------------------------------------------------- input
def load_documents(paths):
    """Files or folders (.pdf, .txt, .md; folders are searched recursively, in sorted order). One document per file."""
    files, seen = [], set()
    for p in map(Path, paths):
        if p.is_dir():
            found = sorted(q for q in p.rglob("*") if q.is_file() and q.suffix.lower() in EXTS)
        elif p.is_file():
            if p.suffix.lower() not in EXTS:
                raise ValueError(f"unsupported file type: {p} (use .pdf, .txt or .md)")
            found = [p]
        else:
            raise FileNotFoundError(f"no such file or folder: {p}")
        for f in found:
            if f.resolve() not in seen:
                seen.add(f.resolve())
                files.append(f)
    docs = []
    for f in files:
        if f.suffix.lower() == ".pdf":
            import pymupdf                          # pinned 1.26.7 in this project
            with pymupdf.open(f) as d:
                pages = [pg.get_text() for pg in d]
        else:
            pages = [f.read_text(encoding="utf-8", errors="replace")]
        docs.append({"name": f.name, "stem": f.stem, "pages": pages, "is_pdf": f.suffix.lower() == ".pdf"})
    if not docs:
        raise ValueError("no .pdf, .txt or .md documents found")
    return prepare_docs(docs)


def prepare_docs(docs):
    stems = [d["stem"] for d in docs]
    if len(set(stems)) != len(stems):
        raise ValueError(f"two documents share a file stem ({sorted(s for s in stems if stems.count(s) > 1)}): unit ids would clash")
    for d in docs:
        d["text"] = "\n".join(d["pages"])
        d["starts"], pos = [], 0
        for pg in d["pages"]:
            d["starts"].append(pos)
            pos += len(pg) + 1
    return docs


def uid(docs, di, page, i):
    return f"{page}:{i}" if len(docs) == 1 else f"{docs[di]['stem']}#{page}:{i}"


def page_key(docs, di, page):
    return f"{page}" if len(docs) == 1 else f"{docs[di]['stem']}#{page}"


def make_units(docs):
    """All units of all documents, in order: id -> {id, doc, page, i, kind, a, b (page offsets), da, db, text}."""
    units = {}
    for di, d in enumerate(docs):
        for pn, t in enumerate(d["pages"], 1):
            for i, (k, a, b) in enumerate(split_page(t)):
                u = uid(docs, di, pn, i)
                units[u] = {"id": u, "doc": di, "page": pn, "i": i, "kind": k, "a": a, "b": b,
                            "da": d["starts"][pn - 1] + a, "db": d["starts"][pn - 1] + b, "text": t[a:b]}
    return units


def _jsonl_lines(path):
    return Path(path).read_text(encoding="utf-8").splitlines()


def load_props(source):
    """Returns (records, problems, n_records). Bad records are logged and left out, never silently emptied."""
    if source is None:
        return [], [], 0
    if isinstance(source, (str, Path)):
        if not Path(source).is_file():
            raise FileNotFoundError(f"propositions file not found: {source}")
        raw = []
        for n, line in enumerate(_jsonl_lines(source), 1):
            if not line.strip():
                continue
            try:
                raw.append((n, json.loads(line)))
            except json.JSONDecodeError as e:
                raw.append((n, e))
    else:
        raw = list(enumerate(source, 1))
    out, problems, seen = [], [], set()
    for n, it in raw:
        where = f"record {n}"
        if isinstance(it, Exception):
            problems.append(f"{where}: not valid JSON ({it.msg})")
            continue
        if not isinstance(it, dict):
            problems.append(f"{where}: not a JSON object")
            continue
        pid = str(it.get("prop_id") or f"P{n}")
        text, ids, res = it.get("text"), it.get("source_ids"), it.get("resolved", [])
        if not isinstance(text, str) or not text.strip():
            problems.append(f"{where} ({pid}): missing or empty \"text\"")
            continue
        if not isinstance(ids, list) or not ids or not all(isinstance(x, str) for x in ids):
            problems.append(f"{where} ({pid}): \"source_ids\" must be a non-empty list of strings")
            continue
        if res is None:
            res = []
        if not isinstance(res, list) or not all(isinstance(x, str) for x in res):
            problems.append(f"{where} ({pid}): \"resolved\" must be a list of strings")
            continue
        if pid in seen:
            problems.append(f"{where} ({pid}): duplicate prop_id (left out)")
            continue
        seen.add(pid)
        kept = it.get("kept")
        out.append({"prop_id": pid, "page": it.get("page"), "text": text, "source_ids": list(ids), "resolved": list(res),
                    "kept": kept if isinstance(kept, bool) else None})
    return out, problems, len(raw)


def load_questions(source):
    """A path (.jsonl) or a list of dicts. Accepts the tool's form and the 06 §6.7 form."""
    if source is None:
        return []
    if isinstance(source, (str, Path)):
        if not Path(source).is_file():
            raise FileNotFoundError(f"questions file not found: {source}")
        items = []
        for n, line in enumerate(_jsonl_lines(source), 1):
            if line.strip():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"{source}, line {n}: not valid JSON ({e.msg})") from None
    else:
        items = list(source)
    out = []
    for n, it in enumerate(items, 1):
        it = {"q": it} if isinstance(it, str) else dict(it)
        q = it.get("q") or it.get("question")
        if not str(q or "").strip():
            raise ValueError(f"question {n}: missing \"q\"")
        exp = it.get("expect") or None
        if isinstance(exp, str):
            exp = [exp]
        out.append({"id": str(it.get("id") or it.get("qid") or f"Q{n}"), "q": str(q), "expect": exp,
                    "type": it.get("type") or it.get("category") or None,
                    "answerable": it.get("answerable", True) is not False and (it.get("type") or "") != "no-answer",
                    "created_by": it.get("created_by"),
                    "gold": it.get("gold") if it.get("gold") is not None else it.get("evidence_groups")})
    return out


def load_labels(source):
    """The labelling sheet (CSV) with "label" filled in, or a dict {prop_id: label}. Returns (labels, problems)."""
    if source is None:
        return None, []
    if isinstance(source, dict):
        rows = [{"prop_id": k, "label": v} for k, v in source.items()]
    else:
        if not Path(source).is_file():
            raise FileNotFoundError(f"labels file not found: {source}")
        rows = list(csv.DictReader(io.StringIO(Path(source).read_text(encoding="utf-8-sig"))))
    labels, problems = {}, []
    for n, r in enumerate(rows, 2):
        lab = (r.get("label") or "").strip().lower()
        if not lab:
            continue
        if lab not in LABELS:
            problems.append(f"row {n} ({r.get('prop_id')}): label {lab!r} is not one of {', '.join(LABELS)}")
            continue
        labels[str(r.get("prop_id"))] = lab
    return labels, problems


# ---------------------------------------------------------------------------------------------------------------- v0 chunks (the parents)
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


def make_chunks(docs, size=1000, overlap=200):
    """v0: the 07 recursive splitter per page (v0's 97 chunks for the climate PDF). Offsets are document offsets."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need chunk-size > 0 and 0 <= overlap < chunk-size")
    chunks = []
    for di, d in enumerate(docs):
        n = 0
        for pn, page in enumerate(d["pages"], 1):
            for a, b in recursive_spans(page, size, overlap):
                s = d["starts"][pn - 1]
                chunks.append({"id": f"#{n}" if len(docs) == 1 else f"{d['stem']}#{n}", "doc": di, "page": pn,
                               "start": s + a, "end": s + b, "text": page[a:b]})
                n += 1
    if not chunks:
        raise ValueError("the documents contain no text")
    return chunks


# ---------------------------------------------------------------------------------------------------------------- gold, relevance, CE
def _merge(ranges):
    out = []
    for a, b in sorted(ranges):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _covered_fraction(segments, spans, docs):
    total = hit = 0
    for doc, a, b in segments:
        union = _merge([(x, y) for d, x, y in spans if d == doc])
        t = docs[doc]["text"]
        for i in range(a, b):
            if t[i].isspace():
                continue
            total += 1
            if any(x <= i < y for x, y in union):
                hit += 1
    return 1.0 if total == 0 else hit / total


def ce(G, spans, docs):
    """Complete evidence: every group has an alternative whose non-whitespace characters are all covered by spans."""
    return int(all(max(_covered_fraction(alt, spans, docs) for alt in g) == 1.0 for g in G))


def rel(span, G, docs):
    """any_overlap: the span overlaps >= 1 non-whitespace character of any segment of any alternative."""
    d, x, y = span
    t = docs[d]["text"]
    for g in G:
        for alt in g:
            for doc, a, b in alt:
                if doc == d and any(not t[i].isspace() for i in range(max(a, x), min(b, y))):
                    return 1
    return 0


def gold_to_doc(q, docs):
    """06 evidence_groups (page-relative) -> [[[(doc, a, b), ...] per alternative] per group], plus problems."""
    groups = q.get("gold") or []
    G, problems = [], []
    stems = {d["stem"]: n for n, d in enumerate(docs)}
    for g in groups:
        alts = []
        for alt in g.get("alternatives") or []:
            segs, ok = [], True
            for s in alt.get("segments") or []:
                di = 0 if len(docs) == 1 else stems.get(s.get("doc_id"))
                if di is None:
                    problems.append(f"{q['id']} {g.get('group_id')}/{alt.get('alt_id')}: doc_id {s.get('doc_id')!r} is not a loaded file stem")
                    ok = False
                    continue
                d, p = docs[di], int(s.get("page", 1))
                if not 1 <= p <= len(d["pages"]) or not 0 <= s["char_start"] < s["char_end"] <= len(d["pages"][p - 1]):
                    problems.append(f"{q['id']} {g.get('group_id')}/{alt.get('alt_id')}: page {p} [{s['char_start']}, {s['char_end']}) is outside the page text")
                    ok = False
                    continue
                segs.append((di, d["starts"][p - 1] + s["char_start"], d["starts"][p - 1] + s["char_end"]))
            quote = alt.get("quote")
            if ok and segs and quote:
                txt = "".join(docs[di]["text"][a:b] for di, a, b in segs)
                if not " ".join(txt.split()).startswith(" ".join(quote.split())):
                    problems.append(f"{q['id']} {g.get('group_id')}/{alt.get('alt_id')}: the quote does not match the text at its offsets")
            if ok and segs:
                alts.append(segs)
        if alts:
            G.append(alts)
        elif g.get("alternatives"):
            problems.append(f"{q['id']} {g.get('group_id')}: no usable alternative")
    return G, problems


def states(text, expects):
    """True if the text states one of the expect strings (whole words, case-insensitive, whitespace normalised)."""
    t = " ".join(text.lower().split())
    return any(re.search(r"(?<![a-z0-9])" + re.escape(" ".join(x.lower().split())) + r"(?![a-z0-9])", t) for x in expects or [])


# ---------------------------------------------------------------------------------------------------------------- proposition checks
def check_prop(p, units, docs, chunks):
    """C3 ids and span, alignment with verified resolved names, parents, pronoun start (i4_kit_measure.check_prop)."""
    ids_ok = all(i in units for i in p["source_ids"]) and len(p["source_ids"]) > 0
    r = {"prop_id": p["prop_id"], "ids_ok": ids_ok, "bad_ids": [i for i in p["source_ids"] if i not in units]}
    if not ids_ok:
        r.update(span=None, align=None, unsupported=None, parents=[], contained=False, pronoun=bool(PRONOUN_START.match(p["text"])),
                 resolved_ok=None, one_page=None, inside=None, page_ok=None, heading_only=None, doc=None, page=None)
        return r
    us = [units[i] for i in p["source_ids"]]
    di = us[0]["doc"]
    D = docs[di]["text"]
    a, b = min(u["da"] for u in us), max(u["db"] for u in us)
    first = min(u["da"] for u in us)
    pg = us[0]["page"]
    before = D[docs[di]["starts"][pg - 1]:first]
    resolved_ok = all(words(nm) <= words(before) for nm in p["resolved"])
    allowed = set().union(*(words(u["text"]) for u in us))
    if resolved_ok:
        allowed |= set().union(set(), *(words(nm) for nm in p["resolved"]))
    W = words(p["text"])
    mine = [(n, c) for n, c in enumerate(chunks) if c["doc"] == di]
    contain = [n for n, c in mine if c["start"] <= a and b <= c["end"]]
    overlap = [n for n, c in mine if c["start"] < b and a < c["end"]]
    one_page = len({(u["doc"], u["page"]) for u in us}) == 1
    page_ok = p.get("page") is None or str(p["page"]) == str(pg)
    r.update(span=(di, a, b), inside=0 <= a < b <= len(D), align=(len(W & allowed) / len(W)) if W else None,
             unsupported=sorted(W - allowed), parents=contain or overlap, contained=bool(contain),
             pronoun=bool(PRONOUN_START.match(p["text"])), resolved_ok=resolved_ok, one_page=one_page, page_ok=page_ok,
             heading_only=all(u["kind"] == "h" for u in us), doc=di, page=pg, no_words=not W)
    return r


def coverage(units, props_checked, scope_ids):
    """sentence_coverage over the sentence units in scope_ids: (covered ids, uncovered ids)."""
    covered = {u for p, r in props_checked if r["ids_ok"] for u in p["source_ids"]}
    sent = [u for u in scope_ids if units[u]["kind"] == "s"]
    return [u for u in sent if u in covered], [u for u in sent if u not in covered]


# ---------------------------------------------------------------------------------------------------------------- prompt, leakage
def render_units(units, keys):
    lines = []
    for u in keys:
        u = units[u]
        lines.append(f"[{u['id']}] " + ("(heading) " if u["kind"] == "h" else "") + re.sub(r"\s+", " ", u["text"]))
    return "\n".join(lines)


def render_prompt(units, docs, di, page, template=PROMPT_V1):
    keys = [k for k, u in units.items() if u["doc"] == di and u["page"] == page]
    return template.replace("{units}", render_units(units, keys))


def prompt_example_part(template):
    return template.split("Page:\n")[0] if "Page:\n" in template else template.replace("{units}", "")


def eval_texts(questions):
    """The texts the prompt must not contain: questions, gold quotes, expect strings."""
    out = []
    for q in questions:
        out.append(q["q"])
    for q in questions:
        for g in q.get("gold") or []:
            for alt in g.get("alternatives") or []:
                if alt.get("quote"):
                    out.append(alt["quote"])
    for q in questions:
        out.extend(q.get("expect") or [])
    return out


def leakage(prompt_part, texts, n=8):
    EV = set().union(*(ngrams(t, n) for t in texts)) if texts else set()
    shared = ngrams(prompt_part, n) & EV
    return {"eval_ngrams": len(EV), "shared": sorted(" ".join(g) for g in shared)}


# ---------------------------------------------------------------------------------------------------------------- forecast
def forecast(n_pages, n_props, grading, tpd=TPD, tpm=TPM):
    """Calls, tokens and $ for one index build with the ASSUMED per-call sizes."""
    grading = grading.replace("_", "-")
    if grading not in GRADINGS:
        raise ValueError(f"grading must be one of {GRADINGS}")
    calls = {"gen": n_pages, "batched": n_pages if grading == "batched" else 0, "per-prop": n_props if grading == "per-prop" else 0}
    tin = sum(calls[k] * ASSUME[k][0] for k in calls)
    tout = sum(calls[k] * ASSUME[k][1] for k in calls)
    usd = (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
    return {"grading": grading, "calls": sum(calls.values()), "tokens_in": tin, "tokens_out": tout, "tokens": tin + tout,
            "usd": usd, "days": (tin + tout) / tpd, "minutes": (tin + tout) / tpm}


# ---------------------------------------------------------------------------------------------------------------- dense (optional)
def load_minilm():
    """Returns (embed function, None) or (None, reason). Local cache only."""
    try:
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None, "sentence-transformers is not installed"
    try:
        model = SentenceTransformer(MINILM, device="cpu")
    except Exception:  # noqa: BLE001
        return None, f"{MINILM} is not in the local Hugging Face cache"
    return (lambda texts: model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True,
                                       show_progress_bar=False).astype(np.float32)), None


def _unit(M):
    M = np.asarray(M, dtype=np.float64)
    n = np.linalg.norm(M, axis=-1, keepdims=True)
    return M / np.where(n == 0, 1, n)


def ranked(scores):
    """positions best first; ties broken by the lower position (the course rule)."""
    return sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))


def score_order(res, q, order, k=None):
    """The three scorings for one question and one ranked list of indexed propositions (positions in res['index'])."""
    k = k or res["settings"]["k"]
    docs, chunks, P, R = res["_docs"], res["_chunks"], res["index"], res["_checked"]
    G, rel_chunks = q["_G"], set(q["rel_chunks"])
    rows = []
    for rank, j in enumerate(order, 1):
        p, r = P[j]
        if G:
            rb = rel(r["span"], G, docs)
        elif q["expect"]:
            rb = int(states(" ".join(res["_units"][u]["text"] for u in p["source_ids"]), q["expect"]))
        else:
            rb = 0
        rows.append((rank, j, r["parents"][0], rb, states(p["text"], q["expect"]) if q["expect"] else None))
    parents = list(dict.fromkeys(par for _, _, par, _, _ in rows))
    top_parents = list(dict.fromkeys(par for _, _, par, _, _ in rows[:k]))
    rr_a = next((1 / i for i, par in enumerate(parents, 1) if par in rel_chunks and i <= 10), 0.0)
    rr_b = next((1 / rk for rk, _, _, rb, _ in rows if rb and rk <= 10), 0.0)
    rr_t = next((1 / rk for rk, _, _, rb, st in rows if rb and st and rk <= 10), 0.0) if q["expect"] else None
    ce_a = ce(G, [(chunks[c]["doc"], chunks[c]["start"], chunks[c]["end"]) for c in top_parents], docs) if G else None
    ce_b = ce(G, [P[j][1]["span"] for _, j, _, _, _ in rows[:k]], docs) if G else None
    return {"parents": parents, "top_parents": top_parents, "rr_a": rr_a, "ce_a": ce_a, "rr_b": rr_b, "ce_b": ce_b, "rr_text": rr_t,
            "distinct_facts": len({norm_text(P[j][0]["text"]) for _, j, _, _, _ in rows[:k]}),
            "top": [(P[j][0]["prop_id"], par, rb) for _, j, par, rb, _ in rows[:k]]}


# ---------------------------------------------------------------------------------------------------------------- the check
def _version(p):
    try:
        return md.version(p)
    except md.PackageNotFoundError:
        return None


def _parse_pages(spec, docs):
    out = []
    for x in [s.strip() for s in str(spec).split(",") if s.strip()]:
        if "#" in x:
            stem_, pg = x.rsplit("#", 1)
            di = next((n for n, d in enumerate(docs) if d["stem"] == stem_), None)
        else:
            di, pg = (0 if len(docs) == 1 else None), x
        if di is None:
            raise ValueError(f"page {x!r}: with several documents write <file stem>#<page>")
        if not pg.isdigit() or not 1 <= int(pg) <= len(docs[di]["pages"]):
            raise ValueError(f"page {x!r} does not exist")
        out.append((di, int(pg)))
    return out


def run_check(docs, props=None, questions=None, pages=None, sample=3, grading="batched", budget_usd=None, tpd=TPD,
              dense=False, embedder=None, k=4, labels=None, prompt=None, props_origin="unknown", chunk_size=1000, overlap=200):
    docs = load_documents(docs) if not (docs and isinstance(docs[0], dict)) else prepare_docs(docs)
    grading = grading.replace("_", "-")
    if grading not in GRADINGS:
        raise ValueError(f"grading must be one of {GRADINGS}")
    template = PROMPT_V1 if prompt is None else (Path(prompt).read_text(encoding="utf-8") if isinstance(prompt, Path) or
                                                  (isinstance(prompt, str) and "{units}" not in prompt) else prompt)
    if "{units}" not in template:
        raise ValueError("the prompt template has no {units} placeholder")
    units = make_units(docs)
    chunks = make_chunks(docs, chunk_size, overlap)
    plist, prop_problems, n_records = load_props(props)
    qs = load_questions(questions)
    lab, lab_problems = load_labels(labels)

    # 2 units
    page_rows = []
    for di, d in enumerate(docs):
        for pn in range(1, len(d["pages"]) + 1):
            us = [u for u in units.values() if u["doc"] == di and u["page"] == pn]
            page_rows.append({"doc": di, "page": pn, "key": page_key(docs, di, pn), "chars": len(d["pages"][pn - 1]),
                              "s": sum(u["kind"] == "s" for u in us), "h": sum(u["kind"] == "h" for u in us),
                              "first": us[0]["id"] if us else None, "last": us[-1]["id"] if us else None})
    ns = sorted(r["s"] for r in page_rows)
    n_sent = sum(ns)
    first_ids = {r["first"] for r in page_rows if r["first"]}
    last_sent = {}
    for u in units.values():
        if u["kind"] == "s":
            last_sent[(u["doc"], u["page"])] = u["id"]
    limits = {"fragments": [u for u in first_ids if units[u]["kind"] == "s" and units[u]["text"][:1].islower()],
              "cut_at_end": [u for u in last_sent.values() if not re.search(r'[.!?]["”)\]]?$', units[u]["text"])],
              "eg": sum(d["text"].count("e.g.") + d["text"].count("i.e.") for d in docs)}
    limits["fragments"].sort(key=lambda u: (units[u]["doc"], units[u]["page"]))
    limits["cut_at_end"].sort(key=lambda u: (units[u]["doc"], units[u]["page"]))
    unit_stats = {"sentences": n_sent, "headings": sum(r["h"] for r in page_rows), "units": len(units),
                  "min": ns[0] if ns else 0, "median": ns[len(ns) // 2] if ns else 0, "max": ns[-1] if ns else 0,
                  "words4": sum(len(re.findall(r"\S+", u["text"])) >= 4 for u in units.values() if u["kind"] == "s"),
                  "spans_ok": all(docs[u["doc"]]["text"][u["da"]:u["db"]] == u["text"] for u in units.values())}

    # 4 proposition checks
    checked = [(p, check_prop(p, units, docs, chunks)) for p in plist]
    norm = collections.defaultdict(list)
    for p, r in checked:
        norm[norm_text(p["text"])].append(p["prop_id"])
    dup_groups = [ids for ids in norm.values() if len(ids) > 1]
    dup_of = {pid: [x for x in ids if x != pid] for ids in dup_groups for pid in ids}
    valid = [(p, r) for p, r in checked if r["ids_ok"]]
    index = [(p, r) for p, r in valid if p["kept"] is not False]
    src_sent = {u for p, r in valid for u in p["source_ids"] if units[u]["kind"] == "s"}
    flagged = [(p, r) for p, r in valid if r["align"] is None or r["align"] < 1]
    summary = {"records": n_records, "loaded": len(plist), "valid": len(valid), "indexed": len(index),
               "bad_ids": [p["prop_id"] for p, r in checked if not r["ids_ok"]],
               "outside": [p["prop_id"] for p, r in valid if not r["inside"]],
               "multi_page": [p["prop_id"] for p, r in valid if not r["one_page"]],
               "page_mismatch": [p["prop_id"] for p, r in valid if not r["page_ok"]],
               "heading_only": [p["prop_id"] for p, r in valid if r["heading_only"]],
               "flagged": [p["prop_id"] for p, r in flagged], "pronoun": [p["prop_id"] for p, r in checked if r["pronoun"]],
               "resolved_uses": sum(bool(p["resolved"]) for p, r in valid),
               "resolved_bad": [p["prop_id"] for p, r in valid if r["resolved_ok"] is False],
               "align_min": min((r["align"] for p, r in valid if r["align"] is not None), default=None),
               "contained": sum(r["contained"] for p, r in valid),
               "n_parents": collections.Counter(len(r["parents"]) for p, r in valid),
               "per_sentence": (len(valid) / len(src_sent)) if src_sent else None, "source_sentences": len(src_sent),
               "dup_groups": dup_groups, "distinct": len(norm),
               "by_page": collections.Counter(page_key(docs, r["doc"], r["page"]) for p, r in valid)}

    # 5 coverage
    written = sorted({(r["doc"], r["page"]) for p, r in index})
    cov_rows = []
    for di, pn in written:
        ids = [u for u, x in units.items() if x["doc"] == di and x["page"] == pn]
        hit, miss = coverage(units, index, ids)
        cov_rows.append({"key": page_key(docs, di, pn), "covered": len(hit), "sentences": len(hit) + len(miss), "missing": miss})
    cov_tot = (sum(r["covered"] for r in cov_rows), sum(r["sentences"] for r in cov_rows))

    # 6 questions: gold, relevant chunks, reachability, relation type
    gold_problems = []
    reach_alts = reach_hit = 0
    spans = [r["span"] for p, r in index]
    for q in qs:
        q["_G"], pr = gold_to_doc(q, docs)
        gold_problems += pr
        if q["_G"]:
            q["rel_chunks"] = [i for i, c in enumerate(chunks) if rel((c["doc"], c["start"], c["end"]), q["_G"], docs)]
            q["reach"] = [[any(rel(sp, [[alt]], docs) for sp in spans) for alt in g] for g in q["_G"]]
            reach_alts += sum(len(g) for g in q["reach"])
            reach_hit += sum(sum(g) for g in q["reach"])
            q["rel_props"] = [p["prop_id"] for p, r in index if rel(r["span"], q["_G"], docs)]
        elif q["expect"]:
            q["rel_chunks"] = [i for i, c in enumerate(chunks) if states(c["text"], q["expect"])]
            q["reach"] = None
            q["rel_props"] = [p["prop_id"] for p, r in index if states(" ".join(units[u]["text"] for u in p["source_ids"]), q["expect"])]
        else:
            q["rel_chunks"], q["reach"], q["rel_props"] = [], None, []
        q["text_props"] = [p["prop_id"] for p, r in index if q["expect"] and states(p["text"], q["expect"])]
        t = (q["type"] or "").lower()
        q["relation"] = True if t in RELATION_TYPES else False if t in SINGLE_TYPES else bool(RELATION_RE.search(q["q"]))
        q["labelled"] = bool(q["rel_chunks"])

    # 3 forecast
    n_pages = len(page_rows)
    p_est = round(n_sent * DENSE_X_RATIO)
    p_file = round(n_sent * summary["per_sentence"]) if summary["per_sentence"] else None
    fc = {g: forecast(n_pages, p_est, g, tpd) for g in GRADINGS}
    rendered = {(r["doc"], r["page"]): len(render_prompt(units, docs, r["doc"], r["page"], template)) for r in page_rows}
    biggest = max(rendered, key=lambda x: (rendered[x], -x[0], -x[1]))
    if pages:
        sample_pages = _parse_pages(pages, docs)
    else:
        cand = [(r["doc"], r["page"]) for r in page_rows if r["s"] + r["h"] > 0] or [(r["doc"], r["page"]) for r in page_rows]
        sample_pages = [cand[i] for i in sorted({int(round(x)) for x in np.linspace(0, len(cand) - 1, min(max(sample, 1), len(cand)))})]
    sample_rows = [{"key": page_key(docs, di, pn), "units": sum(1 for u in units.values() if u["doc"] == di and u["page"] == pn),
                    "chars": len(docs[di]["pages"][pn - 1]), "rendered": rendered[(di, pn)]} for di, pn in sample_pages]
    forecast_res = {"pages": n_pages, "sentences": n_sent, "p_est": p_est, "p_file": p_file, "rows": fc, "tpd": tpd, "tpm": TPM,
                    "chunks": len(chunks), "per_1k": {g: {"calls": fc[g]["calls"] * 1000 / len(chunks), "usd": fc[g]["usd"] * 1000 / len(chunks),
                                                          "tokens": fc[g]["tokens"] * 1000 / len(chunks)} for g in GRADINGS},
                    "index": [{"name": nm, "dim": dim, "chunks_kib": len(chunks) * dim * 4 / 1024, "props_kib": p_est * dim * 4 / 1024}
                              for dim, nm in DIMS],
                    "x": p_est / len(chunks), "mean_page_tokens": sum(len(p) for d in docs for p in d["pages"]) / n_pages * TOK_PER_CHAR,
                    "biggest": {"key": page_key(docs, *biggest), "chars": rendered[biggest], "tokens": rendered[biggest] * TOK_PER_CHAR},
                    "sample": sample_rows, "per_page_calls": 2 if grading == "batched" else 1,
                    "per_page_props": n_sent / n_pages * DENSE_X_RATIO}

    # 10 leakage
    texts = eval_texts(qs)
    leak = leakage(prompt_example_part(template), texts) if qs else None

    # faithfulness labels
    faith = None
    if lab is not None:
        known = {p["prop_id"] for p in plist}
        lab_problems += [f"label for {pid}: no such proposition in the propositions file" for pid in sorted(set(lab) - known)]
        got = {pid: v for pid, v in lab.items() if pid in known}
        n = len(got)
        x = sum(v == "supported" for v in got.values())
        faith = {"n": n, "supported": x, "added": sum(v == "added" for v in got.values()), "distorted": sum(v == "distorted" for v in got.values()),
                 "wilson": wilson(x, n) if n else None}
        withk = [(p, got[p["prop_id"]]) for p in plist if p["prop_id"] in got and p["kept"] is not None]
        good = [p for p, v in withk if v == "supported"]
        bad = [p for p, v in withk if v != "supported"]
        faith["filter"] = {"n": len(withk), "good": len(good), "bad": len(bad),
                           "keep_good": sum(p["kept"] for p in good) / len(good) if good else None,
                           "catch_bad": sum(not p["kept"] for p in bad) / len(bad) if bad else None} if withk else None

    # 6 dense ranking
    dense_res = {"requested": bool(dense), "status": None, "rows": {}, "summary": None}
    res = {"_docs": docs, "_units": units, "_chunks": chunks, "_checked": checked, "index": index, "settings": {"k": k}}
    if dense:
        fn, why = (embedder, None) if embedder is not None else load_minilm()
        if fn is None:
            dense_res["status"] = f"SKIPPED ({why}; section 6 needs --dense with a local MiniLM)"
        elif not index:
            dense_res["status"] = "SKIPPED (no valid propositions to rank)"
        else:
            dense_res["status"] = "custom embedder" if embedder is not None else f"{MINILM} (local)"
            Ec = _unit(fn([c["text"] for c in chunks]))
            Ep = _unit(fn([p["text"] for p, r in index]))
            Q = _unit(fn([q["q"] for q in qs])) if qs else np.zeros((0, Ec.shape[1]))
            for qi, q in enumerate(qs):
                if not q["labelled"]:
                    continue
                oc = ranked(Ec @ Q[qi])
                rr_c = next((1 / i for i, c in enumerate(oc, 1) if c in q["rel_chunks"] and i <= 10), 0.0)
                ce_c = ce(q["_G"], [(chunks[c]["doc"], chunks[c]["start"], chunks[c]["end"]) for c in oc[:k]], docs) if q["_G"] else None
                op = ranked(Ep @ Q[qi])
                s = score_order(res, q, op, k)
                dense_res["rows"][q["id"]] = {"rr_chunks": rr_c, "ce_chunks": ce_c, "top_chunks": [chunks[c]["id"] for c in oc[:k]], **s}
            rows = list(dense_res["rows"].values())
            if rows:
                mean = lambda key: (sum(r[key] for r in rows if r[key] is not None) / sum(r[key] is not None for r in rows)
                                    if any(r[key] is not None for r in rows) else None)
                dense_res["summary"] = {"n": len(rows), "mrr_chunks": mean("rr_chunks"), "mrr_a": mean("rr_a"), "mrr_b": mean("rr_b"),
                                        "mrr_text": mean("rr_text"), "ce_chunks": mean("ce_chunks"), "ce_a": mean("ce_a"), "ce_b": mean("ce_b"),
                                        "n_ce": sum(r["ce_a"] is not None for r in rows)}
                dense_res["summary"]["improved"] = dense_res["summary"]["mrr_a"] > dense_res["summary"]["mrr_chunks"]

    out = {"settings": {"k": k, "grading": grading, "budget_usd": budget_usd, "tpd": tpd, "chunk_size": chunk_size, "overlap": overlap,
                        "props_origin": props_origin, "prompt": "prop_gen_v1 (built in)" if template == PROMPT_V1 else "your template",
                        "pymupdf": _version("pymupdf"), "dense": bool(dense)},
           "docs": [{"name": d["name"], "pages": len(d["pages"]), "chars": len(d["text"]), "is_pdf": d["is_pdf"]} for d in docs],
           "page_rows": page_rows, "unit_stats": unit_stats, "limits": limits, "units": units,
           "chunks": [{"id": c["id"], "doc": c["doc"], "page": c["page"], "start": c["start"], "end": c["end"]} for c in chunks],
           "props": [{**p, **{x: v for x, v in r.items() if x != "prop_id"}, "dup_of": dup_of.get(p["prop_id"], [])} for p, r in checked],
           "prop_problems": prop_problems, "summary": summary, "coverage": {"rows": cov_rows, "total": cov_tot},
           "questions": qs, "gold_problems": gold_problems,
           "reach": (reach_hit, reach_alts), "forecast": forecast_res, "leak": leak, "n_eval_texts": len(texts),
           "labels": faith, "label_problems": lab_problems, "dense": dense_res,
           "_docs": docs, "_units": units, "_chunks": chunks, "_checked": checked, "index": index}
    out["checklist"] = checklist(out)
    out["recommendation"] = recommend(out)
    return out


# ---------------------------------------------------------------------------------------------------------------- checklist
def _ids(xs, n=12):
    xs = list(xs)
    return ", ".join(xs[:n]) + (f" and {len(xs) - n} more" if len(xs) > n else "")


def checklist(res):
    S, F, st = res["summary"], res["forecast"], res["settings"]
    out = []

    def add(cid, title, verdict, evidence, how):
        out.append({"id": cid, "title": title, "verdict": verdict, "evidence": evidence, "how": how})

    sel = F["rows"][st["grading"]]
    over_budget = st["budget_usd"] is not None and sel["usd"] > st["budget_usd"]
    over_quota = sel["tokens"] > st["tpd"]
    over_tpm = F["biggest"]["tokens"] > F["tpm"]
    add("C1", "Forecast before any call: calls, tokens and $ vs the budget and the daily quota",
        BAD if over_budget or over_quota or over_tpm else OK,
        f"grading {st['grading']}: {sel['calls']:,} calls, {sel['tokens']:,} tokens (ASSUMED per-call sizes), ${sel['usd']:.3f}, "
        f"{sel['days']:.2f} days of {st['tpd']:,} tokens per day"
        + (f"; budget ${st['budget_usd']:.2f} {'exceeded' if over_budget else 'kept'}" if st["budget_usd"] is not None else "; no budget given")
        + (f"; the largest page prompt alone is about {F['biggest']['tokens']:,.0f} tokens (DERIVED), over the {F['tpm']:,} tokens-per-minute limit"
           if over_tpm else ""),
        "section 3; replace the ASSUMED sizes with the provider's usage numbers after one recorded page")
    rate = (len(res["prop_problems"]) / S["records"]) if S["records"] else 0.0
    if not S["records"]:
        add("C2", "Responses are schema-valid; parse failures and length stops under 2%, logged", ASK,
            "no propositions file", "validate every response against proposition_set_v1; log json_validate_failed and finish_reason=length")
    else:
        add("C2", "Responses are schema-valid; parse failures and length stops under 2%, logged", BAD if rate >= FAIL_RATE else ASK,
            f"{len(res['prop_problems'])} of {S['records']} records are invalid ({rate:.1%}) and listed in section 4"
            + ("" if rate >= FAIL_RATE else "; parse-failure and finish_reason=length rates need the run log of a recorded LLM run (this tool sees only the file)"),
            "validate every response against proposition_set_v1; log json_validate_failed and finish_reason=length; never turn a failure into an empty list")
    c3_bad = S["bad_ids"] + S["outside"] + S["multi_page"] + S["page_mismatch"]
    if not S["loaded"]:
        add("C3", "Every source_id exists; every span lies inside the document", ASK, "no propositions", "check every id against the numbered units")
    else:
        add("C3", "Every source_id exists; every span lies inside the document", BAD if c3_bad else OK,
            (f"bad ids: {_ids(S['bad_ids'])}; " if S["bad_ids"] else "") + (f"span outside the text: {_ids(S['outside'])}; " if S["outside"] else "")
            + (f"sources on more than one page: {_ids(S['multi_page'])}; " if S["multi_page"] else "")
            + (f"page field differs from its units: {_ids(S['page_mismatch'])}; " if S["page_mismatch"] else "")
            + f"{S['valid']} of {S['loaded']} propositions have valid ids, spans inside the text and one page"
            + (f"; heading-only sources (the prompt allows a heading only with a sentence): {_ids(S['heading_only'])}" if S["heading_only"] else ""),
            "check every id against the numbered units; span(p) = [min a, max b) must lie inside the text")
    if not S["valid"]:
        add("C4", "Alignment: every proposition with align(p) < 1 is listed", ASK, "no valid propositions", "read each listed one against its source")
    else:
        fl = [p for p in res["props"] if p["prop_id"] in S["flagged"]]
        add("C4", "Alignment: every proposition with align(p) < 1 is listed", BAD if fl else OK,
            (f"{len(fl)} of {S['valid']} below 1: " + "; ".join(f"{p['prop_id']} {('-' if p['align'] is None else f'{p['align']:.3f}')} "
                                                               f"({' '.join(p['unsupported']) or 'no content words'})" for p in fl[:12])
             + (f" and {len(fl) - 12} more" if len(fl) > 12 else "")) if fl else
            f"0 of {S['valid']} below 1 (min {S['align_min']:.3f}); align sees only ADDED words: a dropped qualifier or a wrong referent passes, so read C5",
            "read each listed proposition against its source; an unsupported word is an added or changed fact until a person says otherwise")
    fa = res["labels"]
    if fa is None or fa["n"] == 0:
        add("C5", f"Hand-checked faithfulness on ≥ {MIN_FAITH} propositions, with a Wilson lower bound", ASK,
            "no labels yet: write the labelling sheet (--labels-csv), label at least 30 rows, then pass it back with --labels",
            "label supported / added / distorted against the source text; report supported / n with its Wilson interval")
    else:
        lo, hi = fa["wilson"]
        verdict = (OK if lo >= FAITH_BAR else BAD) if fa["n"] >= MIN_FAITH else ASK
        add("C5", f"Hand-checked faithfulness on ≥ {MIN_FAITH} propositions, with a Wilson lower bound", verdict,
            f"{fa['supported']}/{fa['n']} supported = {fa['supported'] / fa['n']:.3f}, Wilson 95% [{lo:.3f}, {hi:.3f}]; "
            f"added {fa['added']}, distorted {fa['distorted']}" + ("" if fa["n"] >= MIN_FAITH else f"; fewer than {MIN_FAITH} labels: label more")
            + f"; the bar is a lower bound ≥ {FAITH_BAR}",
            "label supported / added / distorted against the source text; report supported / n with its Wilson interval")
    cv, cn = res["coverage"]["total"]
    if not cn:
        add("C6", f"sentence_coverage ≥ {COVER_BAR}; sentences with no proposition are listed", ASK, "no valid propositions", "section 5")
    else:
        add("C6", f"sentence_coverage ≥ {COVER_BAR}; sentences with no proposition are listed", OK if cv / cn >= COVER_BAR else BAD,
            f"{cv}/{cn} = {cv / cn:.3f} of the sentences on the {len(res['coverage']['rows'])} page(s) with propositions; "
            f"{cn - cv} uncovered sentences are listed in section 5 (a page you wrote only in part counts as uncovered)",
            "every sentence that states a fact needs at least one proposition, or its fact is lost from the index")
    if not S["loaded"]:
        add("C7", "No pronoun-initial propositions (decontextualisation)", ASK, "no propositions", "replace It / They / This … with the name")
    else:
        add("C7", "No pronoun-initial propositions (decontextualisation)", BAD if S["pronoun"] else OK,
            (f"pronoun starts: {_ids(S['pronoun'])}" if S["pronoun"] else f"0 of {S['loaded']} start with a pronoun")
            + f"; {S['resolved_uses']} use a resolved name"
            + (f"; resolved name NOT found earlier on the page: {_ids(S['resolved_bad'])}" if S["resolved_bad"] else
               ("; every resolved name occurs earlier on its page" if S["resolved_uses"] else "")),
            "replace It / They / These … with the full name used earlier on the page, and list that name in resolved")
    d = res["dense"]
    df = [r["distinct_facts"] for r in d["rows"].values()]
    if not S["loaded"]:
        add("C8", "Near-duplicates: distinct-facts@k and the share of duplicate texts", ASK, "no propositions", "section 4")
    else:
        share = 1 - S["distinct"] / S["loaded"]
        add("C8", "Near-duplicates: distinct-facts@k and the share of duplicate texts", BAD if S["dup_groups"] else OK,
            f"{S['distinct']} distinct normalised texts in {S['loaded']} propositions (duplicate share {share:.3f})"
            + (": " + "; ".join(" = ".join(g) for g in S["dup_groups"][:8]) if S["dup_groups"] else "")
            + (f"; distinct-facts@{st['k']} per question {df}" if df else f"; distinct-facts@{st['k']} needs a ranking (--dense)"),
            "identical texts take several top-k places; deduplicate at query time or keep them knowingly (a document that repeats itself)")
    if st["grading"] == "off":
        add("C9", "The quality grade is compared with your labels (keep-good, catch-bad, n)", OK,
            "grading off: no filter to calibrate", "keep-good = kept ∧ good / good; catch-bad = dropped ∧ bad / bad")
    elif fa and fa.get("filter"):
        f = fa["filter"]
        add("C9", "The quality grade is compared with your labels (keep-good, catch-bad, n)", OK,
            f"n = {f['n']} labelled propositions with a kept flag: keep-good {('-' if f['keep_good'] is None else f'{f['keep_good']:.3f}')} "
            f"(of {f['good']} good), catch-bad {('-' if f['catch_bad'] is None else f'{f['catch_bad']:.3f}')} (of {f['bad']} bad); "
            "the 7/10 threshold is uncalibrated until these numbers say otherwise",
            "keep-good = kept ∧ good / good; catch-bad = dropped ∧ bad / bad")
    else:
        add("C9", "The quality grade is compared with your labels (keep-good, catch-bad, n)", ASK,
            f"grading {st['grading']}: needs labels (--labels) and the grader's kept flag in the propositions file",
            "keep-good = kept ∧ good / good; catch-bad = dropped ∧ bad / bad; the grade is a filter, not a faithfulness measurement")
    lk = res["leak"]
    if lk is None:
        add("C10", "No eval question or gold quote in the prompt (8-gram test); no book text", ASK,
            "no questions given, nothing to compare; book text: check by hand (the privacy guard is not built yet)",
            "8-gram overlap of the template and its example with the questions, gold quotes and expect texts")
    else:
        add("C10", "No eval question or gold quote in the prompt (8-gram test); no book text", BAD if lk["shared"] else OK,
            f"{len(lk['shared'])} shared 8-grams between the prompt's template + example and {res['n_eval_texts']} eval texts "
            f"({lk['eval_ngrams']} distinct 8-grams)" + (f", e.g. '{lk['shared'][0]}'" if lk["shared"] else "")
            + "; book text: check by hand (the privacy guard is not built yet)",
            "write the few-shot example from outside your corpus; re-run this test whenever the prompt changes")
    qs = [q for q in res["questions"] if q["answerable"]]
    if not qs:
        add("C11", "Your questions are mostly single-fact lookups, not compare or summarise", ASK, "no answerable questions given",
            "type each question (factual-single-span, multi-span, multi-hop …)")
    else:
        relq = [q["id"] for q in qs if q["relation"]]
        add("C11", "Your questions are mostly single-fact lookups, not compare or summarise", BAD if len(relq) > len(qs) / 2 else OK,
            f"{len(relq)} of {len(qs)} answerable questions need a relation between facts (from type, else wording)"
            + (f": {_ids(relq)}" if relq else ""),
            "propositions lose the relation between facts; check the types by hand")
    pp = F["per_page_calls"]
    add("C12", "The corpus is stable (re-indexing cost on change)", ASK,
        f"each changed page costs {pp} call(s) with grading {st['grading']}"
        + (f" plus about {F['per_page_props']:.0f} grading calls" if st["grading"] == "per-prop" else "")
        + f"; re-indexing all {F['pages']} pages = {F['rows'][st['grading']]['calls']:,} calls",
        "how often do your documents change? A weekly change multiplies the index cost")
    return out


def recommend(res):
    c = {x["id"]: x["verdict"] for x in res["checklist"]}
    S, d, fa = res["summary"], res["dense"]["summary"], res["labels"]
    n_lab = d["n"] if d else 0
    if c["C2"] == BAD or c["C3"] == BAD:
        return "Fix generation first: some records or source ids are broken (C2/C3). Fix the token cap, the schema and the ids before measuring anything."
    if c["C5"] == BAD or (S["valid"] and len(S["flagged"]) / S["valid"] >= MANY_FLAGS):
        return ("Propositions are rewriting facts (C4/C5): do not index them. Fix the prompt, or consider contextual chunk headers (I5) instead.")
    if c["C11"] == BAD:
        return "Keep chunks: most of your questions compare or combine facts, and propositions lose the relation between facts (C11)."
    if d and not d["improved"] and c["C1"] == BAD:
        return "Not worth the index cost: arm (a) MRR@10 did not beat the plain chunks, and the forecast is over your budget or quota (C1)."
    missing = []
    if c["C5"] != OK:
        missing.append(f"label at least {MIN_FAITH} propositions with the labelling sheet (C5)")
    if n_lab < MIN_LABELLED:
        missing.append(f"run --dense with at least {MIN_LABELLED} labelled questions (arm (a) vs the plain chunks; now {n_lab})")
    if missing:
        return "Not decided yet: " + "; ".join(missing) + ". The checks above say whether these propositions can be trusted, not whether they help."
    if not d["improved"]:
        return ("No gain measured: arm (a) MRR@10 did not beat the plain chunks on these questions. Keep chunks and record the result "
                "as inconclusive, not as a loss.")
    return "Adopt as a multi-vector index that returns parent chunks (arm (a)); re-run this check whenever your documents change."


# ---------------------------------------------------------------------------------------------------------------- report
def _c(x):
    return str(x).replace("|", "\\|").replace("\n", " ")


def _f(x, n=3):
    return "-" if x is None else f"{x:.{n}f}"


def render_report(res):
    st, S, F, U, L = res["settings"], res["summary"], res["forecast"], res["unit_stats"], res["limits"]
    units, chunks, k = res["units"], res["chunks"], st["k"]
    cl = " ".join(f"{x['id']} {x['verdict']}" for x in res["checklist"])
    origin = {"hand": "hand-written (not LLM output)", "llm": "exported from a recorded LLM run", "unknown": "origin not stated"}[st["props_origin"]]
    out = ["# Proposition fit check", "",
           "**What this is:** an automatic check of whether proposition indexing suits these documents: the units, the cost forecast, "
           "and code checks of each proposition against its source.",
           "**What this is not:** an evaluation of proposition indexing. No LLM is called; a few questions show the mechanism, not a result.", "",
           f"**Recommendation:** {res['recommendation']} (section 8). Checklist: {cl}.", "",
           "## 1 Settings and documents", "",
           "Documents: " + "; ".join(f"`{d['name']}` ({d['pages']} page(s), {d['chars']:,} characters with pages joined by a line break)" for d in res["docs"]) + ".",
           f"Propositions: {S['loaded']} loaded from {S['records']} record(s), {origin}. Questions: {len(res['questions'])}."
           + (f" Labels: {res['labels']['n']} hand labels." if res["labels"] else ""),
           f"Settings: prompt {st['prompt']} · grading `{st['grading']}` · k {k} · parents = v0 chunks ({st['chunk_size']} characters, "
           f"overlap {st['overlap']}, per page) · daily quota {st['tpd']:,} tokens"
           + (f" · budget ${st['budget_usd']:.2f}" if st["budget_usd"] is not None else "")
           + (f" · pymupdf {st['pymupdf']}" if st["pymupdf"] else "") + ". No API call.", "",
           "| Number | Status |", "|---|---|",
           "| Units, spans, align, parents, coverage, duplicates, 8-gram test | measured on your files by this tool |",
           f"| Tokens per call ({ASSUME['gen'][0]:,} in / {ASSUME['gen'][1]:,} out per page to generate; {ASSUME['batched'][0]:,} / {ASSUME['batched'][1]:,} "
           f"batched grade; {ASSUME['per-prop'][0]:,} / {ASSUME['per-prop'][1]:,} per-proposition grade) | **ASSUMED** (research I4 §9), not measured |",
           f"| Prices ${PRICE_IN:.3f} / ${PRICE_OUT:.2f} per 1M tokens (Groq openai/gpt-oss-20b); {TPD:,} tokens per day, {TPM:,} per minute | CITED (LLMOPS §6.2); the plan row is UNVERIFIED |",
           f"| Propositions per sentence {DENSE_X_RATIO:.3f} | CITED (Dense X README: 257M / 114M) |",
           f"| Page and prompt tokens (characters × {TOK_PER_CHAR:.4f}) | DERIVED (P1's measured ratio on the climate PDF); a proxy for your text |", ""]

    # 2 units
    out += ["## 2 Units", "",
            f"{U['sentences']:,} sentences and {U['headings']:,} headings ({U['units']:,} units) on {len(res['page_rows'])} page(s); sentences per page "
            f"min {U['min']} / median {U['median']} / max {U['max']}; {U['words4']:,} sentences have at least 4 words. "
            f"Every unit's offsets give back its text: {U['spans_ok']}.", "",
            "| Page | Sentences | Headings | Unit ids |", "|---|---|---|---|"]
    for r in res["page_rows"][:MAX_ROWS]:
        out.append(f"| {r['key']} | {r['s']} | {r['h']} | {(r['first'] + ' – ' + r['last']) if r['first'] else '-'} |")
    if len(res["page_rows"]) > MAX_ROWS:
        out.append(f"| … | | | {len(res['page_rows']) - MAX_ROWS} more pages |")
    out += ["", "Known splitter limits on this text (shown, not fixed):",
            "- Page-start fragments (a sentence cut by the page break, starting in lower case): "
            + (", ".join(f"{u} {units[u]['text'][:40]!r}" for u in L["fragments"][:10]) + (f" and {len(L['fragments']) - 10} more" if len(L["fragments"]) > 10 else "")
               if L["fragments"] else "none") + ".",
            "- Last sentence of a page with no end punctuation (cut at the page end): "
            + (", ".join(L["cut_at_end"][:10]) + (f" and {len(L['cut_at_end']) - 10} more" if len(L["cut_at_end"]) > 10 else "") if L["cut_at_end"] else "none") + ".",
            f"- 'e.g.' or 'i.e.' would end a sentence early: {L['eg']} occurrence(s).", ""]

    # 3 forecast
    out += ["## 3 Forecast for the whole collection", "",
            f"{F['pages']} pages (one generation call each), {F['sentences']:,} sentences → about **{F['p_est']:,} propositions** at Dense X's "
            f"{DENSE_X_RATIO:.3f} per sentence" + (f" (about {F['p_file']:,} at your file's {S['per_sentence']:.2f})" if F["p_file"] else "") + ".", "",
            f"| Grading | Calls | Tokens (ASSUMED sizes) | $ | Days of {F['tpd']:,} tokens per day | Minutes at {F['tpm']:,} per minute, at least |",
            "|---|---|---|---|---|---|"]
    for g in GRADINGS:
        r = F["rows"][g]
        b = "**" if g == st["grading"] else ""
        out.append(f"| {b}{g}{b} | {r['calls']:,} | {r['tokens']:,} | ${r['usd']:.3f} | {r['days']:.2f} | {r['minutes']:.0f} |")
    out += ["", f"Per 1k chunks (DERIVED: × 1000 / {F['chunks']} v0 chunks): "
            + "; ".join(f"{g} {F['per_1k'][g]['calls']:,.0f} calls, ${F['per_1k'][g]['usd']:.2f}" for g in GRADINGS) + ".", "",
            "| Embedder | Numbers per vector | Chunks (KiB) | Propositions (KiB) |", "|---|---|---|---|"]
    for r in F["index"]:
        out.append(f"| {r['name']} | {r['dim']} | {r['chunks_kib']:,.0f} | {r['props_kib']:,.0f} |")
    out += ["", f"Index size = n × dim × 4 bytes: **×{F['x']:.1f} vectors** ({F['p_est']:,} propositions vs {F['chunks']} chunks).", "",
            f"Prompt `{st['prompt']}` on the sample pages (`--render-prompt PAGE` prints one, to run it by hand):", "",
            "| Page | Units | Page characters | Page tokens (DERIVED) | Rendered prompt characters | about tokens (DERIVED) |", "|---|---|---|---|---|---|"]
    for r in F["sample"]:
        out.append(f"| {r['key']} | {r['units']} | {r['chars']:,} | {r['chars'] * TOK_PER_CHAR:,.0f} | {r['rendered']:,} | {r['rendered'] * TOK_PER_CHAR:,.0f} |")
    out += ["", f"Mean page: about {F['mean_page_tokens']:,.0f} tokens (DERIVED); the ASSUMED generation input is {ASSUME['gen'][0]:,}. "
            f"Largest rendered prompt: page {F['biggest']['key']}, {F['biggest']['chars']:,} characters, about {F['biggest']['tokens']:,.0f} tokens. "
            "The output side (about 45 propositions plus reasoning) is the larger, unmeasured share: size `max_completion_tokens` for it and log `finish_reason=length`.", ""]

    # 4 propositions
    out += ["## 4 Proposition checks", ""]
    if not S["records"]:
        out += ["No propositions file given (use --props).", ""]
    else:
        np_ = S["n_parents"]
        out += [f"{S['loaded']} propositions; {S['valid']} with valid ids; {S['indexed']} indexed (kept). By page: "
                + ", ".join(f"p.{pg} {n}" for pg, n in sorted(S["by_page"].items(), key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', x[0])])) + ".",
                f"- align: min {_f(S['align_min'])}; below 1: {len(S['flagged'])} ({_ids(S['flagged']) or 'none'}).",
                f"- Pronoun starts: {len(S['pronoun'])} ({_ids(S['pronoun']) or 'none'}). Resolved names used by {S['resolved_uses']}; not found earlier on the page: "
                f"{_ids(S['resolved_bad']) or 'none'}.",
                f"- Parents: span inside one chunk for {S['contained']}/{S['valid']}; " + ", ".join(f"{n} parent(s) {c}" for n, c in sorted(np_.items()))
                + " (two parents = the 200-character overlap); primary = the first.",
                f"- {S['valid']} propositions from {S['source_sentences']} source sentences"
                + (f" = {S['per_sentence']:.2f} per sentence (Dense X: {DENSE_X_RATIO:.2f})." if S["per_sentence"] else "."),
                f"- Identical normalised texts: {len(S['dup_groups'])} group(s)" + (": " + "; ".join(" = ".join(g) for g in S["dup_groups"][:10]) if S["dup_groups"] else "") + ".", ""]
        if res["prop_problems"]:
            out += ["Invalid records (logged, left out):", ""] + [f"- {x}" for x in res["prop_problems"][:MAX_ROWS]] + [""]
        out += ["| Proposition | Source ids | span(p) | align | Unsupported | Pronoun | Parents | Text |", "|---|---|---|---|---|---|---|---|"]
        for p in res["props"][:200]:
            if not p["ids_ok"]:
                out.append(f"| {p['prop_id']} | {' '.join(p['source_ids'])} (**bad: {' '.join(p['bad_ids'])}**) | - | - | - | "
                           f"{'**yes**' if p['pronoun'] else 'no'} | - | {_c(p['text'][:160])} |")
                continue
            sp = p["span"]
            out.append(f"| {p['prop_id']} | {' '.join(p['source_ids'])} | [{sp[1]:,}, {sp[2]:,}) | {('**' + _f(p['align']) + '**') if p['align'] is None or p['align'] < 1 else _f(p['align'])} | "
                       f"{' '.join(p['unsupported']) or '-'} | {'**yes**' if p['pronoun'] else 'no'} | {', '.join(chunks[i]['id'] for i in p['parents'])} | "
                       f"{_c(p['text'][:160])}{' (dup: ' + ', '.join(p['dup_of']) + ')' if p['dup_of'] else ''} |")
        if len(res["props"]) > 200:
            out.append(f"| … | | | | | | | {len(res['props']) - 200} more |")
        out += ["", "align counts only ADDED words: a dropped qualifier (\"well below\" → \"below\") or a wrong referent passes it. "
                "Only a person reading against the source catches those (C5, the labelling sheet).", ""]

    # 5 coverage
    out += ["## 5 Coverage", ""]
    cr, (cv, cn) = res["coverage"]["rows"], res["coverage"]["total"]
    if not cr:
        out += ["No valid propositions, so no coverage.", ""]
    else:
        out += [f"sentence_coverage on the pages with propositions: {cv}/{cn} = {cv / cn:.3f}. A page you wrote only in part shows its other "
                "sentences as uncovered: that is a property of your sample, not of the method.", "",
                "| Page | Covered / sentences | sentence_coverage | Uncovered sentences |", "|---|---|---|---|"]
        for r in cr:
            out.append(f"| {r['key']} | {r['covered']}/{r['sentences']} | {r['covered'] / r['sentences']:.3f} | {_ids(r['missing'], 20) or 'none'} |")
        miss = [u for r in cr for u in r["missing"]]
        if miss:
            out += ["", "Uncovered sentences (facts the index would not hold):", ""]
            out += [f"- [{u}] {_c(' '.join(units[u]['text'].split())[:160])}" for u in miss[:MAX_ROWS]]
            if len(miss) > MAX_ROWS:
                out.append(f"- … {len(miss) - MAX_ROWS} more")
        out.append("")
    h, n = res["reach"]
    if n:
        out += [f"gold_reachability: {h}/{n} = {h / n:.3f} gold alternatives are overlapped by some span(p). Arm (b) can never beat it.", ""]
    if res["gold_problems"]:
        out += ["Gold problems:", ""] + [f"- {x}" for x in res["gold_problems"]] + [""]

    # 6 per question
    out += ["## 6 Per question", ""]
    qs = res["questions"]
    if not qs:
        out += ["No questions given (use --questions).", ""]
    else:
        draft = sum(q.get("created_by") == "llm-draft" for q in qs)
        if draft:
            out += [f"> **Draft questions:** {draft} of {len(qs)} are `created_by: llm-draft`: an illustration of the mechanism, not checked labels.", ""]
        out += ["| Question | Type | Needs a relation | Relevant chunks | Propositions on the gold | Text states an expect | Gold groups reachable |",
                "|---|---|---|---|---|---|---|"]
        for q in qs:
            out.append(f"| {q['id']}: {_c(q['q'][:70])} | {q['type'] or '-'} | {'yes' if q['relation'] else 'no'} | "
                       f"{', '.join(chunks[i]['id'] for i in q['rel_chunks']) or '-'} | {_ids(q['rel_props'], 8) or '-'} | {_ids(q['text_props'], 8) or '-'} | "
                       f"{' '.join('yes' if any(g) else 'no' for g in q['reach']) if q['reach'] else '-'} |")
        out.append("")
        d = res["dense"]
        if not d["requested"]:
            out += ["Ranking (arm (a) vs the plain chunks, arm (b), the text check) needs `--dense` (a local MiniLM). Not run here.", ""]
        elif not d["rows"]:
            out += [f"Ranking: {d['status'] or 'no labelled question (give gold or an expect text)'}.", ""]
        else:
            out += [f"Ranking with {d['status']}. MRR@10 counts a rank above 10 as 0; CE@{k} needs gold. Arm (a) cuts at the top {k} "
                    f"propositions, so it returns at most {k} parents, often fewer.", "",
                    f"| Question | Chunks RR / CE@{k} | Arm (a) RR / CE@{k} (parents in top {k}) | Arm (b) RR / CE@{k} | Text check RR | distinct-facts@{k} |",
                    "|---|---|---|---|---|---|"]
            for qid, r in d["rows"].items():
                out.append(f"| {qid} | {_f(r['rr_chunks'])} / {_r(r['ce_chunks'])} | {_f(r['rr_a'])} / {_r(r['ce_a'])} ({len(r['top_parents'])}) | "
                           f"{_f(r['rr_b'])} / {_r(r['ce_b'])} | {_f(r['rr_text'])} | {r['distinct_facts']} |")
            s = d["summary"]
            out += ["", f"Means over {s['n']} labelled question(s): MRR@10 chunks {_f(s['mrr_chunks'])}, arm (a) {_f(s['mrr_a'])}, arm (b) {_f(s['mrr_b'])}, "
                    f"text check {_f(s['mrr_text'])}; CE@{k} (over {s['n_ce']} with gold) chunks {_f(s['ce_chunks'])}, arm (a) {_f(s['ce_a'])}, arm (b) {_f(s['ce_b'])}. "
                    f"Arm (a) {'beats' if s['improved'] else 'does not beat'} the plain chunks on MRR@10." + (
                        f" With fewer than {MIN_LABELLED} questions this is a mechanism check, not a result." if s["n"] < MIN_LABELLED else ""), ""]

    # 7, 8
    out += ["## 7 Checklist", "", "| Check | Verdict | Evidence | How to check |", "|---|---|---|---|"]
    for x in res["checklist"]:
        out.append(f"| {x['id']} {_c(x['title'])} | {x['verdict']} | {_c(x['evidence'])} | {_c(x['how'])} |")
    out += ["", "✓ fine · ✗ problem found · ? check by hand.", "", "## 8 Recommendation", "", res["recommendation"], "",
            "Order of the rules: C2/C3 broken output → C5/C4 rewritten facts → C11 relation questions → no gain at a high cost (C1) → "
            "not enough evidence → no gain → adopt.", "",
            "Lesson: `study/lessons/I4_propositions.html`. This report is a mechanism check on your data, not an evaluation result."]
    return "\n".join(out) + "\n"


def _r(x):
    return "-" if x is None else str(x)


def labels_csv(res):
    """The labelling sheet for C5: one row per proposition with its source text; fill in "label" and "note"."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["prop_id", "page", "source_ids", "source_text", "proposition", "align", "unsupported", "label", "note"])
    units = res["units"]
    for p in res["props"]:
        src = " ".join(" ".join(units[u]["text"].split()) for u in p["source_ids"] if u in units) if p["ids_ok"] else "(source id not found)"
        page = page_key(res["_docs"], p["doc"], p["page"]) if p["ids_ok"] else (p.get("page") or "")
        w.writerow([p["prop_id"], page, " ".join(p["source_ids"]), src, p["text"], _f(p["align"]) if p["align"] is not None else "",
                    " ".join(p["unsupported"] or []), "", ""])
    return buf.getvalue()


# ---------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Would proposition indexing help on my documents, what would it cost, and are the "
                                             "propositions faithful? Writes a Markdown report. No API calls.")
    ap.add_argument("--docs", nargs="+", required=True, help="files or folders (.pdf, .txt, .md); one document per file")
    ap.add_argument("--props", help="propositions JSONL ({\"prop_id\", \"page\", \"text\", \"source_ids\", \"resolved\", \"kept\"})")
    ap.add_argument("--props-origin", choices=("hand", "llm", "unknown"), default="unknown", help="who wrote the propositions (printed in the report)")
    ap.add_argument("--questions", help="questions JSONL ({\"id\", \"q\", \"expect\", \"type\", \"gold\"}) or the 06 §6.7 form")
    ap.add_argument("--pages", help="sample pages for the prompt render, e.g. 10,23 (or stem#10 with several documents)")
    ap.add_argument("--sample", type=int, default=3, help="number of evenly spaced sample pages when --pages is not given (default 3)")
    ap.add_argument("--render-prompt", metavar="PAGE", help="print the prop_gen_v1 prompt for this page and stop (run it by hand)")
    ap.add_argument("--prompt", help="your own prompt template (must contain {units}); default: the built-in prop_gen_v1")
    ap.add_argument("--grading", choices=GRADINGS, default="batched", help="quality grade in the forecast (default batched: one call per page)")
    ap.add_argument("--budget-usd", type=float, help="your budget for one index build (check C1)")
    ap.add_argument("--tpd", type=int, default=TPD, help=f"daily token quota (default {TPD:,})")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--dense", action="store_true", help="rank with a local MiniLM (section 6); skipped with a message if missing")
    ap.add_argument("--labels", help="the labelling sheet with the label column filled in (checks C5, C9)")
    ap.add_argument("--labels-csv", help="write the labelling sheet here")
    ap.add_argument("--provider", choices=("none", "groq", "anthropic"), default="none")
    ap.add_argument("--report", help="write the Markdown report here (default: print it)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    if a.provider != "none":
        print(f"--provider {a.provider} is not available yet: it needs the course's study/llmops/ cache (record once, replay offline), "
              "which is not built. Write the propositions by hand, or export them from a recorded run, and pass them with --props. "
              "Never send private or book text to an API.", file=sys.stderr)
        return 2
    if a.render_prompt:
        docs = load_documents(a.docs)
        units = make_units(docs)
        template = Path(a.prompt).read_text(encoding="utf-8") if a.prompt else PROMPT_V1
        (di, pg), = _parse_pages(a.render_prompt, docs)
        sys.stdout.write(render_prompt(units, docs, di, pg, template))
        return 0
    res = run_check(a.docs, props=a.props, questions=a.questions, pages=a.pages, sample=a.sample, grading=a.grading,
                    budget_usd=a.budget_usd, tpd=a.tpd, dense=a.dense, k=a.k, labels=a.labels,
                    prompt=Path(a.prompt) if a.prompt else None, props_origin=a.props_origin)
    if a.dense and res["dense"]["status"] and res["dense"]["status"].startswith("SKIPPED"):
        print(f"--dense {res['dense']['status']}", file=sys.stderr)
    text = render_report(res)
    if a.labels_csv:
        Path(a.labels_csv).parent.mkdir(parents=True, exist_ok=True)
        Path(a.labels_csv).write_text(labels_csv(res), encoding="utf-8-sig", newline="")
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8", newline="\n")
        for x in res["checklist"]:
            print(f"{x['id']:4s} {x['verdict']}  {x['title']}")
        print(f"recommendation: {res['recommendation']}")
        print(f"report: {a.report}" + (f" · labelling sheet: {a.labels_csv}" if a.labels_csv else ""))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
