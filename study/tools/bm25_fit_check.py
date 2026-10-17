"""bm25_fit_check: does BM25 keyword search suit MY documents and questions?

What this is: a command-line tool (also importable) that chunks your documents, builds a BM25 index exactly as the P3
lesson does (rank_bm25 0.2.2 BM25Okapi, k1 1.5, b 0.75, epsilon 0.25), runs your questions, and writes a Markdown report:
  1 Collection        chunks, avgdl, vocabulary, mean idf, the idf floor, the "valley", overlap doubling
  2 Tokenizer audit   identifier-like strings in your documents and what each tokenizer does to them
  3 Per question      tokens, unknown tokens, the rarest token, the top-k, zero-score and "vague" warnings
  4 Measuring         (questions with "expect") rank of the right chunk, Hit@1 / Hit@k / MRR per type,
                      for all three tokenizers, and dense (MiniLM) side by side with --dense
  5 Checklist         C1-C12 with a verdict (✓ fine, ✗ problem found, ? check by hand) and the evidence
  6 Recommendation    BM25 alone / hybrid / fix the tokenizer first / not enough data
What this is not: an evaluation. A handful of labelled questions shows the mechanism, not which retriever is better.

Chunking: each document's pages are joined with "\n" (PyMuPDF page.get_text() for PDFs), then cut into plain character
windows of --chunk-size with --overlap, as P3's "91 windows". Chunk "#83" is window 83 (page = the page where it starts).
Tokenizers: norm = P3's tok_norm (lower-case runs of letters/digits, keeps 1.5 whole); split = Python's str.split()
(the repo's tokenizer); code = the lesson playground's tokCode: split at "_" and at case changes AND keep the whole
name; dotted numbers such as 1.5 and v2.10.3 stay whole.

No API calls. Standard library + numpy + rank_bm25 + pymupdf; sentence-transformers only with --dense (MiniLM loads
from the Hugging Face cache; set HF_HUB_OFFLINE=1 to forbid downloads).

Usage, from rag_learning/:
    uv run python study/tools/bm25_fit_check.py --docs my_docs/ --questions my_questions.jsonl --report report.md
    uv run python study/tools/bm25_fit_check.py --docs a.pdf b.md --questions q.txt --tokenizer code --identifiers getUserId,ERR_X --dense
Questions: .txt (one question per line; blank lines and lines starting with # are skipped) or .jsonl with
    {"q": "...", "expect": "text the right chunk contains" (optional), "type": "exact-term|paraphrase|other" (optional),
     "id": "..." (optional)}
"expect" is matched case-insensitively with whitespace normalised; keep it shorter than --overlap so it cannot be cut
across two chunks.

Import:
    from bm25_fit_check import run_check, render_report
    result = run_check(["doc.pdf"], "questions.jsonl", tokenizer="norm", k=4)
    print(render_report(result))
"""
from __future__ import annotations

import argparse
import bisect
import collections
import importlib.metadata as md
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_K1, DEFAULT_B, DEFAULT_EPSILON = 1.5, 0.75, 0.25
TYPES = ("exact-term", "paraphrase", "other")
EXTS = (".pdf", ".txt", ".md")
OK, BAD, ASK = "✓", "✗", "?"

# ---------------------------------------------------------------------------------------------------------------- tokenizers
NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def tok_norm(text):
    """P3's tok_norm: lower-case, runs of letters and digits; keeps 1.5 and 650,000 whole."""
    return NORM_RE.findall(text.lower())


def tok_split(text):
    """The repo's tokenizer: whitespace only, case and punctuation kept."""
    return text.split()


CODE_RUN = re.compile(r"[A-Za-z0-9_]+(?:[.,][0-9]+)*")


def _parts(run):
    return [w.lower() for piece in re.split(r"_+", run) for w in CAMEL.split(piece) if w]


def tok_code(text):
    """The lesson playground's tokCode (study/lessons/P3_bm25.html): take runs of [A-Za-z0-9_]+ with optional
    [.,]digits groups, split each at "_" and at lower/digit -> Upper case changes, lower-case the parts, and also keep
    the whole run (lower-cased) when it has more than one part. So 1.5 and v2.10.3 stay whole; getUserId -> get, user,
    id, getuserid. (P3 K6's toy rule differs: it splits at dots, so 1.5 -> 1, 5.)"""
    out = []
    for run in CODE_RUN.findall(text):
        parts = _parts(run)
        out += parts + ([run.lower()] if len(parts) > 1 else [])
    return out


TOKENIZERS = {"norm": tok_norm, "split": tok_split, "code": tok_code}

# A short list of English function words. Used only to call a question token "common" in the vague-question warning
# and the common-word check (C6); the index itself never drops them.
STOPWORDS = frozenset("""a about above after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further had has have having he her
here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not now of off on
once only or other our ours ourselves out over own same she should so some such than that the their theirs them
themselves then there these they this those through to too under until up very was we were what when where which while
who whom why will with would you your yours yourself yourselves""".split())

# Identifier-like strings, checked in this order; the look-arounds keep the classes from overlapping.
ID_CLASSES = [
    ("version", re.compile(r"(?<![\w.])(?:v?\d+(?:\.\d+){2,}|v\d+(?:\.\d+)+)(?!\w)(?!\.\d)")),
    ("snake_case", re.compile(r"(?<!\w)[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+(?!\w)")),
    ("CamelCase", re.compile(r"(?<!\w)(?:[a-z][a-z0-9]*(?:[A-Z][a-z0-9]+)+[A-Za-z0-9]*|[A-Z][a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)+)(?!\w)")),
    ("ALLCAPS", re.compile(r"(?<!\w)[A-Z][A-Z0-9]+(?!\w)")),
    ("decimal", re.compile(r"(?<![\w.])\d+\.\d+(?!\w)(?!\.\d)")),
]
MAX_ID_ROWS = 25


# ---------------------------------------------------------------------------------------------------------------- input
def load_documents(paths):
    """Files or folders (.pdf, .txt, .md; folders are searched recursively, in sorted order)."""
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
        docs.append({"name": f.name, "stem": f.stem, "path": str(f), "pages": pages, "is_pdf": f.suffix.lower() == ".pdf",
                     "text": "\n".join(pages)})
    return docs


def load_questions(source):
    """A path (.txt or .jsonl) or a list of dicts / strings. Returns a list of {"id", "q", "expect", "type"}."""
    if source is None:
        return []
    if isinstance(source, (str, Path)) and Path(source).is_file():
        path = Path(source)
        lines = path.read_text(encoding="utf-8").splitlines()
        if path.suffix.lower() == ".jsonl":
            items = []
            for n, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise ValueError(f"{path}, line {n}: not valid JSON ({e})") from None
        else:
            items = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
    elif isinstance(source, (list, tuple)):
        items = list(source)
    else:
        raise FileNotFoundError(f"questions file not found: {source}")
    out = []
    for n, it in enumerate(items, 1):
        it = {"q": it} if isinstance(it, str) else dict(it)
        if not str(it.get("q", "")).strip():
            raise ValueError(f"question {n}: missing \"q\"")
        typ = it.get("type")
        if typ is not None and typ not in TYPES:
            raise ValueError(f"question {n}: type {typ!r} is not one of {', '.join(TYPES)}")
        out.append({"id": str(it.get("id") or f"Q{n}"), "q": str(it["q"]), "expect": it.get("expect") or None, "type": typ})
    return out


def make_chunks(docs, size=1000, overlap=200):
    """Plain character windows per document (P3's 91 windows for the climate PDF at 1000/200)."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need chunk-size > 0 and 0 <= overlap < chunk-size")
    single = len(docs) == 1
    chunks = []
    for di, d in enumerate(docs):
        text = d["text"]
        starts, pos = [], 0
        for pg in d["pages"]:
            starts.append(pos)
            pos += len(pg) + 1
        for j, a in enumerate(range(0, len(text), size - overlap)):
            e = min(a + size, len(text))
            chunks.append({"id": f"#{j}" if single else f"{d['stem']}#{j}", "doc": di, "index": j,
                           "page": bisect.bisect_right(starts, a) if d["is_pdf"] else None,
                           "start": a, "end": e, "text": text[a:e]})
    return chunks


def norm_ws(s):
    return " ".join(s.split()).lower()


def ranked(scores):
    """Positions best first; ties by the lower position (the chunk that comes first in the documents)."""
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


# ---------------------------------------------------------------------------------------------------------------- the index
class Index:
    def __init__(self, chunks, tokenizer, k1=DEFAULT_K1, b=DEFAULT_B, epsilon=DEFAULT_EPSILON):
        self.name, self.tok = tokenizer, TOKENIZERS[tokenizer]
        self.tokens = [self.tok(c["text"]) for c in chunks]
        self.N = len(chunks)
        self.total = sum(map(len, self.tokens))
        self.usable = self.N > 0 and self.total > 0
        self.bm = BM25Okapi(self.tokens, k1=k1, b=b, epsilon=epsilon) if self.usable else None
        self.df = collections.Counter(t for c in self.tokens for t in set(c))
        self.floor = epsilon * self.bm.average_idf if self.usable else float("nan")

    def raw_idf(self, n):
        return math.log(self.N - n + 0.5) - math.log(n + 0.5)

    def scores(self, tokens):
        return self.bm.get_scores(tokens) if self.usable else np.zeros(self.N)

    def is_weak(self, t):
        """'Common': an English function word, or a word whose idf is at or below the floor (floored, 0, or valley)."""
        n = self.df.get(t, 0)
        return t in STOPWORDS or (n > 0 and (self.raw_idf(n) <= 0 or self.raw_idf(n) < self.floor))

    def rank_of(self, targets, scores, positive_only=True):
        for r, i in enumerate((i for i in ranked(scores) if scores[i] > 0 or not positive_only), 1):
            if i in targets:
                return r
        return None


# ---------------------------------------------------------------------------------------------------------------- 1 collection
def collection_stats(idx, docs, chunks, epsilon):
    if not idx.usable:
        return {"N": idx.N, "usable": False}
    N, bm = idx.N, idx.bm
    vocab = len(idx.df)
    floored = sorted((t for t, n in idx.df.items() if idx.raw_idf(n) < 0), key=lambda t: (-idx.df[t], t))
    zero = sorted(t for t, n in idx.df.items() if idx.raw_idf(n) == 0)
    floor = idx.floor
    valley_n = [n for n in range(1, N + 1) if 0 <= idx.raw_idf(n) < floor] if floor > 0 else []
    valley_words = [t for t, n in idx.df.items() if n in set(valley_n)]
    once = doubled = frags = 0
    for di, d in enumerate(docs):
        whole = collections.Counter(idx.tok(d["text"]))
        dfd = collections.Counter(t for c, toks in zip(chunks, idx.tokens) if c["doc"] == di for t in set(toks))
        ones = [t for t, n in whole.items() if n == 1]
        once += len(ones)
        doubled += sum(1 for t in ones if dfd[t] >= 2)
        frags += len(set(dfd) - set(whole))
    return {"usable": True, "N": N, "docs": len(docs), "avgdl": bm.avgdl, "vocab": vocab, "mean_idf": bm.average_idf,
            "floor": floor, "epsilon": epsilon, "floored": floored, "pct_floored": 100 * len(floored) / vocab if vocab else 0.0,
            "zero_idf": zero, "valley_n": (min(valley_n), max(valley_n)) if valley_n else None,
            "valley_words": len(valley_words), "once": once, "doubled": doubled,
            "pct_doubled": 100 * doubled / once if once else 0.0, "fragments": frags}


# ---------------------------------------------------------------------------------------------------------------- 2 tokenizer audit
def find_identifiers(docs, given=()):
    found = {}
    for d in docs:
        for cls, pat in ID_CLASSES:
            for m in pat.finditer(d["text"]):
                s = m.group(0)
                if s not in found:
                    found[s] = cls
    for s in given:
        s = s.strip()
        if s and s not in found:
            found[s] = "given"
        elif s:
            found[s] = found[s] + ", given"
    return found


def audit_identifier(ident, cls, docs):
    exact = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(ident) + r"(?![A-Za-z0-9_])")
    anycase = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(ident) + r"(?![A-Za-z0-9_])", re.I)
    forms, casings = collections.Counter(), collections.Counter()
    for d in docs:
        t = d["text"]
        for m in exact.finditer(t):
            a, e = m.start(), m.end()
            while a > 0 and not t[a - 1].isspace():
                a -= 1
            while e < len(t) and not t[e].isspace():
                e += 1
            forms[t[a:e]] += 1
        for m in anycase.finditer(t):
            casings[m.group(0)] += 1
    count = sum(forms.values())
    row = {"ident": ident, "class": cls, "count": count, "forms": dict(forms.most_common()), "casings": dict(casings.most_common()),
           "tokens": {name: TOKENIZERS[name](ident) for name in TOKENIZERS}, "flags": {name: [] for name in TOKENIZERS},
           "ok": {}}
    clean = forms.get(ident, 0)
    if count and clean < count:
        bad = {f: n for f, n in forms.items() if f != ident}
        row["flags"]["split"].append("punctuation attached: " + ", ".join(f"`{f}` ×{n}" for f, n in bad.items())
                                     + (f"; bare ×{clean}" if clean else "; the bare name never occurs"))
    if len(casings) > 1:
        row["flags"]["split"].append("case variants: " + ", ".join(f"`{f}` ×{n}" for f, n in casings.items()))
    row["ok"]["split"] = (count == 0) or clean == count
    for name in ("norm", "code"):
        toks = row["tokens"][name]
        whole = ident.lower() in toks
        row["ok"][name] = whole
        if not whole and len(toks) != 1:
            row["flags"][name].append("cut apart")
        elif not whole:
            row["flags"][name].append("changed")
        if name == "code" and CAMEL.search(ident):
            row["flags"][name].append("case split" + (", whole name kept" if whole else ""))
    return row


def tokenizer_audit(docs, given=()):
    ids = find_identifiers(docs, given)
    rows = [audit_identifier(s, cls, docs) for s, cls in ids.items()]
    by_class = collections.Counter(cls.split(",")[0] for cls in ids.values())
    return {"rows": rows, "by_class": dict(by_class), "n": len(rows), "occurrences": sum(r["count"] for r in rows)}


# ---------------------------------------------------------------------------------------------------------------- 3 per question
def question_result(q, idx, chunks, k):
    toks = idx.tok(q["q"])
    uniq = list(dict.fromkeys(toks))
    known = [t for t in uniq if idx.bm is not None and t in idx.bm.idf]
    unknown = [t for t in uniq if t not in known]
    idf = {t: idx.bm.idf[t] for t in known}
    rarest = max(known, key=lambda t: (idf[t], -uniq.index(t))) if known else None
    scores = idx.scores(toks)                                   # exactly rank_bm25's get_scores(query tokens)
    per_tok = {t: toks.count(t) * idx.scores([t]) for t in known}
    order = ranked(scores)
    pos = [i for i in order if scores[i] > 0]
    weak = [t for t in known if idx.is_weak(t)]
    strong = [t for t in known if t not in weak]
    res = {"id": q["id"], "q": q["q"], "type": q["type"], "expect": q["expect"], "tokens": toks, "unknown": unknown,
           "idf": idf, "rarest": rarest, "weak": weak, "strong": strong, "n_pos": len(pos),
           "top": [{"rank": r, "chunk": chunks[i]["id"], "page": chunks[i]["page"], "score": float(scores[i]),
                    "matched": {t: idx.tokens[i].count(t) for t in known if t in idx.tokens[i]}}
                   for r, i in enumerate(pos[:k], 1)],
           "zero": not pos, "fallback": [chunks[i]["id"] for i in np.argsort(scores)[::-1][:k]],
           "vague": bool(known) and not strong,
           "top_score": float(scores[pos[0]]) if pos else None, "kth_score": float(scores[pos[k - 1]]) if len(pos) >= k else None}
    if pos:
        top = pos[0]
        res["weak_share"] = sum(float(per_tok[t][top]) for t in weak) / float(scores[top])
        res["weak_only"] = sum(1 for i in pos if not any(per_tok[t][i] > 0 for t in strong))
    else:
        res["weak_share"], res["weak_only"] = None, 0
    res["_scores"] = scores
    return res


# ---------------------------------------------------------------------------------------------------------------- 4 measuring
def targets_for(expect, chunks):
    e = norm_ws(expect)
    return {i for i, c in enumerate(chunks) if e in c["_norm"]}


def metrics(ranks, k):
    n = len(ranks)
    if not n:
        return None
    return {"n": n, "hit1": sum(r == 1 for r in ranks if r), "hitk": sum(r is not None and r <= k for r in ranks),
            "mrr": sum(1 / r for r in ranks if r) / n}


def per_type(rows, key, k):
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r["type"] or "untyped"].append(r[key])
    out = {t: metrics(v, k) for t, v in sorted(groups.items())}
    out["all"] = metrics([r[key] for r in rows], k)
    return out


def load_dense(model_name):
    import os
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    try:
        import transformers
        transformers.utils.logging.disable_progress_bar()
    except Exception:  # noqa: BLE001
        pass
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name, device="cpu")


def embed(model, texts):
    return model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)


# ---------------------------------------------------------------------------------------------------------------- the check
def run_check(docs, questions=None, identifiers=(), chunk_size=1000, overlap=200, tokenizer="norm", k=4, dense=False,
              k1=DEFAULT_K1, b=DEFAULT_B, epsilon=DEFAULT_EPSILON, dense_model=DEFAULT_MODEL):
    """docs: file/folder paths (or already loaded documents); questions: a path or a list. Returns a result dict."""
    if tokenizer not in TOKENIZERS:
        raise ValueError(f"tokenizer must be one of {', '.join(TOKENIZERS)}")
    if k < 1:
        raise ValueError("k must be at least 1")
    docs = docs if (docs and isinstance(docs[0], dict)) else load_documents(docs)
    qs = load_questions(questions)
    chunks = make_chunks(docs, chunk_size, overlap)
    for c in chunks:
        c["_norm"] = norm_ws(c["text"])
    indexes = {name: Index(chunks, name, k1, b, epsilon) for name in TOKENIZERS}
    idx = indexes[tokenizer]
    res = {"settings": {"tokenizer": tokenizer, "chunk_size": chunk_size, "overlap": overlap, "k": k, "k1": k1, "b": b,
                        "epsilon": epsilon, "dense": dense, "dense_model": dense_model if dense else None,
                        "versions": {p: _version(p) for p in ("rank-bm25", "numpy", "pymupdf")}},
           "documents": [{"name": d["name"], "pages": len(d["pages"]), "chars": len(d["text"])} for d in docs],
           "chunks": [{"id": c["id"], "page": c["page"], "start": c["start"], "end": c["end"]} for c in chunks]}
    res["collection"] = collection_stats(idx, docs, chunks, epsilon)
    res["audit"] = tokenizer_audit(docs, identifiers)
    res["questions"] = [question_result(q, idx, chunks, k) for q in qs] if idx.usable else []
    # ---- measuring
    labelled = []
    for q, qr in zip(qs, res["questions"]):
        if not q["expect"]:
            continue
        tg = targets_for(q["expect"], chunks)
        row = {"id": q["id"], "q": q["q"], "type": q["type"], "expect": q["expect"], "targets": [chunks[i]["id"] for i in sorted(tg)],
               "found": bool(tg), "long": len(q["expect"]) > overlap}
        for name, ix in indexes.items():
            row[f"rank_{name}"] = ix.rank_of(tg, ix.scores(ix.tok(q["q"]))) if (tg and ix.usable) else None
        row["rank"] = row[f"rank_{tokenizer}"]
        row["target_score"] = max((float(qr["_scores"][i]) for i in tg), default=None)
        labelled.append(row)
    res["dense_error"] = None
    if dense and labelled:
        try:
            model = load_dense(dense_model)
            V = embed(model, [c["text"] for c in chunks])
            for row in labelled:
                if row["found"]:
                    tg = {i for i, c in enumerate(chunks) if c["id"] in set(row["targets"])}
                    cos = V @ embed(model, [row["q"]])[0]
                    row["rank_dense"] = next(r for r, i in enumerate(ranked(cos), 1) if i in tg)
                else:
                    row["rank_dense"] = None
        except Exception as e:  # noqa: BLE001
            res["dense_error"] = f"{type(e).__name__}: {str(e)[:200]}"
    usable_rows = [r for r in labelled if r["found"]]
    res["measuring"] = {"rows": labelled, "unfound": [r["id"] for r in labelled if not r["found"]],
                        "by_type": {name: per_type(usable_rows, f"rank_{name}", k) for name in TOKENIZERS} if usable_rows else {},
                        "dense_by_type": (per_type(usable_rows, "rank_dense", k)
                                          if usable_rows and dense and not res["dense_error"] else None)}
    res["checklist"] = checklist(res)
    res["recommendation"] = recommend(res)
    for qr in res["questions"]:
        qr.pop("_scores", None)
    return res


def _version(p):
    try:
        return md.version(p)
    except md.PackageNotFoundError:
        return "not installed"


# ---------------------------------------------------------------------------------------------------------------- 5 checklist
def _fmt(x, d=4):
    return "-" if x is None else f"{x:.{d}f}"


def checklist(res):
    s, col, aud, qs, mea = res["settings"], res["collection"], res["audit"], res["questions"], res["measuring"]
    tok, k = s["tokenizer"], s["k"]
    items = []

    def add(cid, text, verdict, evidence):
        items.append({"id": cid, "check": text, "verdict": verdict, "evidence": evidence})

    present = [r for r in aud["rows"] if r["count"] > 0]
    add("C1", "Users search exact identifiers (codes, names, versions, numbers)", ASK,
        f"manual: only you know what users type. Your documents contain {len(present)} distinct identifier-like strings "
        f"({aud['occurrences']} occurrences): " + ", ".join(f"{c} {n}" for c, n in sorted(aud["by_class"].items()))
        + ". If users search for these, BM25 is the retriever that can match them exactly." if present else
        "manual: no identifier-like strings were detected in the documents.")
    broken = [r for r in present if not r["ok"][tok]]
    ex_rows = mea["by_type"]
    meas_note = ""
    better = None
    if ex_rows and ex_rows[tok].get("exact-term"):
        mrr = {name: ex_rows[name]["exact-term"]["mrr"] for name in TOKENIZERS if ex_rows[name].get("exact-term")}
        meas_note = " Measured on your exact-term questions, MRR: " + ", ".join(f"{n} {v:.3f}" for n, v in mrr.items()) + "."
        best = max(mrr.values())
        if mrr[tok] < best - 1e-12:
            better = [n for n, v in mrr.items() if v == best]
    if not present and not better:
        add("C2", "Identifiers survive the tokenizer", ASK, "no identifier-like strings found to test." + meas_note)
    elif broken or better:
        ev = ""
        if broken:
            ev = (f"under `{tok}`, {len(broken)} of {len(present)} identifiers do not survive whole: "
                  + ", ".join(f"`{r['ident']}`" for r in broken[:8]) + (" …" if len(broken) > 8 else "") + " (see section 2).")
        if better:
            ev += f" `{' / '.join(better)}` ranks your exact-term questions higher than `{tok}`."
        add("C2", "Identifiers survive the tokenizer", BAD, ev.strip() + meas_note)
    else:
        add("C2", "Identifiers survive the tokenizer", OK, f"under `{tok}`, all {len(present)} identifiers stay whole." + meas_note)
    add("C3", "The same tokenizer is used for documents and questions", ASK,
        f"manual: this tool uses `{tok}` on both sides. Check your own index and query code; a different tokenizer on one "
        "side means a token can never match.")
    para = [r for r in mea["rows"] if r["type"] == "paraphrase" and r["found"]]
    if para:
        m = metrics([r["rank"] for r in para], k)
        dn = ""
        if mea["dense_by_type"] and mea["dense_by_type"].get("paraphrase"):
            dm = mea["dense_by_type"]["paraphrase"]
            dn = f"; dense Hit@{k} {dm['hitk']}/{dm['n']}, MRR {dm['mrr']:.3f}"
        add("C4", "Users also ask in their own words (paraphrases)", OK if m["hitk"] == m["n"] else BAD,
            f"measured on {m['n']} paraphrase question(s): BM25 Hit@{k} {m['hitk']}/{m['n']}, MRR {m['mrr']:.3f}{dn}. "
            "BM25 has no synonyms: a paraphrase only matches through shared words.")
    else:
        add("C4", "Users also ask in their own words (paraphrases)", ASK,
            "manual, or label some questions with type \"paraphrase\" and an \"expect\" string to measure it.")
    if not col.get("usable"):
        add("C5", "The collection is large and varied enough", BAD, "no chunk contains a token: nothing to index.")
    else:
        why = []
        if col["N"] < 3:
            why.append(f"only {col['N']} chunk(s); with 2, a word in one chunk gets idf 0 and a shared word a negative idf")
        if col["mean_idf"] <= 0:
            why.append(f"mean idf {col['mean_idf']:.6f} ≤ 0")
        if col["floor"] < 0:
            why.append(f"negative floor ({col['floor']:.6f}): a word in most chunks lowers a chunk's score")
        elif col["floor"] == 0:
            why.append("floor 0: words in more than half of the chunks add nothing")
        add("C5", "The collection is large and varied enough (≥ 3 chunks, mean idf > 0, floor > 0)", BAD if why else OK,
            "; ".join(why) + "." if why else
            f"{col['N']} chunks, mean idf {col['mean_idf']:.6f}, floor {col['floor']:.6f}; {col['pct_floored']:.1f}% of the "
            "vocabulary is floored.")
    bad6 = [q for q in qs if q["zero"] is False and (q["vague"] or (q["weak_share"] or 0) > 0.5)]
    if not qs:
        add("C6", "Common words do not decide the ranking", ASK, "no questions given.")
    else:
        ev = "; ".join(f"{q['id']}: {100 * q['weak_share']:.0f}% of the top score from common words"
                       + (" (vague: no rare word matched)" if q["vague"] else "") for q in bad6)
        worst = max((q["weak_only"] / q["n_pos"] for q in qs if q["n_pos"]), default=0)
        add("C6", "Common words do not decide the ranking", BAD if bad6 else OK,
            (ev + ". " if bad6 else "on every question, rare words carry most of the top score. ")
            + f"Chunks matched by common words only: up to {100 * worst:.0f}% of a question's matches.")
    short = [q for q in qs if q["n_pos"] < k]
    if not qs:
        add("C7", "Only chunks with score > 0 are returned", ASK, "no questions given.")
    elif short:
        add("C7", "Only chunks with score > 0 are returned", BAD,
            "on your data the filter matters: " + "; ".join(
                f"{q['id']} has {q['n_pos']} chunk(s) above 0" + (f" (code returning {k} anyway would hand back {', '.join(q['fallback'])})"
                                                                  if q["zero"] else "") for q in short)
            + ". Make sure your code drops scores ≤ 0 instead of always returning k.")
    else:
        add("C7", "Only chunks with score > 0 are returned", OK,
            f"every question has at least {k} chunks above 0, so the filter changes nothing here (keep it anyway).")
    found = [r for r in mea["rows"] if r["found"]]
    if not mea["rows"]:
        add("C8", "Labelled questions exist", BAD, "no question has an \"expect\" string, so nothing can be measured.")
    elif mea["unfound"]:
        add("C8", "Labelled questions exist", BAD,
            f"{len(found)} labelled; the \"expect\" text of {', '.join(mea['unfound'])} is in no chunk (a typo, or text cut "
            "across two chunks): fix those labels.")
    else:
        cnt = collections.Counter(r["type"] or "untyped" for r in found)
        add("C8", "Labelled questions exist", OK,
            f"{len(found)} labelled (" + ", ".join(f"{t} {n}" for t, n in sorted(cnt.items())) + ")."
            + (" Few questions per type: a demonstration, not an evaluation." if min(cnt.values()) < 10 else ""))
    dbt = mea["dense_by_type"]
    if not s["dense"]:
        add("C9", "BM25 vs dense, per question type", ASK, "run with --dense to compare (MiniLM, local).")
    elif res["dense_error"]:
        add("C9", "BM25 vs dense, per question type", ASK, f"dense model could not load: {res['dense_error']}")
    elif not dbt:
        add("C9", "BM25 vs dense, per question type", ASK, "no labelled questions to compare on.")
    else:
        bbt = mea["by_type"][tok]
        lines, worse = [], []
        for t in (t for t in dbt if t != "all"):
            lines.append(f"{t}: BM25 MRR {bbt[t]['mrr']:.3f} vs dense {dbt[t]['mrr']:.3f}")
            if dbt[t]["mrr"] > bbt[t]["mrr"] + 1e-12:
                worse.append(t)
        add("C9", "BM25 vs dense, per question type", BAD if worse else OK,
            "; ".join(lines) + (f". Dense does better on: {', '.join(worse)}." if worse else ". BM25 is as good or better on every type."))
    default = (s["k1"], s["b"], s["epsilon"]) == (DEFAULT_K1, DEFAULT_B, DEFAULT_EPSILON)
    add("C10", "k1 and b stay at their defaults unless measured", OK if default else ASK,
        f"k1 {s['k1']}, b {s['b']}, epsilon {s['epsilon']} (rank_bm25 {s['versions']['rank-bm25']})"
        + ("." if default else ": changed from 1.5 / 0.75 / 0.25; keep it only if measured on labelled questions."))
    if col.get("usable"):
        add("C11", "The chunking is fixed and recorded", ASK,
            f"manual: record it with the index: {s['chunk_size']}-character windows, {s['overlap']} overlap, {col['N']} chunks. "
            f"The overlap counts {col['doubled']} of {col['once']} once-only tokens ({col['pct_doubled']:.1f}%) in two chunks, "
            f"and {col['fragments']} tokens are word pieces cut at a chunk edge. Any change alters every df and idf.")
    else:
        add("C11", "The chunking is fixed and recorded", ASK, "no usable chunks.")
    if qs:
        tops = [q["top_score"] for q in qs if q["top_score"] is not None]
        add("C12", "No fixed threshold on raw scores", ASK,
            "manual: top scores across your questions range " + (f"{min(tops):.4f} to {max(tops):.4f}" if tops else "-")
            + "; see the score table in section 3. A score depends on the question's words, not on whether a chunk answers it.")
    else:
        add("C12", "No fixed threshold on raw scores", ASK, "manual: no questions given.")
    return items


# ---------------------------------------------------------------------------------------------------------------- 6 recommendation
def recommend(res):
    c = {i["id"]: i for i in res["checklist"]}
    if c["C5"]["verdict"] == BAD:
        return {"verdict": "not enough data to judge", "reasons": [c["C5"]["evidence"]]}
    if c["C2"]["verdict"] == BAD:
        return {"verdict": "fix the tokenizer first", "reasons": [c["C2"]["evidence"]]}
    if not res["questions"] or not res["measuring"]["rows"]:
        why = "no questions were given" if not res["questions"] else             "no labelled questions (add \"expect\" strings), so retrieval cannot be measured"
        return {"verdict": "not enough data to judge", "reasons": [why]}
    hybrid = [c[i]["evidence"] for i in ("C9", "C4") if c[i]["verdict"] == BAD]
    if hybrid:
        notes = [c["C6"]["evidence"]] if c["C6"]["verdict"] == BAD else []
        return {"verdict": "use hybrid (BM25 + dense)", "reasons": hybrid + notes}
    reasons = ["identifiers survive the tokenizer and BM25 found the labelled chunks."]
    if c["C9"]["verdict"] == ASK:
        reasons.append("not compared with dense yet (run with --dense).")
    if c["C6"]["verdict"] == BAD:
        reasons.append("but: " + c["C6"]["evidence"])
    return {"verdict": "BM25 alone looks fine", "reasons": reasons}


# ---------------------------------------------------------------------------------------------------------------- report
def _cell(x):
    return str(x).replace("|", "\\|").replace("\n", " ")


def _toks(ts, limit=12):
    ts = list(ts)
    return " · ".join(f"`{_cell(t)}`" for t in ts[:limit]) + (" …" if len(ts) > limit else "") if ts else "(none)"


def _rank(r):
    return "not found" if r is None else str(r)


def render_report(res):
    s, col, aud, mea = res["settings"], res["collection"], res["audit"], res["measuring"]
    tok, k = s["tokenizer"], s["k"]
    L = []
    w = L.append
    w("# BM25 fit check")
    w("")
    w("**What this is:** an automatic check of whether BM25 keyword search suits these documents and questions, measured on your own chunks.")
    w("**What this is not:** an evaluation. A few labelled questions show the mechanism; decide with many questions per type.")
    w("")
    rec = res["recommendation"]
    w(f"**Recommendation: {rec['verdict']}** (section 6). Checklist: "
      + " ".join(f"{i['id']} {i['verdict']}" for i in res["checklist"]) + ".")
    w("")
    w(f"Settings: tokenizer `{tok}` · {s['chunk_size']}-character chunks, overlap {s['overlap']} · k {k} · "
      f"k1 {s['k1']}, b {s['b']}, epsilon {s['epsilon']} · rank-bm25 {s['versions']['rank-bm25']}, numpy "
      f"{s['versions']['numpy']}, pymupdf {s['versions']['pymupdf']}" + (f" · dense `{s['dense_model']}`" if s["dense"] else "") + ".")
    w("Documents: " + "; ".join(f"`{d['name']}` ({d['pages']} page(s), {d['chars']:,} characters)" for d in res["documents"]) + ".")
    w("")
    # 1
    w("## 1 Collection")
    w("")
    if not col.get("usable"):
        w(f"Not usable: {col['N']} chunk(s) and no tokens. Nothing below can be computed.")
    else:
        w("| Measure | Value | What it means |")
        w("|---|---|---|")
        w(f"| Chunks N | {col['N']} | from {col['docs']} document(s) |")
        w(f"| Average length avgdl | {col['avgdl']:.2f} tokens | b compares each chunk with this |")
        w(f"| Vocabulary | {col['vocab']:,} distinct tokens | |")
        w(f"| Mean idf (before the floor) | {col['mean_idf']:.6f} | |")
        w(f"| Floor = {col['epsilon']} × mean idf | {col['floor']:.6f} | the idf used for any word in more than half of the chunks |")
        fl = ", ".join(f"`{t}`" for t in col["floored"][:8]) + (" …" if len(col["floored"]) > 8 else "")
        w(f"| Floored words | {len(col['floored'])} ({col['pct_floored']:.1f}% of the vocabulary) | {fl or '-'} |")
        if col["zero_idf"]:
            w(f"| Words with idf exactly 0 | {len(col['zero_idf'])} | in exactly half of the chunks: they add nothing |")
        if col["valley_n"]:
            lo, hi = col["valley_n"]
            w(f"| The valley | n = {lo} to {hi} ({col['valley_words']} words) | a word in {lo} to {hi} chunks is worth less than the most common words |")
        else:
            w("| The valley | none | (the floor is not above 0) |")
        w(f"| Once-only tokens counted in 2+ chunks | {col['doubled']} of {col['once']} ({col['pct_doubled']:.1f}%) | the overlap doubles their df |")
        w(f"| Token fragments | {col['fragments']} | word pieces cut at a chunk edge |")
    w("")
    # 2
    w("## 2 Tokenizer audit")
    w("")
    if not aud["rows"]:
        w("No identifier-like strings (ALLCAPS, CamelCase, snake_case, versions, decimals) were found, and none were given.")
    else:
        w(f"{aud['n']} distinct identifier-like strings, {aud['occurrences']} occurrences: "
          + ", ".join(f"{c} {n}" for c, n in sorted(aud["by_class"].items())) + f". Chosen tokenizer: `{tok}`.")
        w("Flags: *punctuation attached* (`split()` glues brackets or commas to the name, so the bare name misses it), "
          "*case variants* (`split()` keeps case), *cut apart* (the whole name is not one token), "
          "*case split* (split where the letter case changes).")
        w("")
        rows = sorted(aud["rows"], key=lambda r: (r["ok"][tok], all(r["ok"].values()), -r["count"], r["ident"]))
        w("| Identifier | Class | Count | `split()` | `norm` | `code` | Flags |")
        w("|---|---|---|---|---|---|---|")
        for r in rows[:MAX_ID_ROWS]:
            flags = " · ".join(f"{n}: " + "; ".join(r["flags"][n]) for n in ("split", "norm", "code") if r["flags"][n]) or "-"
            cells = []
            for n in ("split", "norm", "code"):
                cells.append(("✗ " if not r["ok"][n] else "") + _toks(r["tokens"][n] if n != "split" else list(r["forms"]) or r["tokens"][n], 6))
            w(f"| `{_cell(r['ident'])}` | {r['class']} | {r['count']} | {cells[0]} | {cells[1]} | {cells[2]} | {_cell(flags)} |")
        if len(rows) > MAX_ID_ROWS:
            w(f"| … | | | | | | {len(rows) - MAX_ID_ROWS} more, all whole under `{tok}` |"
              if all(r["ok"][tok] for r in rows[MAX_ID_ROWS:]) else f"| … | | | | | | {len(rows) - MAX_ID_ROWS} more |")
        w("")
        w("`split()` column: the forms the name takes in the text after splitting at spaces. ✗ = does not survive whole.")
    w("")
    # 3
    w("## 3 Per question")
    w("")
    if not res["questions"]:
        w("No questions given." if col.get("usable") else "No usable index.")
    else:
        w(f"| Question | Type | Chunks > 0 | Top score | Score at rank {k} | Right chunk's score |")
        w("|---|---|---|---|---|---|")
        tscore = {r["id"]: r["target_score"] for r in mea["rows"]}
        for q in res["questions"]:
            w(f"| {q['id']} | {q['type'] or '-'} | {q['n_pos']} | {_fmt(q['top_score'])} | {_fmt(q['kth_score'])} | "
              f"{_fmt(tscore.get(q['id']))} |")
        w("")
        for q in res["questions"]:
            w(f"### {q['id']} · \"{_cell(q['q'])}\"")
            w("")
            w(f"- Tokens (`{tok}`): {_toks(q['tokens'], 20)}")
            w(f"- Not in the index (df 0, add nothing): {_toks(q['unknown'])}")
            if q["rarest"]:
                w(f"- Rarest token: `{q['rarest']}`, idf {q['idf'][q['rarest']]:.6f}"
                  + ("; common tokens: " + _toks(q["weak"]) if q["weak"] else ""))
            if q["zero"]:
                w(f"- **Zero-score warning:** no question token matched; every chunk scores ≤ 0. Code that returns {k} chunks "
                  f"anyway (`np.argsort(scores)[::-1][:{k}]`) would hand back arbitrary chunks: {', '.join(q['fallback'])}.")
            elif q["n_pos"] < k:
                w(f"- **Short list:** only {q['n_pos']} chunk(s) score above 0; returning {k} would pad with arbitrary chunks.")
            if q["vague"]:
                w(f"- **Vague warning:** every matched token is common ({_toks(q['weak'])}), so the ranking rests on common "
                  f"words: {q['n_pos']} chunks match, none through a rare word.")
            if q["top"]:
                w("")
                w("| Rank | Chunk | Page | Score | Matched tokens (count) |")
                w("|---|---|---|---|---|")
                for t in q["top"]:
                    m = ", ".join(f"`{_cell(x)}` ×{n}" for x, n in t["matched"].items())
                    w(f"| {t['rank']} | {t['chunk']} | {t['page'] if t['page'] else '-'} | {t['score']:.4f} | {m} |")
                if q["weak_share"] is not None:
                    w("")
                    w(f"Common words give {100 * q['weak_share']:.0f}% of the top score; {q['weak_only']} of the {q['n_pos']} "
                      "matching chunks match through common words only.")
            w("")
    # 4
    w("## 4 Measuring")
    w("")
    if not mea["rows"]:
        w("No question has an `expect` string, so nothing is measured. Add `\"expect\": \"text the right chunk contains\"`.")
    else:
        dense_on = mea["dense_by_type"] is not None
        w("Rank of the first chunk that contains the `expect` text (case and spacing ignored). BM25 ranks only chunks "
          "that score above 0; *not found* = the right chunk scores 0. Dense ranks every chunk.")
        w("")
        w("| Question | Type | Right chunk(s) | `split()` | `norm` | `code` |" + (" Dense |" if dense_on else ""))
        w("|---|---|---|---|---|---|" + ("---|" if dense_on else ""))
        for r in mea["rows"]:
            tg = ", ".join(r["targets"]) if r["found"] else "**expect text in no chunk**"
            w(f"| {r['id']} | {r['type'] or '-'} | {tg} | {_rank(r['rank_split'])} | {_rank(r['rank_norm'])} | "
              f"{_rank(r['rank_code'])} |" + (f" {_rank(r.get('rank_dense'))} |" if dense_on else ""))
        w("")
        if mea["by_type"]:
            w(f"Per type, chosen tokenizer `{tok}`" + (" and dense" if dense_on else "") + f" (MRR = mean of 1 ÷ rank, not found = 0; no cut-off):")
            w("")
            w(f"| Type | n | BM25 Hit@1 | BM25 Hit@{k} | BM25 MRR |" + (f" Dense Hit@1 | Dense Hit@{k} | Dense MRR |" if dense_on else ""))
            w("|---|---|---|---|---|" + ("---|---|---|" if dense_on else ""))
            for t, m in mea["by_type"][tok].items():
                line = f"| {t} | {m['n']} | {m['hit1']}/{m['n']} | {m['hitk']}/{m['n']} | {m['mrr']:.3f} |"
                if dense_on:
                    d = mea["dense_by_type"][t]
                    line += f" {d['hit1']}/{d['n']} | {d['hitk']}/{d['n']} | {d['mrr']:.3f} |"
                w(line)
            w("")
            w("BM25 MRR per type under each tokenizer:")
            w("")
            types = list(mea["by_type"][tok])
            w("| Tokenizer | " + " | ".join(types) + " |")
            w("|---|" + "---|" * len(types))
            for name in TOKENIZERS:
                w(f"| `{name}` | " + " | ".join(f"{mea['by_type'][name][t]['mrr']:.3f}" for t in types) + " |")
        if res["dense_error"]:
            w("")
            w(f"Dense: not measured, the model could not load ({res['dense_error']}).")
    w("")
    # 5
    w("## 5 Checklist")
    w("")
    w("✓ = no problem found · ✗ = a problem found on your data · ? = check by hand (the evidence helps).")
    w("")
    w("| # | Check | Verdict | Evidence |")
    w("|---|---|---|---|")
    for i in res["checklist"]:
        w(f"| {i['id']} | {i['check']} | {i['verdict']} | {_cell(i['evidence'])} |")
    w("")
    # 6
    w("## 6 Recommendation")
    w("")
    w(f"**{rec['verdict']}**")
    w("")
    for r in rec["reasons"]:
        w(f"- {r}")
    w("")
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Does BM25 suit my documents and questions? Writes a Markdown report.")
    ap.add_argument("--docs", nargs="+", required=True, help="files or folders (.pdf, .txt, .md)")
    ap.add_argument("--questions", help=".txt (one per line) or .jsonl ({\"q\", \"expect\", \"type\"})")
    ap.add_argument("--identifiers", default="", help="comma-separated names to audit as well")
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--tokenizer", choices=list(TOKENIZERS), default="norm")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--k1", type=float, default=DEFAULT_K1)
    ap.add_argument("--b", type=float, default=DEFAULT_B)
    ap.add_argument("--dense", action="store_true", help="also rank with MiniLM (local) and compare per type")
    ap.add_argument("--dense-model", default=DEFAULT_MODEL)
    ap.add_argument("--report", help="write the Markdown report here (default: print it)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    res = run_check(a.docs, a.questions, [s for s in a.identifiers.split(",") if s.strip()], a.chunk_size, a.overlap,
                    a.tokenizer, a.k, a.dense, a.k1, a.b, DEFAULT_EPSILON, a.dense_model)
    text = render_report(res)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8")
        c = res["collection"]
        print(f"chunks {c['N']}" + (f", avgdl {c['avgdl']:.2f}, floor {c['floor']:.6f}" if c.get("usable") else ""))
        for i in res["checklist"]:
            print(f"{i['id']:4s} {i['verdict']}  {i['check']}")
        print(f"recommendation: {res['recommendation']['verdict']}")
        print(f"report: {a.report}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
