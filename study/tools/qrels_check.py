"""qrels_check: are my relevance labels good enough to measure retrieval on MY documents?

What this is: a command-line tool (also importable) that chunks your documents as the P2/P3 lessons do, builds the P2
inverted index, runs your questions through its own keyword-overlap retriever (and, with --dense, a local MiniLM
retriever), reads your relevance labels, and writes a Markdown report:
  1 Collection and index     chunks, vocabulary, postings, df = 1 terms, the commonest terms; postings equal a scan
  2 Questions vs the index   per question: tokens, tokens with no postings, AND / OR set sizes, postings read, flags
  3 Label audit              what the labels say, per question; reasons, versions, timestamps, problems; with --spans
                             the span -> chunk conversion; 5 relevant pairs to re-read
  4 Pool and holes           per run: Judged@k, Hole@k, pool depth, P@k with holes as 0 and as relevant; the holes;
                             ties at the cut-off; with --pool-from, full labels vs a simulated pool
  5 Set vs ranking           per question and run: the top k with marks, P@k, R@k, first relevant rank, RR
  6 Checklist                Q1-Q12 with a verdict (✓ fine, ✗ problem found, ? check by hand), the evidence, how to check
  7 Recommendation           first matching rule wins (see recommend())
Also a normalised TREC qrels file (--trec-out): "qid 0 chunk_id grade", one line per judged pair.
What this is not: an evaluation of your retriever. It checks whether the labels can carry one.

Definitions (P2 lesson):
  tokens          lowercase runs of [a-z0-9] (no stemming, no stop words), for documents and questions alike
  keyword run     candidates = the union of the question tokens' postings; score = number of distinct question tokens in
                  the chunk; ties: the earlier chunk first (document order). Only chunks with score > 0 are returned
  dense run       MiniLM (sentence-transformers/all-MiniLM-L6-v2, local, normalised, cosine = dot) over every chunk
  relevant        grade >= --min-grade (default 1). Unjudged pairs count as not relevant, except where stated
  P@k             relevant chunks in the top k / chunks returned in the top k (0 when nothing is returned)
  R@k             relevant chunks in the top k / relevant chunks for the question (undefined when there are none)
  Judged@k        judged chunks in the top k / k;  Hole@k = unjudged chunks in the top k / k (empty slots are neither)
  pool depth      the largest d such that every question's top d in this run is judged
Means of P@k and R@k are over answerable questions (and R@k only over those with at least one relevant chunk).

Labels (one of):
  --qrels FILE    JSONL, one label per line: {"qid", "doc", "grade", "why", "judge", "guideline_version", "ts"}
                  ("did", "docid" or "chunk" are accepted for "doc"), or TREC 4 columns "qid 0 doc grade".
                  Unlisted pairs are unjudged (TREC rule); --unlisted zero says you judged every pair.
  --spans FILE    06 §6.7 form (qid, question, category, answerable, evidence_groups, created_by, notes): each span is
                  converted to chunk labels with any_overlap (06 §7.2: the chunk overlaps >= 1 non-whitespace character
                  of a segment; offsets: page-relative, pages joined with "\\n"). Every chunk is labelled (0 = no overlap).
Questions: --questions FILE (JSONL: "id" or "qid", "q" or "question", optional "need", "type", "answerable"), or the
spans file's own questions.
Runs: the keyword run always; --dense adds MiniLM; --runs adds TREC run files ("qid Q0 doc rank score tag") or JSONL
({"qid", "docs": [...]} or {"qid", "doc", "rank", "score"}; an optional "ts" says when the run was made).
--pool-from keyword:3[,dense:3] simulates a pool: only those runs' top d are judged (labels taken from your full labels,
unlisted = 0), and every check uses the pooled labels. This shows what a one-retriever pool hides (P2 lesson, K4).

No API calls, no network: standard library + numpy + pymupdf; sentence-transformers only with --dense (MiniLM from the
local Hugging Face cache, HF_HUB_OFFLINE=1).

Usage, from rag_learning/:
    uv run python study/tools/qrels_check.py --docs my_docs/ --questions q.jsonl --qrels qrels.jsonl --dense --report r.md
    uv run python study/tools/qrels_check.py --docs a.pdf --doc-ids a --spans gold.jsonl --dense --report r.md --trec-out qrels.trec
    uv run python study/tools/qrels_check.py --chunks chunks.jsonl --questions q.jsonl --qrels qrels.jsonl --dense --pool-from keyword:3

Import:
    from qrels_check import run_check, render_report
    result = run_check(docs=["doc.pdf"], spans="gold.jsonl", dense=True, k=4)
    print(render_report(result))
"""
from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")             # never download the dense model
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import argparse
import bisect
import collections
import datetime as dt
import hashlib
import importlib.metadata as md
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

OK, BAD, ASK = "✓", "✗", "?"
EXTS = (".pdf", ".txt", ".md")
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
TOKEN_RE = re.compile(r"[a-z0-9]+")
NAN = float("nan")
MAX_LIST = 40


def tokenize(text):
    """P2's tokenizer: lowercase, runs of [a-z0-9]. 'Sea-level RISE, 2019!' -> ['sea', 'level', 'rise', '2019']."""
    return TOKEN_RE.findall(text.lower())


def norm_ws(s):
    return " ".join(s.split())


# ---------------------------------------------------------------------------------------------------------------- input
def load_documents(paths, doc_ids=None):
    """Files or folders (.pdf, .txt, .md). Pages are joined with "\\n" (PyMuPDF page.get_text() for PDFs)."""
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
    if doc_ids and len(doc_ids) != len(files):
        raise ValueError(f"--doc-ids gives {len(doc_ids)} ids for {len(files)} documents")
    docs = []
    for n, f in enumerate(files):
        if f.suffix.lower() == ".pdf":
            import pymupdf                                  # pinned 1.26.7 in this project
            with pymupdf.open(f) as d:
                pages = [pg.get_text() for pg in d]
        else:
            pages = [f.read_text(encoding="utf-8", errors="replace")]
        starts, pos = [], 0
        for pg in pages:
            starts.append(pos)
            pos += len(pg) + 1
        docs.append({"id": doc_ids[n] if doc_ids else f.stem, "name": f.name, "pages": pages, "page_starts": starts,
                     "is_pdf": f.suffix.lower() == ".pdf", "text": "\n".join(pages)})
    if len({d["id"] for d in docs}) != len(docs):
        raise ValueError("two documents have the same id; pass --doc-ids")
    return docs


def make_windows(docs, size=1000, overlap=200):
    """Plain character windows per document: 1,000 / step 800 gives the climate PDF's 91 windows. Id: '<doc id>#<j>'."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need chunk-size > 0 and 0 <= overlap < chunk-size")
    chunks = []
    for di, d in enumerate(docs):
        text = d["text"]
        for j, a in enumerate(range(0, len(text), size - overlap)):
            e = min(a + size, len(text))
            chunks.append({"id": f"{d['id']}#{j}", "doc": di, "start": a, "end": e, "text": text[a:e],
                           "page": bisect.bisect_right(d["page_starts"], a) if d["is_pdf"] else None})
    return chunks


def _jsonl(path):
    out = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}, line {n}: not valid JSON ({e})") from None
    return out


def load_chunks(path):
    """JSONL {"id", "text"} (your own chunks or whole short documents)."""
    chunks = []
    for n, r in enumerate(_jsonl(path), 1):
        cid, text = r.get("id", r.get("chunk_id")), r.get("text")
        if cid is None or text is None:
            raise ValueError(f"{path}, chunk {n}: needs \"id\" and \"text\"")
        chunks.append({"id": str(cid), "doc": None, "start": None, "end": None, "text": str(text), "page": r.get("page")})
    if len({c["id"] for c in chunks}) != len(chunks):
        raise ValueError(f"{path}: chunk ids are not unique")
    return chunks


def load_questions(source):
    """JSONL (or a list of dicts): id/qid, q/question, optional need, type/category, answerable."""
    items = _jsonl(source) if isinstance(source, (str, Path)) else list(source)
    out = []
    for n, it in enumerate(items, 1):
        qid, q = it.get("id", it.get("qid")), it.get("q", it.get("question"))
        if qid is None or not str(q or "").strip():
            raise ValueError(f"question {n}: needs an id (\"id\" or \"qid\") and a text (\"q\" or \"question\")")
        out.append({"id": str(qid), "q": str(q), "need": it.get("need"), "type": it.get("type", it.get("category")),
                    "answerable": it.get("answerable"), "created_by": it.get("created_by"), "notes": it.get("notes")})
    if len({q["id"] for q in out}) != len(out):
        raise ValueError("question ids are not unique")
    return out


def _is_jsonl(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            return line.lstrip().startswith("{")
    return False


def load_qrels(path, guideline_version=None):
    """JSONL or TREC 4-column qrels -> {"format", "labels": [{qid, doc, grade, why, judge, guideline_version, ts, line}]}."""
    labels = []
    if _is_jsonl(path):
        fmt = "JSONL"
        for n, r in enumerate(_jsonl(path), 1):
            doc = r.get("doc", r.get("did", r.get("docid", r.get("chunk"))))
            if r.get("qid") is None or doc is None or r.get("grade") is None:
                raise ValueError(f"{path}, line {n}: needs \"qid\", \"doc\" and \"grade\"")
            g = r["grade"]
            if isinstance(g, bool) or not isinstance(g, int) or g < 0:
                raise ValueError(f"{path}, line {n}: grade must be a whole number >= 0, got {g!r}")
            labels.append({"qid": str(r["qid"]), "doc": str(doc), "grade": g, "why": r.get("why"), "judge": r.get("judge"),
                           "guideline_version": r.get("guideline_version") or guideline_version, "ts": r.get("ts"), "line": n})
    else:
        fmt = "TREC"
        for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
            parts = line.split()
            if not parts or parts[0].startswith("#"):
                continue
            if len(parts) != 4 or not re.fullmatch(r"\d+", parts[3]):
                raise ValueError(f"{path}, line {n}: TREC qrels need 4 columns 'qid 0 doc grade'")
            labels.append({"qid": parts[0], "doc": parts[2], "grade": int(parts[3]), "why": None, "judge": None,
                           "guideline_version": guideline_version, "ts": None, "line": n})
    return {"format": fmt, "labels": labels}


def load_runs(paths):
    """TREC run files or JSONL rankings. Returns {name: {"ranking": {qid: [(doc, score)]}, "ts": iso or None}}."""
    runs = {}
    for p in map(Path, paths or []):
        name = p.stem
        if name in runs or name in ("keyword", "dense"):
            raise ValueError(f"run name {name!r} is used twice (rename the file)")
        rows, ts = collections.defaultdict(list), []
        if _is_jsonl(p):
            for n, r in enumerate(_jsonl(p), 1):
                if r.get("ts"):
                    ts.append(str(r["ts"]))
                if "docs" in r:
                    for i, d in enumerate(r["docs"], 1):
                        rows[str(r["qid"])].append((i, str(d), None))
                else:
                    rows[str(r["qid"])].append((int(r["rank"]), str(r["doc"]), r.get("score")))
        else:
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                parts = line.split()
                if not parts:
                    continue
                if len(parts) != 6:
                    raise ValueError(f"{p}, line {n}: TREC runs need 6 columns 'qid Q0 doc rank score tag'")
                rows[parts[0]].append((int(parts[3]), parts[2], float(parts[4])))
        when = min(ts) if ts else dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")
        runs[name] = {"ranking": {q: [(d, s) for _, d, s in sorted(v, key=lambda x: x[0])] for q, v in rows.items()},
                      "ts": when, "ts_source": "ts field" if ts else "file time", "builtin": False}
    return runs


# ---------------------------------------------------------------------------------------------------------------- spans
def spans_to_labels(items, docs, chunks):
    """06 evidence_groups -> chunk labels with any_overlap on document offsets. Returns labels per question + details."""
    by_doc = collections.defaultdict(list)
    for i, c in enumerate(chunks):
        by_doc[c["doc"]].append(i)
    ids = {d["id"]: n for n, d in enumerate(docs)}
    labels, details, problems = {}, [], []
    for it in items:
        qid = str(it["qid"])
        grades, reasons = {}, {}
        for g in it.get("evidence_groups") or []:
            for alt in g.get("alternatives") or []:
                hit = set()
                for seg in alt.get("segments") or []:
                    di = ids.get(seg.get("doc_id"))
                    if di is None and len(docs) == 1:
                        di = 0
                    if di is None:
                        problems.append(f"{qid} {g.get('group_id')}/{alt.get('alt_id')}: doc_id {seg.get('doc_id')!r} is not a loaded document")
                        continue
                    d = docs[di]
                    p = int(seg["page"])
                    if not 1 <= p <= len(d["pages"]) or not 0 <= seg["char_start"] < seg["char_end"] <= len(d["pages"][p - 1]):
                        problems.append(f"{qid} {g.get('group_id')}/{alt.get('alt_id')}: page {p} [{seg['char_start']}, {seg['char_end']}) is outside the page text")
                        continue
                    a = d["page_starts"][p - 1] + seg["char_start"]
                    b = d["page_starts"][p - 1] + seg["char_end"]
                    for ci in by_doc[di]:
                        x, y = chunks[ci]["start"], chunks[ci]["end"]
                        if any(not ch.isspace() for ch in d["text"][max(x, a):min(y, b)]):
                            hit.add(ci)
                quote, segs = alt.get("quote"), alt.get("segments") or []
                if quote and segs and all(_seg_ok(s_, docs, ids) for s_ in segs):
                    d = docs[ids.get(segs[0].get("doc_id"), 0)]
                    txt = "".join(d["pages"][s_["page"] - 1][s_["char_start"]:s_["char_end"]] for s_ in segs)
                    if not norm_ws(txt).startswith(norm_ws(quote)):
                        problems.append(f"{qid} {g.get('group_id')}/{alt.get('alt_id')}: the quote does not match the text at its offsets (another parser or snapshot?)")
                grade = int(alt.get("grade", 1))
                for ci in hit:
                    cid = chunks[ci]["id"]
                    grades[cid] = max(grades.get(cid, 0), grade)
                    reasons.setdefault(cid, g.get("fact"))
                details.append({"qid": qid, "group": g.get("group_id"), "alt": alt.get("alt_id"),
                                "page": segs[0]["page"] if segs else None,
                                "chunks": [chunks[ci]["id"] for ci in sorted(hit)]})
        labels[qid] = {c["id"]: {"grade": grades.get(c["id"], 0), "why": reasons.get(c["id"]),
                                 "guideline_version": it.get("guideline_version"), "ts": it.get("ts") or it.get("created_at")}
                       for c in chunks}
    return labels, details, problems


def _seg_ok(seg, docs, ids):
    di = ids.get(seg.get("doc_id"), 0 if len(docs) == 1 else None)
    if di is None:
        return False
    pages = docs[di]["pages"]
    return 1 <= int(seg["page"]) <= len(pages) and 0 <= seg["char_start"] < seg["char_end"] <= len(pages[int(seg["page"]) - 1])


# ---------------------------------------------------------------------------------------------------------------- index and runs
class InvertedIndex:
    def __init__(self, chunks):
        self.tokens = [tokenize(c["text"]) for c in chunks]
        self.postings = {}
        for i, toks in enumerate(self.tokens):
            for t in sorted(set(toks)):
                self.postings.setdefault(t, []).append(i)
        self.N = len(chunks)

    def df(self, t):
        return len(self.postings.get(t, []))

    def stats(self):
        dfs = {t: len(p) for t, p in self.postings.items()}
        top = sorted(dfs.items(), key=lambda x: (-x[1], x[0]))[:10]
        return {"vocab": len(dfs), "postings": sum(dfs.values()), "tokens": sum(map(len, self.tokens)),
                "df1": sum(1 for n in dfs.values() if n == 1), "top": top}

    def equals_scan(self):
        """Every term's postings equal a full scan of the chunks (no chunk missed, none extra)."""
        sets = [set(t) for t in self.tokens]
        return all(p == [i for i in range(self.N) if t in sets[i]] for t, p in self.postings.items())

    def query(self, text):
        toks = list(dict.fromkeys(tokenize(text)))
        known = [t for t in toks if t in self.postings]
        acc = collections.Counter()
        for t in known:
            for i in self.postings[t]:
                acc[i] += 1
        and_set = set.intersection(*(set(self.postings[t]) for t in toks)) if toks and len(known) == len(toks) else set()
        return {"tokens": tokenize(text), "distinct": toks, "unknown": [t for t in toks if t not in self.postings],
                "or": len(acc), "and": len(and_set), "postings_read": sum(self.df(t) for t in known),
                "ranking": sorted(acc.items(), key=lambda x: (-x[1], x[0]))}


_MODELS = {}


def load_dense(model_name):
    if model_name in _MODELS:
        return _MODELS[model_name]
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    try:
        import transformers
        transformers.utils.logging.disable_progress_bar()
    except Exception:  # noqa: BLE001
        pass
    from sentence_transformers import SentenceTransformer
    _MODELS[model_name] = SentenceTransformer(model_name, device="cpu")
    return _MODELS[model_name]


def embed(model, texts):
    return model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)


# ---------------------------------------------------------------------------------------------------------------- metrics
def precision(top, rel):
    """Set precision of a returned list: relevant / returned (0.0 for an empty list), as P2 S8."""
    return 0.0 if not top else sum(1 for d in top if d in rel) / len(top)


def recall(top, rel):
    return NAN if not rel else sum(1 for d in top if d in rel) / len(rel)


def first_relevant_rank(ranking, rel):
    return next((i for i, d in enumerate(ranking, 1) if d in rel), None)


def cohen_kappa(a, b):
    """Cohen's kappa for two binary label lists (separate marginals, as scikit-learn's cohen_kappa_score)."""
    n = len(a)
    if not n:
        return NAN, NAN
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return po, (NAN if pe == 1 else (po - pe) / (1 - pe))


def _mean(xs):
    xs = [x for x in xs if not (isinstance(x, float) and math.isnan(x))]
    return float(np.mean(xs)) if xs else NAN


def _parse_ts(s):
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _version(p):
    try:
        return md.version(p)
    except md.PackageNotFoundError:
        return "not installed"


# ---------------------------------------------------------------------------------------------------------------- the check
def run_check(docs=None, chunks=None, questions=None, qrels=None, spans=None, runs=None, dense=False, relabel=None,
              k=4, chunk_size=1000, overlap=200, doc_ids=None, min_grade=1, unlisted="unjudged", pool_from=None,
              hole_limit=0.10, guideline_version=None, dense_model=MINILM):
    """docs: file/folder paths (or loaded documents); chunks: a chunks.jsonl path (instead of docs). Returns a result."""
    if k < 1:
        raise ValueError("k must be at least 1")
    if (docs is None) == (chunks is None):
        raise ValueError("give --docs or --chunks (one of them)")
    if (qrels is None) == (spans is None):
        raise ValueError("give --qrels or --spans (one of them)")
    if unlisted not in ("unjudged", "zero"):
        raise ValueError("unlisted must be 'unjudged' or 'zero'")
    if docs is not None:
        docs = docs if (docs and isinstance(docs[0], dict)) else load_documents(docs, doc_ids)
        chunk_list = make_windows(docs, chunk_size, overlap)
        chunk_src = "windows"
    else:
        if spans is not None:
            raise ValueError("--spans needs --docs (spans are document offsets)")
        docs, chunk_list, chunk_src = [], load_chunks(chunks), "your chunks"
    cpos = {c["id"]: i for i, c in enumerate(chunk_list)}
    # ---- labels and questions
    span_items, span_details, span_problems = None, [], []
    if spans is not None:
        span_items = _jsonl(spans) if isinstance(spans, (str, Path)) else list(spans)
        given, span_details, span_problems = spans_to_labels(span_items, docs, chunk_list)
        label_format = "spans"
        raw_labels = []
        qs = load_questions(questions) if questions else load_questions(span_items)
        span_by_q = {str(it["qid"]): it for it in span_items}
        for q in qs:
            it = span_by_q.get(q["id"], {})
            q["answerable"] = it.get("answerable", q["answerable"]) if q["answerable"] is None else q["answerable"]
            q["created_by"] = q["created_by"] or it.get("created_by")
            q["notes"] = q["notes"] or it.get("notes")
        complete = True
    else:
        if questions is None:
            raise ValueError("--qrels needs --questions (the question texts)")
        qs = load_questions(questions)
        loaded = load_qrels(qrels, guideline_version) if isinstance(qrels, (str, Path)) else {"format": "JSONL", "labels": list(qrels)}
        label_format, raw_labels = loaded["format"], loaded["labels"]
        given = collections.defaultdict(dict)
        for lab in raw_labels:
            given[lab["qid"]][lab["doc"]] = lab
        complete = unlisted == "zero"
    qids = [q["id"] for q in qs]
    # ---- problems in the labels
    dup = collections.defaultdict(set)
    for lab in raw_labels:
        dup[(lab["qid"], lab["doc"])].add(lab["grade"])
    conflicts = sorted(f"{q} {d}" for (q, d), g in dup.items() if len(g) > 1)
    unknown_q = sorted({lab["qid"] for lab in raw_labels if lab["qid"] not in set(qids)})
    unknown_d = sorted({f"{lab['qid']} {lab['doc']}" for lab in raw_labels if lab["doc"] not in cpos}, key=lambda s: s)

    def full_grade(q, cid):
        """The given labels; None = unjudged."""
        lab = given.get(q, {}).get(cid)
        if lab is not None:
            return lab["grade"]
        return 0 if complete else None

    # ---- index and runs
    idx = InvertedIndex(chunk_list)
    qinfo = {q["id"]: idx.query(q["q"]) for q in qs}
    all_runs = {"keyword": {"ranking": {q: [(chunk_list[i]["id"], s) for i, s in qinfo[q]["ranking"]] for q in qids},
                            "ts": None, "builtin": True,
                            "desc": "keyword overlap from the inverted index (distinct question tokens matched; ties: earlier chunk first)"}}
    dense_error = None
    if dense:
        try:
            model = load_dense(dense_model)
            V = embed(model, [c["text"] for c in chunk_list])
            Q = embed(model, [q["q"] for q in qs])
            S = Q @ V.T
            all_runs["dense"] = {"ranking": {q: [(chunk_list[j]["id"], float(S[i, j]))
                                                 for j in sorted(range(len(chunk_list)), key=lambda j: (-S[i, j], j))]
                                             for i, q in enumerate(qids)},
                                 "ts": None, "builtin": True, "desc": f"dense `{dense_model}` cosine over every chunk (ties: earlier chunk first)"}
        except Exception as e:  # noqa: BLE001
            dense_error = f"{type(e).__name__}: {str(e)[:200]}"
    for name, r in load_runs(runs).items():
        r["desc"] = f"your run `{name}` ({r['ts_source']} {r['ts']})"
        all_runs[name] = r
    # ---- labels in use (pool simulation or the given labels)
    pool_spec = []
    if pool_from:
        for part in str(pool_from).split(","):
            name, _, depth = part.strip().partition(":")
            if name not in all_runs or not depth.isdigit() or int(depth) < 1:
                raise ValueError(f"--pool-from {part!r}: use run:depth with a run in {', '.join(all_runs)}")
            pool_spec.append((name, int(depth)))
        pool = {q: {d for name, dep in pool_spec for d, _ in all_runs[name]["ranking"].get(q, [])[:dep]} for q in qids}

        def grade(q, cid):
            return (full_grade(q, cid) or 0) if cid in pool[q] else None
    else:
        pool = None
        grade = full_grade

    def rel_set(q, g=grade):
        if complete or pool is not None or label_format == "spans":
            cands = [c["id"] for c in chunk_list]
        else:
            cands = list(given.get(q, {}))
        return {c for c in cands if (g(q, c) or 0) >= min_grade}

    REL = {q: rel_set(q) for q in qids}
    REL_FULL = {q: rel_set(q, lambda q_, c_: (full_grade(q_, c_) or 0)) for q in qids}
    answerable = [q["id"] for q in qs if q["answerable"] is not False]
    # ---- per run, per question
    per = {}
    for name, r in all_runs.items():
        rows = {}
        for q in qids:
            ranking = r["ranking"].get(q, [])
            top = [d for d, _ in ranking[:k]]
            judged = [d for d in top if grade(q, d) is not None]
            holes = [d for d in top if grade(q, d) is None]
            rows[q] = {"top": top, "scores": [s for _, s in ranking[:k]], "judged": len(judged), "holes": holes,
                       "empty": k - len(top), "p": precision(top, REL[q]),
                       "p_upper": 0.0 if not top else (sum(1 for d in top if d in REL[q]) + len(holes)) / len(top),
                       "r": recall(top, REL[q]), "p_full": precision(top, REL_FULL[q]), "r_full": recall(top, REL_FULL[q]),
                       "first": first_relevant_rank(top, REL[q]), "tie": tie_at_cut(ranking, k, REL[q])}
        depth = 0
        while depth < k and all(len(r["ranking"].get(q, [])) <= depth or grade(q, r["ranking"][q][depth][0]) is not None for q in qids):
            depth += 1
        ans = [rows[q] for q in answerable]
        per[name] = {"rows": rows, "depth": depth, "desc": r["desc"],
                     "judged_k": _mean([x["judged"] / k for x in rows.values()]),
                     "hole_k": _mean([len(x["holes"]) / k for x in rows.values()]),
                     "empty_k": _mean([x["empty"] / k for x in rows.values()]),
                     "p": _mean([x["p"] for x in ans]), "p_upper": _mean([x["p_upper"] for x in ans]),
                     "r": _mean([x["r"] for x in ans]), "p_full": _mean([x["p_full"] for x in ans]),
                     "r_full": _mean([x["r_full"] for x in ans]),
                     "n_r": sum(1 for x in ans if not math.isnan(x["r"])), "n_r_full": sum(1 for x in ans if not math.isnan(x["r_full"]))}
    hole_list = sorted({(q, d) for name in per for q in qids for d in per[name]["rows"][q]["holes"]},
                       key=lambda x: (qids.index(x[0]), cpos.get(x[1], 10 ** 9), x[1]))
    hole_runs = {h: sorted(n for n in per if h[1] in per[n]["rows"][h[0]]["holes"]) for h in hole_list}
    # ---- spans: zero-labelled chunks every run puts in its top k (missed evidence?)
    shared_zero = []
    if (complete or label_format == "spans") and len(per) >= 2 and pool is None:
        for q in qids:
            common = set.intersection(*(set(per[n]["rows"][q]["top"]) for n in per)) - REL[q]
            shared_zero += [(q, d) for d in sorted(common, key=lambda d: cpos.get(d, 0))]
    # ---- relabel
    agree = None
    if relabel is not None:
        if _is_jsonl(relabel) and any("evidence_groups" in r for r in _jsonl(relabel)):
            if spans is None:
                raise ValueError("a span relabel file needs --spans labels to compare with")
            other, _, _ = spans_to_labels(_jsonl(relabel), docs, chunk_list)
            pairs = [(q, c["id"]) for q in other if q in set(qids) for c in chunk_list]
            second = {(q, c): other[q][c]["grade"] for q, c in pairs}
        else:
            lab2 = load_qrels(relabel)["labels"]
            second = {(x["qid"], x["doc"]): x["grade"] for x in lab2}
            pairs = sorted(second, key=lambda x: (qids.index(x[0]) if x[0] in qids else 10 ** 6, cpos.get(x[1], 10 ** 9), x[1]))
        both = [(q, c) for q, c in pairs if full_grade(q, c) is not None]
        a = [int(full_grade(q, c) >= min_grade) for q, c in both]
        b = [int(second[(q, c)] >= min_grade) for q, c in both]
        po, kappa = cohen_kappa(a, b)
        qtype = {q["id"]: q["type"] or "untyped" for q in qs}
        dis = [(q, c, x, y) for (q, c), x, y in zip(both, a, b) if x != y]
        agree = {"n": len(both), "n_q": len({q for q, _ in both}), "agreement": po, "kappa": kappa, "disagree": dis,
                 "by_type": dict(collections.Counter(qtype.get(q, "untyped") for q, *_ in dis))}
    res = {"settings": {"k": k, "chunk_size": chunk_size if docs else None, "overlap": overlap if docs else None,
                        "chunk_src": chunk_src, "min_grade": min_grade, "unlisted": unlisted, "hole_limit": hole_limit,
                        "pool_from": pool_spec, "dense": dense, "dense_model": dense_model if dense else None,
                        "guideline_version_flag": guideline_version,
                        "versions": {p: _version(p) for p in ("pymupdf", "numpy", "sentence-transformers")}},
           "documents": [{"id": d["id"], "name": d["name"], "pages": len(d["pages"]), "chars": len(d["text"])} for d in docs],
           "chunks": chunk_list, "index": dict(idx.stats(), N=idx.N, scan_ok=idx.equals_scan()),
           "questions": qs, "qinfo": qinfo, "label_format": label_format, "raw_labels": raw_labels, "complete": complete,
           "given": given, "span_items": span_items or [], "span_details": span_details, "span_problems": span_problems,
           "conflicts": conflicts, "unknown_q": unknown_q, "unknown_d": unknown_d,
           "REL": REL, "REL_FULL": REL_FULL, "answerable": answerable, "runs": per, "run_ts": {n: r.get("ts") for n, r in all_runs.items() if not r["builtin"]},
           "holes": hole_list, "hole_runs": hole_runs, "shared_zero": shared_zero, "pooled": pool is not None,
           "dense_error": dense_error, "agree": agree}
    res["full_grade"] = full_grade
    res["sample"] = sample_relevant(res)
    res["checklist"] = checklist(res)
    res["recommendation"] = recommend(res)
    res["trec"] = export_trec(res)
    return res


def tie_at_cut(ranking, k, rel):
    """A tie that straddles the cut: the score at rank k equals the score at rank k + 1. Returns None or a dict."""
    if len(ranking) <= k or ranking[k - 1][1] is None or ranking[k][1] is None:
        return None
    s = ranking[k - 1][1]
    if abs(ranking[k][1] - s) > 1e-12:
        return None
    group = [d for d, x in ranking if x is not None and abs(x - s) <= 1e-12]
    inside = [d for d in group if d in {d2 for d2, _ in ranking[:k]}]
    n_rel = sum(1 for d in group if d in rel)
    return {"score": s, "inside": inside, "outside": [d for d in group if d not in inside], "size": len(group),
            "changes": 0 < n_rel < len(group)}


def sample_relevant(res, n=5):
    """5 relevant pairs in a fixed pseudo-random order (sha256 of 'qid|chunk'), for Q12."""
    pairs = [(q, d) for q in res["REL_FULL"] for d in res["REL_FULL"][q]]
    pairs.sort(key=lambda x: hashlib.sha256(f"{x[0]}|{x[1]}".encode()).hexdigest())
    return pairs[:n]


def export_trec(res):
    """Normalised TREC qrels: 'qid 0 chunk grade', one line per judged pair (the given labels, not the pool)."""
    lines, cpos = [], {c["id"]: i for i, c in enumerate(res["chunks"])}
    for q in res["questions"]:
        if res["label_format"] == "spans" or res["complete"]:
            docs = [c["id"] for c in res["chunks"]]
        else:
            docs = sorted(res["given"].get(q["id"], {}), key=lambda d: (cpos.get(d, 10 ** 9), d))
        for d in docs:
            g = res["full_grade"](q["id"], d)
            if g is not None:
                lines.append(f"{q['id']} 0 {d} {g}")
    return "\n".join(lines) + ("\n" if lines else "")


# ---------------------------------------------------------------------------------------------------------------- 6 checklist
HOW = {
    "Q1": "Give every question at least one label; mark a question with no relevant chunk \"answerable\": false, so "
          "'no answer' is a decision, not a gap. Every label must point at an existing chunk, once.",
    "Q2": "Write `why` in your own words (more than 3 words): what in the chunk meets the need, or why a look-alike "
          "does not. With spans, the group's `fact` is the reason; an unanswerable item needs a `notes` line.",
    "Q3": "Put `guideline_version` on every label (or --guideline-version for a TREC file); bump it whenever a "
          "guideline sentence changes.",
    "Q4": "Record `ts` when you label and keep each run file's time; label from the need and the chunks, before you "
          "open any ranked list.",
    "Q5": "Pool the top k (10 is common) of both the keyword run and the dense run, judge the union, rerun. "
          "--pool-from keyword:3 shows what a one-retriever pool hides.",
    "Q6": "Hole@k = unjudged chunks in a run's top k ÷ k. Judge the holes listed in section 4, then rerun.",
    "Q7": "Compute each run's P@k twice: holes as not relevant (lower bound) and holes as relevant (upper bound). "
          "If two runs swap order, the unjudged chunks decide the winner.",
    "Q8": "Compare the score at rank k with the score at rank k + 1. State the tie rule, and say whether another "
          "order would change P@k.",
    "Q9": "Look up each question token's postings: no postings at all = vocabulary mismatch (keyword search can "
          "never find it); an OR set over half the chunks = common words dominate.",
    "Q10": "After 7 days or more, re-label at least 10 items with the old labels hidden (--relabel); raw agreement "
           "≥ 0.90 (06 §6.5) and κ ≥ 0.67.",
    "Q11": "Label evidence spans (06 evidence_groups) and let the tool derive chunk labels with any_overlap; "
           "chunk-id labels are void as soon as you re-chunk.",
    "Q12": "Re-read the 5 pairs listed in section 3: does the chunk help answer the need, or does it only share "
           "words? Then check one ambiguous question in full.",
}


def _f(x, d=3):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def _pct(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}%"


def _short(xs, n=8):
    xs = list(xs)
    return ", ".join(xs[:n]) + (f" … (+{len(xs) - n})" if len(xs) > n else "")


def checklist(res):
    s, qs, fmt, per = res["settings"], res["questions"], res["label_format"], res["runs"]
    k, qids = s["k"], [q["id"] for q in res["questions"]]
    items = []

    def add(cid, text, verdict, evidence):
        items.append({"id": cid, "check": text, "verdict": verdict, "evidence": evidence, "how": HOW[cid]})

    # Q1
    unlabelled = [q for q in qids if fmt != "spans" and not res["complete"] and not res["given"].get(q)]
    implicit = [q["id"] for q in qs if not res["REL_FULL"][q["id"]] and q["answerable"] is not False and q["id"] not in unlabelled]
    contra = [q["id"] for q in qs if res["REL_FULL"][q["id"]] and q["answerable"] is False]
    bad = []
    if unlabelled:
        bad.append(f"no label at all: {_short(unlabelled)}")
    if implicit:
        bad.append(f"no relevant chunk but not marked \"answerable\": false: {_short(implicit)}")
    if contra:
        bad.append(f"marked unanswerable but has relevant chunks: {_short(contra)}")
    if res["unknown_q"]:
        bad.append(f"labels for questions not in the question file: {_short(res['unknown_q'])}")
    if res["unknown_d"]:
        bad.append(f"labels for chunk ids that do not exist: {_short(res['unknown_d'])}")
    if res["conflicts"]:
        bad.append(f"the same pair labelled twice with different grades: {_short(res['conflicts'])}")
    n_un = sum(1 for q in qs if q["answerable"] is False)
    add("Q1", "Every question has at least one label, and answerable vs unanswerable is explicit", BAD if bad else OK,
        "; ".join(bad) + "." if bad else
        f"{len(qs)} questions: {len(qs) - n_un} with at least one relevant chunk, {n_un} marked \"answerable\": false.")
    # Q2
    if fmt == "spans":
        nofact = [str(it["qid"]) for it in res["span_items"]
                  if any(len(str(g.get("fact") or "").split()) <= 3 for g in it.get("evidence_groups") or [])]
        nonote = [q["id"] for q in qs if q["answerable"] is False and len(str(q["notes"] or "").split()) <= 3]
        bad = ([f"an evidence group with no `fact` of more than 3 words: {_short(nofact)}"] if nofact else []) + \
              ([f"unanswerable with no note: {_short(nonote)}"] if nonote else [])
        add("Q2", "Every non-zero label (and each tempting zero) has a reason of more than 3 words", BAD if bad else OK,
            "; ".join(bad) + "." if bad else
            "every evidence group has a `fact` (the reason each derived label carries), and every unanswerable item a note.")
    elif fmt == "TREC":
        add("Q2", "Every non-zero label (and each tempting zero) has a reason of more than 3 words", BAD,
            f"TREC qrels carry no reasons ({len(res['raw_labels'])} labels). Keep a JSONL file with `why` as your master copy.")
    else:
        miss = [lab for lab in res["raw_labels"] if not lab["why"] or len(str(lab["why"]).split()) <= 3]
        nz = sum(1 for lab in miss if lab["grade"] >= 1)
        add("Q2", "Every non-zero label (and each tempting zero) has a reason of more than 3 words", BAD if miss else OK,
            (f"{len(miss)} of {len(res['raw_labels'])} listed labels have no reason or 3 words or fewer ({nz} of them non-zero): "
             + _short([f"{x['qid']} {x['doc']}" for x in miss]) + ".") if miss else
            f"all {len(res['raw_labels'])} listed labels (non-zero and listed zeros) have a reason of more than 3 words.")
    # Q3
    if fmt == "spans":
        vers = [it.get("guideline_version") or s["guideline_version_flag"] for it in res["span_items"]]
        unit = "span items"
    else:
        vers = [lab["guideline_version"] for lab in res["raw_labels"]]
        unit = "labels"
    missing = sum(1 for v in vers if not v)
    found = sorted({str(v) for v in vers if v})
    add("Q3", "The guideline version is recorded on every label", BAD if (missing or not vers) else OK,
        (f"{missing} of {len(vers)} {unit} have no guideline version"
         + (" (the 06 span form has no per-item `guideline_version`; add one, or pass --guideline-version)" if fmt == "spans" else "")
         + (f"; versions seen: {', '.join(found)}" if found else "") + ".") if (missing or not vers) else
        f"every label has one: {', '.join(found)}" + (" (from --guideline-version)" if s["guideline_version_flag"] and found == [s["guideline_version_flag"]] else "") + ".")
    # Q4
    lts = [lab["ts"] for lab in res["raw_labels"]] if fmt != "spans" else \
          [lab["ts"] for labs in res["given"].values() for lab in list(labs.values())[:1]]
    parsed = [_parse_ts(t) for t in lts if t]
    ext = {n: _parse_ts(t) for n, t in res["run_ts"].items() if t}
    if not parsed or len(parsed) < len(lts):
        add("Q4", "Labels were written before any run was seen", ASK,
            ("no label timestamps" if not parsed else f"{len(lts) - len(parsed)} of {len(lts)} labels have no usable timestamp")
            + ". Check by hand: did you label before looking at any ranked list? (This tool's own runs are built when the report is made.)")
    elif not ext:
        add("Q4", "Labels were written before any run was seen", ASK,
            f"labels dated {min(parsed).isoformat()} to {max(parsed).isoformat()}; no run files given (--runs) to compare with. "
            "Check by hand that you labelled before looking at any ranked list.")
    else:
        late = {n: sum(1 for t in parsed if t >= rt) for n, rt in ext.items()}
        badr = {n: v for n, v in late.items() if v}
        add("Q4", "Labels were written before any run was seen", BAD if badr else OK,
            "; ".join(f"{v} label(s) dated at or after run `{n}` ({res['run_ts'][n]})" for n, v in badr.items()) + "."
            if badr else f"every label ({len(parsed)}) is dated before every run file ({', '.join(f'{n} {t}' for n, t in res['run_ts'].items())}).")
    # Q5
    depths = {n: per[n]["depth"] for n in per}
    contrib = [n for n, d in depths.items() if d >= 1]
    dtxt = ", ".join(f"`{n}` {d}" for n, d in depths.items())
    if len(per) < 2:
        add("Q5", "The pool covers more than one retriever (keyword and dense)", ASK,
            f"only one run (`{next(iter(per))}`); run with --dense (or --runs) to see whether a second retriever's top results were judged."
            + (f" Dense failed: {res['dense_error']}" if res["dense_error"] else ""))
    elif len(contrib) < 2:
        add("Q5", "The pool covers more than one retriever (keyword and dense)", BAD,
            f"pool depth (every question's top d judged): {dtxt}. Only {_short(['`' + c + '`' for c in contrib]) or 'no run'} reached the pool"
            + (f" (simulated: --pool-from {', '.join(f'{n}:{d}' for n, d in s['pool_from'])})" if s["pool_from"] else "") + ".")
    else:
        add("Q5", "The pool covers more than one retriever (keyword and dense)", OK,
            f"pool depth (every question's top d judged): {dtxt}."
            + (" Span labels judge every chunk (no overlap = 0), which holds only if your spans list every place that answers; "
               "section 4 lists zero-labelled chunks that every run ranks in its top k." if res["label_format"] == "spans" else ""))
    # Q6
    over = {n: per[n]["hole_k"] for n in per if per[n]["hole_k"] > s["hole_limit"] + 1e-12}
    htxt = ", ".join(f"`{n}` {_pct(per[n]['hole_k'])}" for n in per)
    add("Q6", f"Hole@k for each run is below the limit ({100 * s['hole_limit']:.0f}%)", BAD if over else OK,
        f"Hole@{k}: {htxt}" + (f"; over the limit: {', '.join('`' + n + '`' for n in over)}. {len(res['holes'])} hole(s) to judge (section 4)." if over else "."))
    # Q7
    names = list(per)
    if len(names) < 2:
        add("Q7", "No two runs swap order when holes count as relevant instead of not relevant", ASK, "needs two runs or more.")
    else:
        flips = []
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                lo = per[a]["p"] - per[b]["p"]
                hi = per[a]["p_upper"] - per[b]["p_upper"]
                if lo * hi < -1e-12:
                    flips.append(f"`{a}` vs `{b}`: P@{k} {_f(per[a]['p'])} vs {_f(per[b]['p'])} with holes as 0, "
                                 f"{_f(per[a]['p_upper'])} vs {_f(per[b]['p_upper'])} with holes as relevant")
        add("Q7", "No two runs swap order when holes count as relevant instead of not relevant", BAD if flips else OK,
            "; ".join(flips) + "." if flips else
            "mean P@{0} (holes as 0 → as relevant): ".format(k) + ", ".join(f"`{n}` {_f(per[n]['p'])} → {_f(per[n]['p_upper'])}" for n in names) + "; no pair swaps.")
    # Q8
    ties = [(n, q, per[n]["rows"][q]["tie"]) for n in per for q in qids if per[n]["rows"][q]["tie"]]
    changing = [(n, q, t) for n, q, t in ties if t["changes"]]
    rule = "ties: the earlier chunk first (document order) for the keyword and dense runs; your own run files keep their file order"
    if not ties:
        add("Q8", "Ties at the cut-off k are reported, and the tie rule is stated", OK, f"no tie straddles rank {k} in any run ({rule}).")
    else:
        ev = (f"{len(ties)} tie(s) straddle rank {k}: " + _short([f"`{n}` {q} ({t['size']} chunks at score {t['score']:g})" for n, q, t in ties], 6)
              + f". {len(changing)} of them mix relevant and not-relevant chunks, so another tie order would change P@{k}"
              + (": " + _short([f"`{n}` {q}" for n, q, _ in changing], 6) if changing else "") + f". Rule: {rule}.")
        add("Q8", "Ties at the cut-off k are reported, and the tie rule is stated", BAD if changing else OK, ev)
    # Q9
    zero = [q for q in qids if not res["qinfo"][q]["or"]]
    zero_ans = [q for q in zero if q in res["answerable"]]
    half = [q for q in qids if res["qinfo"][q]["or"] > res["index"]["N"] / 2]
    parts = []
    if zero:
        parts.append(f"no keyword candidate (no question token has postings): {_short(zero)}"
                     + (f"; answerable among them: {_short(zero_ans)}" if zero_ans else " (all unanswerable)"))
    if half:
        parts.append(f"OR set over half of the {res['index']['N']} chunks: " + _short([f"{q} ({res['qinfo'][q]['or']})" for q in half], 6))
    add("Q9", "Questions with no keyword candidate, and questions whose OR set covers most of the collection, are listed",
        BAD if zero_ans else (ASK if parts else OK),
        ("; ".join(parts) + "." + (" Keyword search can never find the answerable ones." if zero_ans else
                                   " Common words decide those OR sets: rank, do not filter, and check that keyword scores still separate chunks."))
        if parts else "every question has keyword candidates, and no OR set covers more than half of the chunks.")
    # Q10
    ag = res["agree"]
    if ag is None:
        add("Q10", "Self-agreement on a blind re-label of ≥ 10 items: raw agreement and κ", ASK,
            "no --relabel file. After 7 days or more, re-label at least 10 items with the old labels hidden.")
    elif ag["n"] < 10:
        add("Q10", "Self-agreement on a blind re-label of ≥ 10 items: raw agreement and κ", ASK,
            f"only {ag['n']} pair(s) labelled in both passes; need 10 or more.")
    else:
        low = ag["agreement"] < 0.90 or (not math.isnan(ag["kappa"]) and ag["kappa"] < 0.67)
        add("Q10", "Self-agreement on a blind re-label of ≥ 10 items: raw agreement and κ", BAD if low else OK,
            f"{ag['n']} pairs over {ag['n_q']} question(s): raw agreement {ag['agreement']:.3f}, κ {_f(ag['kappa'])}"
            + (" (undefined: one label everywhere)" if math.isnan(ag["kappa"]) else "")
            + f"; {len(ag['disagree'])} disagreement(s)" + (" by type: " + ", ".join(f"{t} {n}" for t, n in sorted(ag["by_type"].items())) if ag["disagree"] else "") + ".")
    # Q11
    if fmt == "spans":
        add("Q11", "Labels are spans or derived from spans, not chunk ids of one chunker", BAD if res["span_problems"] else OK,
            (f"{len(res['span_problems'])} span problem(s): " + "; ".join(res["span_problems"][:4]) + ".") if res["span_problems"] else
            f"span labels, converted with any_overlap to the {len(res['chunks'])} chunks here; re-chunking re-derives them.")
    elif s["chunk_src"] == "windows":
        add("Q11", "Labels are spans or derived from spans, not chunk ids of one chunker", BAD,
            f"{fmt} labels on this tool's window ids ({s['chunk_size']} / overlap {s['overlap']}): they are void if the chunking changes.")
    else:
        add("Q11", "Labels are spans or derived from spans, not chunk ids of one chunker", ASK,
            f"{fmt} labels on your own chunk ids: fine for fixed documents, void if the ids come from a chunker you may change.")
    # Q12
    add("Q12", "A sample of relevant labels is re-read against the need, not the words (one ambiguous question checked)", ASK,
        "manual: re-read " + (_short([f"{q} {d}" for q, d in res["sample"]], 5) if res["sample"] else "(no relevant pairs)") + " (section 3).")
    return items


# ---------------------------------------------------------------------------------------------------------------- 7 recommendation
RULES = [
    (("Q1", "Q2", "Q3", "Q11"), "labels not ready: fix the format and guideline first", None),
    (("Q5", "Q6"), "pool is biased: judge the listed holes (top-k chunks from every run that no one judged), then rerun", "holes"),
    (("Q7",), "your comparison is decided by unjudged chunks: do not report a winner", None),
    (("Q10",), "rewrite the guideline sentence for the disagreeing category; relabel; bump the guideline version", None),
]


def recommend(res):
    c = {i["id"]: i for i in res["checklist"]}
    notes = []
    drafts = [q["id"] for q in res["questions"] if q.get("created_by") == "llm-draft"]
    if drafts:
        notes.append(f"{len(drafts)} of {len(res['questions'])} questions are `created_by: llm-draft` (06 §6.7): not human "
                     "labels; keep them out of scored runs until you verify them.")
    for ids, verdict, extra in RULES:
        failed = [i for i in ids if c[i]["verdict"] == BAD]
        if failed:
            reasons = [f"{i}: {c[i]['evidence']}" for i in failed]
            if extra == "holes":
                reasons.append(f"{len(res['holes'])} hole(s) listed in section 4.")
            return {"verdict": verdict, "rule": ids, "reasons": reasons + notes}
    asks = [i["id"] for i in res["checklist"] if i["verdict"] == ASK]
    reasons = [f"mean Judged@{res['settings']['k']}: " + ", ".join(f"`{n}` {_pct(r['judged_k'])}" for n, r in res["runs"].items()) + "."]
    if asks:
        reasons.append("still to check by hand: " + ", ".join(asks) + " (see the checklist).")
    return {"verdict": "labels are fit for retrieval metrics (P6/M2); report Judged@k next to every number", "rule": None,
            "reasons": reasons + notes}


# ---------------------------------------------------------------------------------------------------------------- report
def _cell(x):
    return str(x).replace("|", "\\|").replace("\n", " ")


def render_report(res):
    s, ix, per, k = res["settings"], res["index"], res["runs"], res["settings"]["k"]
    qids = [q["id"] for q in res["questions"]]
    cpos = {c["id"]: i for i, c in enumerate(res["chunks"])}
    L = []
    w = L.append
    w("# Qrels check")
    w("")
    w("**What this is:** an automatic check of whether your relevance labels (qrels) can measure retrieval on your own chunks: format, reasons, versions, pool coverage, holes, ties.")
    w("**What this is not:** an evaluation of a retriever. The P@k and R@k below only show what the labels can and cannot carry.")
    w("")
    rec = res["recommendation"]
    w(f"**Recommendation: {rec['verdict']}** (section 7). Checklist: " + " ".join(f"{i['id']} {i['verdict']}" for i in res["checklist"]) + ".")
    w("")
    drafts = [q["id"] for q in res["questions"] if q.get("created_by") == "llm-draft"]
    if drafts:
        w(f"> **Draft labels:** {len(drafts)} of {len(res['questions'])} questions are `created_by: llm-draft` (06 §6.7). "
          "This report illustrates the tool; it says nothing about retriever quality.")
        w("")
    src = (f"{s['chunk_size']}-character windows, overlap {s['overlap']} (step {s['chunk_size'] - s['overlap']}), pages joined with \"\\n\""
           if s["chunk_src"] == "windows" else "your chunks (--chunks)")
    w(f"Settings: chunks: {src} · k {k} · relevant = grade ≥ {s['min_grade']} · labels: {res['label_format']}"
      + ("" if res["label_format"] == "spans" else f", unlisted pairs {'= 0 (judged)' if s['unlisted'] == 'zero' else 'unjudged'}")
      + f" · Hole@k limit {100 * s['hole_limit']:.0f}%"
      + (f" · simulated pool: {', '.join(f'{n} top {d}' for n, d in s['pool_from'])}" if s["pool_from"] else "")
      + (f" · dense `{s['dense_model']}`" if s["dense"] else "")
      + f" · pymupdf {s['versions']['pymupdf']}, numpy {s['versions']['numpy']}, sentence-transformers {s['versions']['sentence-transformers']}.")
    if res["documents"]:
        w("Documents: " + "; ".join(f"`{d['name']}` as `{d['id']}` ({d['pages']} page(s), {d['chars']:,} characters)" for d in res["documents"]) + ".")
    w("Runs: " + "; ".join(f"`{n}` = {r['desc']}" for n, r in per.items()) + "."
      + (f" Dense not built: {res['dense_error']}." if res["dense_error"] else ""))
    w("")
    # 1
    w("## 1 Collection and index")
    w("")
    w("Tokens: lowercase runs of `[a-z0-9]` (no stemming, no stop words), the same for chunks and questions.")
    w("")
    w("| Measure | Value |")
    w("|---|---|")
    w(f"| Chunks | {ix['N']:,} |")
    w(f"| Tokens | {ix['tokens']:,} |")
    w(f"| Vocabulary (distinct terms) | {ix['vocab']:,} |")
    w(f"| Postings (term, chunk pairs) | {ix['postings']:,} |")
    w(f"| Terms in exactly one chunk (df = 1) | {ix['df1']:,} |")
    w(f"| Commonest terms (df) | " + ", ".join(f"`{t}` {n}" for t, n in ix["top"]) + " |")
    w(f"| Postings equal a full scan of the chunks | {'yes' if ix['scan_ok'] else '**no**'} |")
    w("")
    # 2
    w("## 2 Questions vs the index")
    w("")
    w("AND = chunks with every question token; OR = chunks with at least one (the keyword run's candidates); postings read = "
      "the sum of the question tokens' df.")
    w("")
    w("| Question | Tokens | No postings | AND | OR | Postings read | Flag |")
    w("|---|---|---|---|---|---|---|")
    for q in res["questions"]:
        qi = res["qinfo"][q["id"]]
        flag = ("**no candidate**" if not qi["or"] else ("OR > half" if qi["or"] > ix["N"] / 2 else "-"))
        w(f"| {q['id']} | {_cell(' '.join(qi['distinct']))} | {_cell(' '.join(qi['unknown'])) or '-'} | {qi['and']} | {qi['or']} | {qi['postings_read']} | {flag} |")
    w("")
    # 3
    w("## 3 Label audit")
    w("")
    fmt = res["label_format"]
    if fmt == "spans":
        w(f"Labels: evidence spans (06 `evidence_groups`), converted to chunk labels with `any_overlap`: a chunk is relevant "
          f"if it overlaps at least one non-whitespace character of a segment (document offsets: page start + char offset). "
          f"Every chunk gets a label (0 = no overlap), so every pair is judged.")
    else:
        w(f"Labels: {fmt} qrels, {len(res['raw_labels'])} listed pair(s); "
          + ("unlisted pairs count as judged 0 (--unlisted zero)." if res["complete"] else "unlisted pairs are unjudged (TREC rule)."))
    w("")
    grades = collections.Counter()
    for q in qids:
        for c in res["chunks"]:
            g = res["full_grade"](q, c["id"])
            if g is not None:
                grades[g] += 1
    for lab in res["raw_labels"]:
        if lab["doc"] not in cpos:
            grades[lab["grade"]] += 1
    w("Judged pairs by grade: " + ", ".join(f"grade {g}: {n:,}" for g, n in sorted(grades.items())) + ".")
    w("")
    w("| Question | Type | Answerable | Relevant chunks (full labels) | Created by | Need / question |")
    w("|---|---|---|---|---|---|")
    for q in res["questions"]:
        relq = sorted(res["REL_FULL"][q["id"]], key=lambda d: cpos.get(d, 10 ** 9))
        ans = {True: "yes", False: "no", None: "not stated"}[q["answerable"] if q["answerable"] in (True, False) else None]
        w(f"| {q['id']} | {q['type'] or '-'} | {ans} | {_cell(_short(relq, 10)) or '-'} | {q.get('created_by') or '-'} | {_cell(q['need'] or q['q'])} |")
    w("")
    if fmt == "spans":
        w("Span → chunk conversion, per evidence group and alternative (groups are AND, alternatives OR):")
        w("")
        w("| Question | Group / alternative | Page | Chunks it overlaps |")
        w("|---|---|---|---|")
        for d in res["span_details"]:
            w(f"| {d['qid']} | {d['group']}/{d['alt']} | {d['page']} | {', '.join(d['chunks']) or '-'} |")
        w("")
        if res["span_problems"]:
            w("Span problems: " + "; ".join(res["span_problems"]) + ".")
            w("")
    probs = []
    if res["unknown_d"]:
        probs.append(f"labels on chunk ids that do not exist: {_short(res['unknown_d'])}")
    if res["unknown_q"]:
        probs.append(f"labels on unknown questions: {_short(res['unknown_q'])}")
    if res["conflicts"]:
        probs.append(f"conflicting duplicates: {_short(res['conflicts'])}")
    if probs:
        w("Problems: " + "; ".join(probs) + ".")
        w("")
    w("Five relevant pairs to re-read against the need (Q12; a fixed pseudo-random order):")
    w("")
    if res["sample"]:
        w("| Question | Chunk | Chunk text (start) |")
        w("|---|---|---|")
        texts = {c["id"]: c["text"] for c in res["chunks"]}
        for q, d in res["sample"]:
            w(f"| {q} | {d} | {_cell(norm_ws(texts.get(d, ''))[:160])} … |")
    else:
        w("(no relevant pairs)")
    w("")
    # 4
    w("## 4 Pool and holes")
    w("")
    if res["pooled"]:
        w(f"**Simulated pool:** only the top {', '.join(f'{d} of `{n}`' for n, d in s['pool_from'])} are judged, with grades taken "
          "from your full labels (unlisted = 0). Every check below uses these pooled labels; the *full* columns use all your labels.")
        w("")
    w(f"Judged@{k} and Hole@{k} are out of {k} slots (empty slots, when a run returns fewer than {k}, are neither). Pool depth = "
      f"the largest d such that every question's top d in the run is judged. P@{k} bounds: holes as not relevant → as relevant.")
    w("")
    head = f"| Run | Judged@{k} | Hole@{k} | Empty | Pool depth | P@{k} (holes 0) | P@{k} (holes relevant) | R@{k} |"
    sep = "|---|---|---|---|---|---|---|---|"
    if res["pooled"]:
        head += f" P@{k} full | R@{k} full |"
        sep += "---|---|"
    w(head)
    w(sep)
    for n, r in per.items():
        line = (f"| `{n}` | {_f(r['judged_k'])} | {_f(r['hole_k'])} | {_f(r['empty_k'])} | {r['depth']} | {_f(r['p'])} | "
                f"{_f(r['p_upper'])} | {_f(r['r'])} (over {r['n_r']}) |")
        if res["pooled"]:
            line += f" {_f(r['p_full'])} | {_f(r['r_full'])} (over {r['n_r_full']}) |"
        w(line)
    w("")
    w(f"Means over the {len(res['answerable'])} answerable question(s); R@{k} only over those with a relevant chunk under the labels in use.")
    w("")
    if res["holes"]:
        w(f"Holes to judge ({len(res['holes'])}: chunks in some run's top {k} that no one judged):")
        w("")
        w("| Question | Chunk | In the top k of |")
        w("|---|---|---|")
        for q, d in res["holes"][:MAX_LIST]:
            w(f"| {q} | {d} | {', '.join('`' + n + '`' for n in res['hole_runs'][(q, d)])} |")
        if len(res["holes"]) > MAX_LIST:
            w(f"| … | {len(res['holes']) - MAX_LIST} more | |")
    else:
        w(f"No holes: every chunk in every run's top {k} is judged.")
    w("")
    if res["shared_zero"]:
        w(f"Zero-labelled chunks that every run puts in its top {k} ({len(res['shared_zero'])}). A missed place that answers "
          "would be a hidden hole, so re-read a few:")
        w("")
        w(", ".join(f"{q} {d}" for q, d in res["shared_zero"][:MAX_LIST]) + (" …" if len(res["shared_zero"]) > MAX_LIST else ""))
        w("")
    ties = [(n, q, per[n]["rows"][q]["tie"]) for n in per for q in qids if per[n]["rows"][q]["tie"]]
    w(f"Ties at the cut-off (the score at rank {k} equals the score at rank {k + 1}); rule: the earlier chunk first.")
    w("")
    if ties:
        w("| Run | Question | Score | Tied chunks | Kept (inside the top k) | Changes P@k under another order |")
        w("|---|---|---|---|---|---|")
        for n, q, t in ties[:MAX_LIST]:
            w(f"| `{n}` | {q} | {t['score']:g} | {t['size']} | {_short(t['inside'], 6)} | {'**yes**' if t['changes'] else 'no'} |")
        if len(ties) > MAX_LIST:
            w(f"| … | {len(ties) - MAX_LIST} more | | | | |")
    else:
        w("None.")
    w("")
    # 5
    w("## 5 Set vs ranking per question")
    w("")
    w(f"Top {k} per run, marked **R** relevant, 0 judged not relevant, ? unjudged (a hole). P@{k} = relevant ÷ returned; "
      f"R@{k} = relevant in the top {k} ÷ all relevant; first relevant rank and RR = 1 ÷ rank within the top {k}.")
    w("")
    w(f"| Question | Run | Top {k} | P@{k} | R@{k} | First relevant rank | RR |")
    w("|---|---|---|---|---|---|---|")
    for q in qids:
        for n, r in per.items():
            row = r["rows"][q]
            marks = []
            for d in row["top"]:
                if d in res["REL"][q]:
                    marks.append(f"{d} **R**")
                elif d in row["holes"]:
                    marks.append(f"{d} ?")
                else:
                    marks.append(f"{d} 0")
            fr = row["first"]
            w(f"| {q} | `{n}` | {', '.join(marks) or '(nothing)'} | {_f(row['p'])} | {_f(row['r'])} | {fr if fr else '-'} | {_f(1 / fr) if fr else '-'} |")
    w("")
    # 6
    w("## 6 Checklist")
    w("")
    w("✓ = no problem found · ✗ = a problem found on your data · ? = check by hand (the evidence and *how to check* help).")
    w("")
    w("| # | Check | Verdict | Evidence | How to check |")
    w("|---|---|---|---|---|")
    for i in res["checklist"]:
        w(f"| {i['id']} | {_cell(i['check'])} | {i['verdict']} | {_cell(i['evidence'])} | {_cell(i['how'])} |")
    w("")
    # 7
    w("## 7 Recommendation")
    w("")
    w(f"**{rec['verdict']}**" + (f" (rule: {' or '.join(rec['rule'])} failed; first match wins)" if rec["rule"] else ""))
    w("")
    for r in rec["reasons"]:
        w(f"- {_cell(r)}")
    w("")
    w("Order of the rules: Q1/Q2/Q3/Q11 label format → Q5/Q6 pool and holes → Q7 bounds → Q10 self-agreement → fit for metrics.")
    w("")
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Are my relevance labels good enough to measure retrieval on my documents? "
                                             "Writes a Markdown report and a normalised TREC qrels file. No API calls.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--docs", nargs="+", help="files or folders (.pdf, .txt, .md), cut into character windows")
    src.add_argument("--chunks", help="chunks.jsonl ({\"id\", \"text\"}) instead of --docs")
    ap.add_argument("--doc-ids", default="", help="comma-separated document ids (default: file stems); chunk ids are '<id>#<j>'")
    ap.add_argument("--questions", help="questions .jsonl ({\"id\", \"q\", \"need\", \"type\", \"answerable\"})")
    lab = ap.add_mutually_exclusive_group(required=True)
    lab.add_argument("--qrels", help="labels: JSONL ({\"qid\", \"doc\", \"grade\", \"why\", \"judge\", \"guideline_version\", \"ts\"}) or TREC 4 columns")
    lab.add_argument("--spans", help="labels as 06 evidence_groups (JSONL), converted with any_overlap")
    ap.add_argument("--runs", nargs="*", help="your run files: TREC 6 columns or JSONL rankings")
    ap.add_argument("--dense", action="store_true", help="add a local MiniLM run (offline)")
    ap.add_argument("--dense-model", default=MINILM)
    ap.add_argument("--relabel", help="a second, blind labelling pass (same formats as --qrels / --spans)")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--min-grade", type=int, default=1, help="relevant = grade >= this (default 1)")
    ap.add_argument("--unlisted", choices=("unjudged", "zero"), default="unjudged", help="what an unlisted pair means")
    ap.add_argument("--pool-from", help="simulate a pool, e.g. keyword:3 or keyword:3,dense:3")
    ap.add_argument("--hole-limit", type=float, default=0.10, help="Q6 limit for Hole@k (default 0.10)")
    ap.add_argument("--guideline-version", help="the guideline version for labels that do not carry one")
    ap.add_argument("--report", help="write the Markdown report here (default: print it)")
    ap.add_argument("--trec-out", help="write the normalised TREC qrels here")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    res = run_check(docs=a.docs, chunks=a.chunks, questions=a.questions, qrels=a.qrels, spans=a.spans, runs=a.runs,
                    dense=a.dense, relabel=a.relabel, k=a.k, chunk_size=a.chunk_size, overlap=a.overlap,
                    doc_ids=[x.strip() for x in a.doc_ids.split(",") if x.strip()] or None, min_grade=a.min_grade,
                    unlisted=a.unlisted, pool_from=a.pool_from, hole_limit=a.hole_limit,
                    guideline_version=a.guideline_version, dense_model=a.dense_model)
    text = render_report(res)
    if a.trec_out:
        Path(a.trec_out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.trec_out).write_text(res["trec"], encoding="utf-8", newline="\n")
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8", newline="\n")
        print(f"chunks {res['index']['N']}, vocabulary {res['index']['vocab']:,}, postings {res['index']['postings']:,}")
        for i in res["checklist"]:
            print(f"{i['id']:4s} {i['verdict']}  {i['check']}")
        print(f"recommendation: {res['recommendation']['verdict']}")
        print(f"report: {a.report}" + (f" · qrels: {a.trec_out}" if a.trec_out else ""))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
