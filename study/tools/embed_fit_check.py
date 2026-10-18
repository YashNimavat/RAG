"""embed_fit_check: does my embedding setup suit MY documents and questions?

What this is: a command-line tool (also importable) that chunks your documents like the course's v0 index (the 07
recursive splitter, per page, 1,000 characters with 200 overlap), embeds them with a LOCAL sentence-transformers model,
runs your questions, and writes a Markdown report:
  1 Setup            model, numbers per vector, length limit, modules, pooling, Normalize, prompts, similarity
  2 Chunks vs limit  token counts with the model's own tokenizer ([CLS]/[SEP] included); chunks over the limit
  3 Vectors          lengths as returned, the self-retrieval test, the score spread, near-duplicate chunks
  4 Per question     the top k with scores; the rank of the chunk that contains "expect"
  5 Measuring        Hit@1 / Hit@k / MRR@10 per question type; with --rerank, --dims and --int8 one row per arm
  6 Checklist        C1-C12 with a verdict (✓ fine, ✗ problem found, ? check by hand) and the evidence
  7 Recommendation   the first thing to fix, or "setup looks sound"
What this is not: an evaluation. A handful of labelled questions shows the mechanism, not which setting is better.

Lesson: study/lessons/P4_embeddings.html (steps 3-12). Checks C1-C12 are the lesson's real-world checklist.

No API calls. --provider cohere is reserved for when the course's study/llmops/ cache exists (record once, replay
offline); until then it refuses to run. Book text must never be sent to any API. Standard library + numpy + pymupdf
+ sentence-transformers (models load from the local Hugging Face cache only; HF_HUB_OFFLINE=1 is set unless you set it yourself).

Usage, from rag_learning/:
    uv run python study/tools/embed_fit_check.py --docs my_docs/ --questions q.jsonl --report embed_report.md
    uv run python study/tools/embed_fit_check.py --docs a.pdf --questions q.jsonl --rerank --dims 256,128 --int8 --threshold 0.5
Questions: .txt (one per line; blank lines and lines starting with # are skipped) or .jsonl with
    {"q": "...", "expect": "text the right chunk contains" (optional), "type": "any label" (optional), "id": "..." (optional)}
"expect" is matched case-insensitively with whitespace normalised; keep it shorter than --overlap. It may also be a list
of texts: a chunk that contains any of them counts as right (for answers stated in more than one place).

Import:
    from embed_fit_check import run_check, render_report
    res = run_check(["doc.pdf"], "questions.jsonl", k=4)
    print(render_report(res))
"""
from __future__ import annotations

import argparse
import bisect
import collections
import importlib.metadata as md
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
EXTS = (".pdf", ".txt", ".md")
SEPARATORS = ("\n\n", "\n", " ")
OK, BAD, ASK = "✓", "✗", "?"
DUP = 0.98                       # cosine above which two chunks count as near-duplicates
MIN_LABELLED = 10                # fewer labelled questions than this = "mechanism only"
SELF_SAMPLE = 5                  # chunks used for the self-retrieval (direction) test
RERANK_N = 10                    # bi-encoder shortlist the cross-encoder reorders


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
        docs.append({"name": f.name, "stem": f.stem, "path": str(f), "pages": pages, "is_pdf": f.suffix.lower() == ".pdf"})
    if not docs:
        raise ValueError("no .pdf, .txt or .md documents found")
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
        exp = it.get("expect") or None
        if isinstance(exp, str):
            exp = [exp]
        out.append({"id": str(it.get("id") or f"Q{n}"), "q": str(it["q"]), "expect": exp,
                    "type": it.get("type") or None})
    return out


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


def make_chunks(docs, size=1000, overlap=200, chunker="v0"):
    """v0: the recursive splitter per page (v0's 97 chunks for the climate PDF). windows: plain character windows
    over the joined pages (P3's 91 windows)."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need chunk-size > 0 and 0 <= overlap < chunk-size")
    single = len(docs) == 1
    chunks = []
    for di, d in enumerate(docs):
        n = 0
        if chunker == "v0":
            for pi, page in enumerate(d["pages"], 1):
                for a, b in recursive_spans(page, size, overlap):
                    chunks.append({"id": f"#{n}" if single else f"{d['stem']}#{n}", "doc": di, "page": pi if d["is_pdf"] else None,
                                   "text": page[a:b]})
                    n += 1
        elif chunker == "windows":
            text = "\n".join(d["pages"])
            starts, pos = [], 0
            for pg in d["pages"]:
                starts.append(pos)
                pos += len(pg) + 1
            for a in range(0, len(text), size - overlap):
                chunks.append({"id": f"#{n}" if single else f"{d['stem']}#{n}", "doc": di,
                               "page": bisect.bisect_right(starts, a) if d["is_pdf"] else None, "text": text[a:min(a + size, len(text))]})
                n += 1
        else:
            raise ValueError(f"unknown chunker {chunker!r} (use v0 or windows)")
    chunks = [c for c in chunks if c["text"].strip()]
    if not chunks:
        raise ValueError("the documents contain no text")
    return chunks


def norm_ws(s):
    return " ".join(s.split()).lower()


# ---------------------------------------------------------------------------------------------------------------- models
def _quiet():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")         # local cache only: this tool never downloads
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    import logging
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    try:
        import transformers
        transformers.utils.logging.disable_progress_bar()
    except Exception:  # noqa: BLE001
        pass


def load_model(name):
    _quiet()
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name, device="cpu")


def model_setup(model, name):
    mods = [type(m).__name__ for m in model]
    pooling = None
    for m in model:
        if type(m).__name__ == "Pooling":
            cfg = m.get_config_dict()
            pooling = cfg.get("pooling_mode") or next((k.replace("pooling_mode_", "").replace("_tokens", "")
                                                       for k, v in cfg.items() if k.startswith("pooling_mode_") and v), None)
    licence = None
    ref = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{name.replace('/', '--')}"
    snap = (ref / "refs" / "main").read_text().strip() if (ref / "refs" / "main").exists() else None
    readme = ref / "snapshots" / snap / "README.md" if snap else None
    if readme and readme.exists():
        m = re.search(r"^license:\s*(\S+)", readme.read_text(encoding="utf-8", errors="replace"), re.M)
        licence = m.group(1) if m else None
    return {"name": name, "snapshot": snap[:8] if snap else None, "dim": model.get_embedding_dimension(),
            "max_seq_length": model.max_seq_length, "modules": mods, "pooling": pooling, "normalize": "Normalize" in mods,
            "prompts": dict(model.prompts or {}), "similarity": model.similarity_fn_name, "licence": licence}


def encode_docs(model, texts, dim=None):
    return model.encode_document(list(texts), convert_to_numpy=True, batch_size=32, show_progress_bar=False,
                                 truncate_dim=dim).astype(np.float32)


def encode_queries(model, texts, dim=None):
    return model.encode_query(list(texts), convert_to_numpy=True, batch_size=32, show_progress_bar=False,
                              truncate_dim=dim).astype(np.float32)


def unit(M):
    n = np.linalg.norm(M, axis=-1, keepdims=True)
    return M / np.where(n == 0, 1, n)


def ranked(scores):
    """positions best first; ties broken by the lower position (the course rule)."""
    return sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))


def first_hit(order, targets):
    return next((r for r, i in enumerate(order, 1) if i in targets), None)


def metrics(ranks, k):
    n = len(ranks)
    if not n:
        return None
    return {"n": n, "hit1": sum(r == 1 for r in ranks if r), "hitk": sum(r is not None and r <= k for r in ranks),
            "mrr": sum(1 / r for r in ranks if r and r <= 10) / n}


# ---------------------------------------------------------------------------------------------------------------- the check
def run_check(docs, questions=None, model=DEFAULT_MODEL, chunk_size=1000, overlap=200, chunker="v0", k=4,
              rerank=False, dims=(), int8=False, threshold=None, manifest=None, reranker=DEFAULT_RERANKER):
    docs = load_documents(docs) if not (docs and isinstance(docs[0], dict)) else docs
    qs = load_questions(questions)
    chunks = make_chunks(docs, chunk_size, overlap, chunker)
    m = load_model(model)
    setup = model_setup(m, model)
    texts = [c["text"] for c in chunks]
    N = len(chunks)
    for c in chunks:
        c["_norm"] = norm_ws(c["text"])

    # 2 chunks vs the limit
    tok = m.tokenizer
    ntok = [len(tok(t, add_special_tokens=True, truncation=False)["input_ids"]) for t in texts]
    over = [i for i, n in enumerate(ntok) if n > setup["max_seq_length"]]
    cut_chars = {}
    for i in over:
        offs = tok(texts[i], add_special_tokens=False, return_offsets_mapping=True, truncation=False)["offset_mapping"]
        cut_chars[i] = len(texts[i]) - offs[setup["max_seq_length"] - 3][1]
    lengths = {"min": min(ntok), "median": int(np.median(ntok)), "max": max(ntok), "over": over, "ignored_chars": cut_chars,
               "over_128": sum(n > 128 for n in ntok), "tokens_over": {i: ntok[i] for i in over}}

    # 3 vectors
    E_raw = encode_docs(m, texts)
    norms = np.linalg.norm(E_raw, axis=1)
    E = unit(E_raw)
    sample = sorted({int(round(x)) for x in np.linspace(0, N - 1, min(SELF_SAMPLE, N))})
    self_ok = [ranked(E @ E[i])[0] == i for i in sample]
    dups = []
    if N <= 5000:
        C = E @ E.T
        iu = np.triu_indices(N, 1)
        pc = C[iu]
        for j in np.flatnonzero(pc > DUP)[:50]:
            dups.append((int(iu[0][j]), int(iu[1][j]), float(pc[j])))
        pair_med = float(np.median(pc)) if len(pc) else None
    else:
        pair_med = None
    vectors = {"norm_min": float(norms.min()), "norm_max": float(norms.max()), "max_dev": float(np.abs(norms - 1).max()),
               "self_sample": sample, "self_ok": self_ok, "dups": dups, "pair_median": pair_med}

    # 4 per question
    rows = []
    Q = unit(encode_queries(m, [q["q"] for q in qs])) if qs else np.zeros((0, setup["dim"]), np.float32)
    for qi, q in enumerate(qs):
        s = E @ Q[qi]
        order = ranked(s)
        targets = {i for i, c in enumerate(chunks) if q["expect"] and any(norm_ws(x) in c["_norm"] for x in q["expect"])}
        rows.append({**q, "top": [(order[j], float(s[order[j]])) for j in range(min(k, N))], "top1": float(s[order[0]]),
                     "median": float(np.median(s)), "targets": sorted(targets), "order": order,
                     "rank": first_hit(order, targets) if targets else None, "missing_target": bool(q["expect"]) and not targets})
    labelled = [r for r in rows if r["targets"]]

    # 5 measuring: arms
    arms = {"base": {r["id"]: r["rank"] for r in labelled}}
    overlap_k = {}
    if rerank and labelled:
        _quiet()
        from sentence_transformers import CrossEncoder
        ce = CrossEncoder(reranker, device="cpu")
        arms["rerank"] = {}
        for r in labelled:
            short = r["order"][:RERANK_N]
            sc = ce.predict([(r["q"], texts[i]) for i in short], show_progress_bar=False)
            new = [short[i] for i in np.argsort(-sc, kind="stable")] + r["order"][RERANK_N:]
            arms["rerank"][r["id"]] = first_hit(new, set(r["targets"]))
    base_top = {r["id"]: r["order"][:k] for r in rows}
    for d in dims:
        if d >= setup["dim"]:
            continue
        Ed = unit(encode_docs(m, texts, d))
        Qd = unit(encode_queries(m, [q["q"] for q in qs], d)) if qs else None
        name = f"dims {d}"
        arms[name], ov = {}, []
        for qi, r in enumerate(rows):
            o = ranked(Ed @ Qd[qi])
            ov.append(len(set(o[:k]) & set(base_top[r["id"]])) / k)
            if r["targets"]:
                arms[name][r["id"]] = first_hit(o, set(r["targets"]))
        overlap_k[name] = float(np.mean(ov)) if ov else None
    if int8 and qs:
        from sentence_transformers.util import quantize_embeddings
        rng = np.vstack((E.min(0), E.max(0)))
        E8 = quantize_embeddings(E, "int8", ranges=rng).astype(np.int32)
        Q8 = quantize_embeddings(Q, "int8", ranges=rng).astype(np.int32)
        arms["int8"], ov = {}, []
        for qi, r in enumerate(rows):
            o = ranked(E8 @ Q8[qi])
            ov.append(len(set(o[:k]) & set(base_top[r["id"]])) / k)
            if r["targets"]:
                arms["int8"][r["id"]] = first_hit(o, set(r["targets"]))
        overlap_k["int8"] = float(np.mean(ov))
    by_type = collections.defaultdict(list)
    for r in labelled:
        by_type[r["type"] or "untyped"].append(r["id"])
    measuring = {arm: {"all": metrics(list(ranks.values()), k),
                       **{t: metrics([ranks[i] for i in ids], k) for t, ids in sorted(by_type.items())}}
                 for arm, ranks in arms.items()}

    man = None
    if manifest:
        man = json.loads(Path(manifest).read_text(encoding="utf-8")) if isinstance(manifest, (str, Path)) else dict(manifest)
    res = {"docs": [{"name": d["name"], "pages": len(d["pages"]), "chars": sum(len(p) for p in d["pages"])} for d in docs],
           "settings": {"model": model, "chunker": chunker, "chunk_size": chunk_size, "overlap": overlap, "k": k, "rerank": rerank,
                        "reranker": reranker if rerank else None, "dims": list(dims), "int8": int8, "threshold": threshold,
                        "versions": {p: _version(p) for p in ("sentence-transformers", "numpy", "pymupdf")}},
           "setup": setup, "n_chunks": N, "chunks": [{"id": c["id"], "page": c["page"]} for c in chunks], "lengths": lengths,
           "vectors": vectors, "rows": [{x: v for x, v in r.items() if x != "order"} for r in rows], "n_labelled": len(labelled),
           "arms": arms, "measuring": measuring, "overlap_k": overlap_k, "manifest": man}
    res["checklist"] = checklist(res)
    res["recommendation"] = recommend(res)
    return res


def _version(p):
    try:
        return md.version(p)
    except md.PackageNotFoundError:
        return None


# ---------------------------------------------------------------------------------------------------------------- checklist
def checklist(res):
    s, L, V, rows, k = res["setup"], res["lengths"], res["vectors"], res["rows"], res["settings"]["k"]
    out = []

    def add(cid, title, verdict, evidence, how):
        out.append({"id": cid, "title": title, "verdict": verdict, "evidence": evidence, "how": how})

    n_over = len(L["over"])
    add("C1", "No chunk is longer than the model's limit", BAD if n_over else OK,
        f"{n_over} of {res['n_chunks']} chunks exceed {s['max_seq_length']} tokens" + (f" (chunks {', '.join(res['chunks'][i]['id'] for i in L['over'][:8])})" if n_over else "")
        + f"; token counts {L['min']}–{L['max']}, median {L['median']}",
        "count tokens with the model's own tokenizer; shorten chunks or pick a longer-context model")
    add("C2", "Vectors are length 1, or normalised by us", OK if V["max_dev"] < 1e-3 else BAD,
        f"lengths as returned {V['norm_min']:.6f}–{V['norm_max']:.6f}" + ("" if V["max_dev"] < 1e-3 else "; this tool normalised them before scoring, your pipeline must too"),
        "max |‖v‖ − 1| over the chunk vectors")
    man = res["manifest"]
    if man and man.get("model_id"):
        same = man["model_id"] == s["name"]
        add("C3", "Questions and chunks use the same model id", OK if same else BAD,
            f"index manifest says {man['model_id']!r}; questions here use {s['name']!r}", "store the model id with the index and compare it at query time")
    else:
        add("C3", "Questions and chunks use the same model id", ASK,
            "this tool embeds both sides with one model; pass --manifest with your index's model_id to check your own pipeline",
            "store the model id with the index and compare it at query time")
    qp = (s["prompts"] or {}).get("query", "")
    add("C4", "The question side has its label", OK if qp else ASK,
        f"model query prompt {qp!r} applied through encode_query" if qp else "the model config has no query prompt; read the model card for a query instruction or input type",
        "Cohere: input_type; sentence-transformers: encode_query / encode_document")
    add("C5", "The score direction is understood", OK if all(V["self_ok"]) else BAD,
        f"self-retrieval: {sum(V['self_ok'])} of {len(V['self_ok'])} sampled chunks rank themselves first (cosine 1)",
        "search a chunk's own text: it must come back first")
    top1 = [r["top1"] for r in rows]
    thr = res["settings"]["threshold"]
    if thr is None:
        add("C6", "No threshold copied from elsewhere", OK if rows else ASK,
            (f"no threshold given; best score per question {min(top1):.4f}–{max(top1):.4f}, median score per question "
             f"{min(r['median'] for r in rows):.4f}–{max(r['median'] for r in rows):.4f}") if rows else "no questions given",
            "compare a threshold with your own model's spread")
    else:
        inside = rows and min(top1) <= thr <= max(top1)
        add("C6", "No threshold copied from elsewhere", BAD if inside else ASK,
            f"threshold {thr} lies {'inside' if inside else 'outside'} the best-score range {min(top1):.4f}–{max(top1):.4f}" if rows else f"threshold {thr}; no questions given",
            "a cut inside the spread keeps some non-answers and drops some answers: set it on labelled data, if at all")
    add("C7", "Near-duplicate chunks are known", BAD if V["dups"] else OK,
        f"{len(V['dups'])} chunk pairs above cosine {DUP}" + (f", e.g. {res['chunks'][V['dups'][0][0]]['id']} and {res['chunks'][V['dups'][0][1]]['id']}" if V["dups"] else ""),
        "remove or merge duplicates; they waste top-k places")
    base = res["measuring"]["base"]["all"]
    nl = res["n_labelled"]
    if nl < MIN_LABELLED:
        add("C8", "The right chunk is found (labelled questions)", ASK,
            f"{nl} labelled question(s)" + (f": Hit@{k} {base['hitk']}/{nl}, MRR@10 {base['mrr']:.3f}" if base else "") + f"; fewer than {MIN_LABELLED} shows a mechanism, not a result",
            "label at least 10 questions with an expect text")
    else:
        add("C8", "The right chunk is found (labelled questions)", OK if base["hitk"] >= 0.8 * nl else BAD,
            f"Hit@{k} {base['hitk']}/{nl}, Hit@1 {base['hit1']}/{nl}, MRR@10 {base['mrr']:.3f}", "Hit@k and MRR per question type")
    if "rerank" in res["arms"]:
        up = sum(1 for q, r in res["arms"]["rerank"].items() if r == 1 and res["arms"]["base"][q] != 1)
        down = sum(1 for q, r in res["arms"]["rerank"].items() if r != 1 and res["arms"]["base"][q] == 1)
        mr = res["measuring"]["rerank"]["all"]
        add("C9", "A reranker was tried", OK, f"top-10 rerank: Hit@1 {base['hit1']} → {mr['hit1']} of {nl} ({up} questions gained rank 1, {down} lost it); MRR@10 {base['mrr']:.3f} → {mr['mrr']:.3f}",
            "rerank the bi-encoder's top 10 with a cross-encoder; compare Hit@1 and MRR")
    else:
        add("C9", "A reranker was tried", ASK, "not run (use --rerank)", "rerank the bi-encoder's top 10 with a cross-encoder")
    smaller = [a for a in res["overlap_k"]]
    if smaller:
        bad = [a for a in smaller if res["overlap_k"][a] < 0.9 or (nl and res["measuring"][a]["all"]["hitk"] < base["hitk"])]
        ev = "; ".join(f"{a}: top-{k} overlap {res['overlap_k'][a]:.2f}" + (f", Hit@{k} {res['measuring'][a]['all']['hitk']}/{nl}" if nl else "") for a in smaller)
        add("C10", "Smaller vectors were measured before use", BAD if bad else OK, ev + (f" (base Hit@{k} {base['hitk']}/{nl})" if nl else ""),
            "keep a smaller setting only if top-k overlap ≥ 0.9 and Hit@k does not drop")
    else:
        add("C10", "Smaller vectors were measured before use", ASK, "not run (use --dims 256,128 and/or --int8)", "compare against the full vectors")
    ex = [r for r in rows if (r["type"] or "").lower() in ("exact-term", "negation", "code")]
    add("C11", "Negations and exact codes were tested", ASK,
        (f"{len(ex)} question(s) typed exact-term/negation/code: ranks {[r['rank'] for r in ex]}" if ex else "no question typed exact-term, negation or code")
        + "; embeddings blur negation and rare exact strings",
        "write 2 negated and 2 code/number questions; compare with keyword search (bm25_fit_check.py)")
    add("C12", "Licence, privacy and cost are clear", ASK,
        f"model licence (model card): {s['licence'] or 'not found in the local cache'}; local model, no API cost; no text left this computer",
        "read the licence; never send private or book text to an API; count calls and tokens before an API run")
    return out


def recommend(res):
    c = {x["id"]: x["verdict"] for x in res["checklist"]}
    if c["C1"] == BAD:
        return "Shorten your chunks (or choose a longer-context model) before comparing anything: text past the limit is ignored."
    if c["C5"] == BAD:
        return "Stop: the score is being read backwards. Fix the score direction first."
    if c["C3"] == BAD:
        return "Re-embed: the questions use a different model from the index."
    if c["C2"] == BAD:
        return "Normalise both chunk and question vectors (this report did), then use dot product or cosine."
    if res["n_labelled"] < MIN_LABELLED:
        return f"Mechanism only, not enough data: label at least {MIN_LABELLED} questions with an expect text before deciding anything."
    if c["C8"] == BAD:
        return "Retrieval misses too often: inspect the per-question table, then try hybrid search (R1) or a reranker (R3)."
    if "rerank" in res["arms"]:
        up = sum(1 for q, r in res["arms"]["rerank"].items() if r == 1 and res["arms"]["base"][q] != 1)
        down = sum(1 for q, r in res["arms"]["rerank"].items() if r != 1 and res["arms"]["base"][q] == 1)
        if up - down >= 3:
            return "The reranker helps here: try R3 properly, on a frozen question set."
    if c["C10"] == OK:
        return "Setup looks sound, and the smaller vectors kept the same results here: smaller is safe on these questions."
    return "Setup looks sound. Next: add negation and exact-code questions (C11) and compare with keyword search."


# ---------------------------------------------------------------------------------------------------------------- report
def _r(x):
    return "-" if x is None else str(x)


def render_report(res):
    s, st, L, V, k = res["setup"], res["settings"], res["lengths"], res["vectors"], res["settings"]["k"]
    cl = " ".join(f"{x['id']} {x['verdict']}" for x in res["checklist"])
    out = ["# Embedding fit check", "",
           "**What this is:** an automatic check of whether an embedding setup suits these documents and questions, measured on your own chunks.",
           "**What this is not:** an evaluation. A few labelled questions show the mechanism; decide with many questions per type.", "",
           f"**Recommendation:** {res['recommendation']} (section 7). Checklist: {cl}.", "",
           f"Settings: model `{st['model']}` · chunker `{st['chunker']}` ({st['chunk_size']} characters, overlap {st['overlap']}) · k {k}"
           + (f" · rerank `{st['reranker']}`" if st["rerank"] else "") + (f" · dims {st['dims']}" if st["dims"] else "")
           + (" · int8" if st["int8"] else "") + (f" · threshold {st['threshold']}" if st["threshold"] is not None else "")
           + " · " + ", ".join(f"{p} {v}" for p, v in st["versions"].items() if v) + ". No API call.",
           "Documents: " + "; ".join(f"`{d['name']}` ({d['pages']} page(s), {d['chars']:,} characters)" for d in res["docs"]) + ".", "",
           "## 1 Setup", "", "| Field | Value | Why it matters (lesson step) |", "|---|---|---|",
           f"| Model | `{s['name']}` (snapshot {s['snapshot'] or 'unknown'}) | store it with the index (4) |",
           f"| Numbers per vector | {s['dim']} | memory: {s['dim'] * 4:,} bytes per float32 vector (10) |",
           f"| Length limit | {s['max_seq_length']} tokens | text past it is ignored (6) |",
           f"| Modules | {', '.join(s['modules'])} | |",
           f"| Pooling | {s['pooling'] or 'unknown'} | how token vectors become one vector (2) |",
           f"| Normalize module | {'yes' if s['normalize'] else 'no'} | without it, normalise yourself (3) |",
           f"| Prompts | {json.dumps(s['prompts'])} | the question side's label (7) |",
           f"| Similarity it declares | {s['similarity']} | use the one it was trained with (5) |", "",
           "## 2 Chunks vs the limit", "",
           f"{res['n_chunks']} chunks; tokens per chunk (the model's tokenizer, special tokens included): min {L['min']}, median {L['median']}, max {L['max']}. "
           f"Over the {s['max_seq_length']}-token limit: **{len(L['over'])}**. Longer than 128 tokens: {L['over_128']} (some models were trained on 128; fits is not the same as well represented).", ""]
    if L["over"]:
        out += ["| Chunk | Page | Tokens | Characters ignored |", "|---|---|---|---|"]
        for i in L["over"][:25]:
            out.append(f"| {res['chunks'][i]['id']} | {_r(res['chunks'][i]['page'])} | {L['tokens_over'][i]} | {L['ignored_chars'][i]} |")
        out.append("")
    out += ["## 3 Vectors", "",
            f"- Lengths as returned: {V['norm_min']:.6f} to {V['norm_max']:.6f} (max |‖v‖ − 1| = {V['max_dev']:.2e}). Scores below use normalised vectors (cosine).",
            f"- Self-retrieval test: {sum(V['self_ok'])} of {len(V['self_ok'])} sampled chunks ({', '.join(res['chunks'][i]['id'] for i in V['self_sample'])}) rank themselves first.",
            f"- Near-duplicates (cosine > {DUP}): {len(V['dups'])}" + ("" if not V["dups"] else ": " + ", ".join(f"{res['chunks'][a]['id']}–{res['chunks'][b]['id']} {c:.4f}" for a, b, c in V["dups"][:10])) + ".",
            f"- Chunk-against-chunk median cosine (analysis, not search): {V['pair_median']:.4f}." if V["pair_median"] is not None else "- Chunk-against-chunk analysis skipped (more than 5,000 chunks).", ""]
    rows = res["rows"]
    out += ["## 4 Per question", ""]
    if not rows:
        out += ["No questions given (use --questions).", ""]
    else:
        out += [f"| Question | Type | Best score | Median score | Top {k} (score) | Right chunk | Rank |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            top = " · ".join(f"{res['chunks'][i]['id']} {sc:.3f}" for i, sc in r["top"])
            right = ", ".join(res["chunks"][i]["id"] for i in r["targets"]) if r["targets"] else ("**expect text not found**" if r["missing_target"] else "-")
            out.append(f"| {r['id']}: {r['q'][:70]} | {r['type'] or '-'} | {r['top1']:.4f} | {r['median']:.4f} | {top} | {right} | {_r(r['rank'])} |")
        out.append("")
    out += ["## 5 Measuring", ""]
    if not res["n_labelled"]:
        out += ["No labelled questions (add an `expect` text to measure).", ""]
    else:
        out += [f"{res['n_labelled']} labelled question(s). MRR@10 counts a rank above 10 as 0.", "",
                f"| Arm | Group | n | Hit@1 | Hit@{k} | MRR@10 | Top-{k} overlap with base |", "|---|---|---|---|---|---|---|"]
        for arm, groups in res["measuring"].items():
            for g, mm in groups.items():
                if mm:
                    ov = res["overlap_k"].get(arm)
                    out.append(f"| {arm} | {g} | {mm['n']} | {mm['hit1']} | {mm['hitk']} | {mm['mrr']:.3f} | {'-' if ov is None or g != 'all' else f'{ov:.2f}'} |")
        out.append("")
    out += ["## 6 Checklist", "", "| Check | Verdict | Evidence | How to check |", "|---|---|---|---|"]
    for x in res["checklist"]:
        out.append(f"| {x['id']} {x['title']} | {x['verdict']} | {x['evidence']} | {x['how']} |")
    out += ["", "✓ fine · ✗ problem found · ? check by hand.", "", "## 7 Recommendation", "", res["recommendation"], "",
            "Lesson: `study/lessons/P4_embeddings.html`. This report is a mechanism check on your data, not an evaluation result."]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Does my embedding setup suit my documents and questions? Writes a Markdown report.")
    ap.add_argument("--docs", nargs="+", required=True, help="files or folders (.pdf, .txt, .md)")
    ap.add_argument("--questions", help=".txt (one per line) or .jsonl ({\"q\", \"expect\", \"type\", \"id\"})")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="a local sentence-transformers model")
    ap.add_argument("--chunker", choices=["v0", "windows"], default="v0", help="v0 = recursive per page (default); windows = plain")
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--rerank", action="store_true", help="rerank the top 10 with a local cross-encoder")
    ap.add_argument("--dims", default="", help="comma-separated smaller sizes to test, e.g. 256,128")
    ap.add_argument("--int8", action="store_true", help="also test int8 vectors")
    ap.add_argument("--threshold", type=float, help="a similarity threshold you plan to use (check C6)")
    ap.add_argument("--manifest", help="JSON of an existing index with a model_id (check C3)")
    ap.add_argument("--provider", choices=["local", "cohere"], default="local")
    ap.add_argument("--report", help="write the Markdown report here (default: print it)")
    a = ap.parse_args(argv)
    if a.provider == "cohere":
        print("--provider cohere is not available yet: it needs the course's study/llmops/ cache (record once, replay offline), "
              "which is not built. Never send private or book text to an API.", file=sys.stderr)
        return 2
    dims = tuple(int(x) for x in a.dims.split(",") if x.strip())
    res = run_check(a.docs, a.questions, model=a.model, chunk_size=a.chunk_size, overlap=a.overlap, chunker=a.chunker, k=a.k,
                    rerank=a.rerank, dims=dims, int8=a.int8, threshold=a.threshold, manifest=a.manifest)
    text = render_report(res)
    if a.report:
        Path(a.report).write_text(text, encoding="utf-8")
        print(f"report written: {a.report} ({res['recommendation']})")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
