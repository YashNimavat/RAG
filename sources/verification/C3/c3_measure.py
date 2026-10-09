"""C3 (embedding & indexing with metadata) measurements: every measured number in
concepts/C3_embedding_indexing.md comes from this run.

Local only: no Groq or Cohere call, no .env read. MiniLM-L6 and paraphrase-MiniLM-L3 are loaded from the
local Hugging Face cache (offline mode is forced below). Index and cache files are written to a temporary
folder that is deleted at the end; nothing is written inside the workspace.

The canonical code is executed, not re-typed: the 06 §5.3 snapshot_id recipe and the 07 H.1/H.3 chunking
code are loaded from the documents through sources/verification/corrections/contracts_check.py.

Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C3/c3_measure.py \
        "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        > sources/verification/C3/out_c3_measure.txt 2> sources/verification/C3/out_c3_measure.stderr.txt
Sections S1-S8 are deterministic. S9 (timings) depends on the machine and its load.
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import dataclasses
import hashlib
import importlib.metadata as md
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
import pymupdf

WS = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc  # noqa: E402

PDF = sys.argv[1]
L6 = "sentence-transformers/all-MiniLM-L6-v2"
L3 = "sentence-transformers/paraphrase-MiniLM-L3-v2"
SPEC_L6 = dict(provider="sentence_transformers", model_id=L6, revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
               input_type="none", preproc_version="none")
SPEC_L3 = dict(provider="sentence_transformers", model_id=L3, revision="4ca70771034acceecb2e72475f72050fcdde4ddc",
               input_type="none", preproc_version="none")
Q_D002 = "In what year was the Paris Agreement adopted?"     # 06 §6.7 draft seed (demo only)
D002_PAGE, D002_SPAN = 10, (438, 537)                       # 06 §6.7 page-relative evidence span


def head(t):
    print(f"\n=== {t}")


def fp(x):                                                  # the lab's _fp
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def file_sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# ===================================================================== given in the lab (see C1, C2)
def split_spans(text, start, end, separators, size):
    """C2 lab / 07 H.1 recursive splitter (spans only). "" = last resort: single characters."""
    if end - start <= size:
        return [(start, end)]
    if not separators or separators[0] == "":
        return [(s, s + 1) for s in range(start, end)]
    sep, rest = separators[0], separators[1:]
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
        out.extend([(a, b)] if b - a <= size else split_spans(text, a, b, rest, size))
    return out


def recursive_spans(text, size, overlap, separators):
    """Greedy merge of pieces up to `size`; the next chunk restarts with whole trailing pieces <= `overlap`."""
    if not 0 <= overlap < size:
        raise ValueError("need 0 <= overlap < size")
    if not text:
        return []
    spans, cur = [], []
    for p in split_spans(text, 0, len(text), separators, size):
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


def page_starts(pages):
    s, pos = [], 0
    for p in pages:
        s.append(pos)
        pos += len(p) + 1
    return s


def to_page_segments(a, b, starts, doc_len):
    """07 H.3 rule: page p owns its text plus the joining '\n' after it."""
    import bisect
    segs = []
    for p in range(bisect.bisect_right(starts, a), bisect.bisect_right(starts, b - 1) + 1):
        lo = starts[p - 1]
        hi = starts[p] if p < len(starts) else doc_len
        segs.append({"page": p, "char_start": max(a, lo) - lo, "char_end": min(b, hi) - lo})
    return segs


def make_chunks(doc_id, snapshot_id, pages, cfg, params_hash_fn):
    """06 §2.3 Chunk records (dicts, 06 key order) from the v0 recursive_char chunker. Given in the lab, 'see C2'."""
    if cfg["name"] != "recursive_char" or cfg["unit"] != "chars":
        raise NotImplementedError("this given chunker only does recursive_char in characters")
    full, starts = "\n".join(pages), page_starts(pages)
    size, ov, seps = cfg["chunk_size"], cfg["chunk_overlap"], cfg["separators"]
    if cfg["scope"] == "per_page":
        spans = [(starts[i] + a, starts[i] + b) for i, p in enumerate(pages) for a, b in recursive_spans(p, size, ov, seps)]
    elif cfg["scope"] == "cross_page":
        spans = recursive_spans(full, size, ov, seps)
    else:
        raise ValueError(cfg["scope"])
    h = params_hash_fn(cfg)
    return [{"doc_id": doc_id, "snapshot_id": snapshot_id, "chunk_id": f"{doc_id}:{snapshot_id}:{h}:{seq:05d}",
             "seq": seq, "char_start": a, "char_end": b, "page_segments": to_page_segments(a, b, starts, len(full)),
             "text": full[a:b], "text_sha256": sha(full[a:b]), "chunker": cfg["name"], "params_hash": h, "meta": {}}
            for seq, (a, b) in enumerate(spans)]


# 06 §2.4 `chunking:` block, exactly (course-wide interface decision; C2 lab PARAMS)
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
C2_JSONL_SHA256 = "d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b"   # C2LAB_FACTS (Save row)


# ===================================================================== what the learner writes (reference)
def params_hash(cfg: dict) -> str:
    """Course recipe (C2 lab): sha256 of the sorted-key JSON of the 06 §2.4 chunking block, first 12 hex."""
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode("utf-8")).hexdigest()[:12]


EMBED_FIELDS = ("provider", "model_id", "revision", "input_type", "normalize", "preproc_version")


def embed_hash(embedding: dict) -> str:
    """Course decision 2026-10-08: the manifest's embedding block without the measured dim and max_seq_length."""
    return hashlib.sha256(json.dumps({k: embedding[k] for k in EMBED_FIELDS}, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def embedding_cache_key(text, *, provider, model_id, revision, input_type, preproc_version):
    """06 §2.4: sha256(provider|model_id|revision|input_type|preproc_version|text)."""
    meta = [provider, model_id, str(revision), input_type, preproc_version]
    if any("|" in f for f in meta):
        raise ValueError("'|' is reserved as the field separator")
    return sha("|".join(meta + [text]))


class Counting:
    """Wraps a SentenceTransformer: counts texts actually sent to the model."""
    def __init__(self, model):
        self.model, self.n_texts, self.n_calls = model, 0, 0

    def __call__(self, texts):
        self.n_texts += len(texts)
        self.n_calls += 1
        return self.model.encode(list(texts), normalize_embeddings=False, convert_to_numpy=True).astype(np.float32)


def cached_embed(texts, spec, encode, cache_dir):
    """Content-keyed cache of RAW provider vectors; returns L2-normalised float32 rows and hit/miss counts."""
    cache_dir = pathlib.Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    keys = [embedding_cache_key(t, **spec) for t in texts]
    found = {k: np.load(cache_dir / f"{k}.npy", allow_pickle=False) for k in set(keys)
             if (cache_dir / f"{k}.npy").exists()}
    missing = list(dict.fromkeys(k for k in keys if k not in found))      # unique, in order
    if missing:
        first = {k: texts[keys.index(k)] for k in missing}
        new = encode([first[k] for k in missing])
        for k, v in zip(missing, new):
            v = np.asarray(v, dtype=np.float32)
            np.save(cache_dir / f"{k}.npy", v)
            found[k] = v
    raw = np.stack([found[k] for k in keys]).astype(np.float32)
    V = (raw / np.linalg.norm(raw, axis=1, keepdims=True)).astype(np.float32)
    n_miss = sum(k in set(missing) for k in keys)
    return V, {"hits": len(texts) - n_miss, "misses": n_miss}


REBUILD_EMBED_FIELDS = ("provider", "model_id", "revision", "preproc_version", "normalize")


def rebuild_reasons(manifest: dict, run_cfg: dict) -> list:
    """Which parts of the run config are incompatible with this index. [] means: reuse the index."""
    r = []
    if manifest["snapshot_id"] != run_cfg["snapshot_id"]:
        r.append("snapshot")
    if manifest["params_hash"] != params_hash(run_cfg["chunker"]):
        r.append("chunker")
    me, we = manifest["embedding"], run_cfg["embedding"]
    if any(me[f] != we[f] for f in REBUILD_EMBED_FIELDS) or me["input_type"]["documents"] != we["input_type"]["documents"]:
        r.append("embedding")
    return r


def write_index(index_dir, chunks, V, manifest):
    index_dir = pathlib.Path(index_dir)
    if (index_dir / "manifest.json").exists():
        old = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
        if rebuild_reasons(old, {"snapshot_id": manifest["snapshot_id"], "chunker": manifest["chunker"],
                                 "embedding": manifest["embedding"]}):
            raise FileExistsError(f"{index_dir} holds a different index; never overwrite in place")
    index_dir.mkdir(parents=True, exist_ok=True)
    np.save(index_dir / "vectors.npy", V.astype(np.float32))
    with open(index_dir / "chunks.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    m = dict(manifest)
    m["files"] = {"vectors.npy": {"sha256": file_sha(index_dir / "vectors.npy"), "shape": list(V.shape),
                                  "dtype": "float32"},
                  "chunks.jsonl": {"sha256": file_sha(index_dir / "chunks.jsonl"), "lines": len(chunks)}}
    (index_dir / "manifest.json").write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    return m


class IndexMismatch(ValueError):
    pass


CHUNK_ID_RE = re.compile(r"^[^:]+:[0-9a-f]{12}:[0-9a-f]{12}:\d{5}$")


def load_index(index_dir, run_cfg):
    """Fail closed: every problem raises IndexMismatch with the list of reasons."""
    index_dir = pathlib.Path(index_dir)
    m = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
    probs = []
    for name in ("vectors.npy", "chunks.jsonl"):
        if file_sha(index_dir / name) != m["files"][name]["sha256"]:
            probs.append(f"{name} sha256 differs from the manifest")
    V = np.load(index_dir / "vectors.npy", allow_pickle=False)
    lines = (index_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    chunks = [json.loads(x) for x in lines]
    if V.dtype != np.float32 or list(V.shape) != m["files"]["vectors.npy"]["shape"]:
        probs.append("vectors dtype/shape")
    if len(V) != len(chunks):
        probs.append(f"{len(V)} vectors but {len(chunks)} chunk lines")
    if not np.allclose(np.linalg.norm(V, axis=1), 1.0, atol=1e-5):
        probs.append("rows are not unit length")
    for i, c in enumerate(chunks):
        if (c["params_hash"] != m["params_hash"] or c["snapshot_id"] != m["snapshot_id"]
                or not CHUNK_ID_RE.match(c["chunk_id"]) or sha(c["text"]) != c["text_sha256"]):
            probs.append(f"chunk line {i} inconsistent")
            break
    if m.get("embed_hash") != embed_hash(m["embedding"]) or m["params_hash"] != params_hash(m["chunker"]):
        probs.append("manifest hashes do not match its own chunker/embedding blocks")
    probs += [f"rebuild needed: {r}" for r in rebuild_reasons(m, run_cfg)]
    if probs:
        raise IndexMismatch(probs)
    return V, chunks, m


def top_k(scores, k):
    """P5 rule: exact, ties broken by the smaller row id."""
    cand = np.flatnonzero(scores >= np.partition(scores, -k)[-k])
    order = np.lexsort((cand, -scores[cand]))
    return cand[order][:k]


# ===================================================================== run
def main():
    md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
    md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
    cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
    core, chunking, _ = cc.load_07_modules(md07)
    PARSER = {"backend": "pymupdf", "version": pymupdf.VersionBind, "call": "page.get_text()", "options": {}}

    def snapshot_id_of(pages_by_doc):
        return cc.snapshot_id_06(PARSER, cc.CLEANING_NONE, {d: sha("\n".join(p)) for d, p in pages_by_doc.items()})

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="c3_measure_"))
    try:
        # ------------------------------------------------------------------ S1
        head("S1 environment, snapshot and chunk records")
        vers = {k: md.version(k) for k in ("pymupdf", "numpy", "sentence-transformers", "torch", "transformers")}
        print("python", platform.python_version(), "|", vers)
        print("platform", platform.platform(), "| cpu_count", os.cpu_count())
        pdf_bytes = pathlib.Path(PDF).read_bytes()
        print("pdf sha256", hashlib.sha256(pdf_bytes).hexdigest(), "bytes", len(pdf_bytes))
        pages = [p.get_text() for p in pymupdf.open(PDF)]
        full = "\n".join(pages)
        SNAP = snapshot_id_of({"climate": pages})
        print(f"pages={len(pages)} doc chars={len(full)} doc_text_sha256={sha(full)}")
        print(f"snapshot_id (06 §5.3 recipe executed from the document) = {SNAP}  (06 states ea07572562ac: "
              f"{'MATCH' if SNAP == 'ea07572562ac' else 'MISMATCH'})")
        empty_pages = [i + 1 for i, p in enumerate(pages) if not p]
        print("empty pages:", empty_pages, "| page lengths min/max:", min(map(len, pages)), max(map(len, pages)))
        CFG = dict(CHUNKING)
        print("chunker config = 06 §2.4 chunking block:", json.dumps(CFG))
        print("params_hash (sha256 of json.dumps(cfg, sort_keys=True), first 12 hex) =", params_hash(CFG))
        chunks = make_chunks("climate", SNAP, pages, CFG, params_hash)
        n = len(chunks)
        jsonl = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")
        print(f"lab given chunker, per_page recursive_char 1000/200: {n} chunks; chunks.jsonl {len(jsonl)} bytes, sha256 "
              f"{hashlib.sha256(jsonl).hexdigest()}; equals the C2 lab's v0 output (C2LAB_FACTS): "
              f"{hashlib.sha256(jsonl).hexdigest() == C2_JSONL_SHA256}")
        ref = chunking.chunk_document("climate", SNAP, pages, chunking.ChunkerConfig(name="recursive", size=1000, overlap=200))
        same = sum(c["char_start"] == r.char_start and c["char_end"] == r.char_end and c["text"] == r.text
                   and c["text_sha256"] == r.text_sha256
                   and [(x["page"], x["char_start"], x["char_end"]) for x in c["page_segments"]]
                   == [(x.page, x.char_start, x.char_end) for x in r.page_segments] for c, r in zip(chunks, ref))
        print(f"same spans/text/text_sha256/page_segments as 07 H.3 chunk_document(recursive, 1000/200): {same}/{len(ref)} "
              f"(07's own ids use params_hash {chunking.ChunkerConfig(name='recursive', size=1000, overlap=200).params_hash()}: "
              f"07 field names, not the course recipe)")
        print("multi-segment chunks:", sum(len(c["page_segments"]) > 1 for c in chunks),
              "| text == doc_text[char_start:char_end]:", sum(full[c["char_start"]:c["char_end"]] == c["text"] for c in chunks), "/", n)
        lens = [len(c["text"]) for c in chunks]
        print("chunk lengths min/max:", min(lens), max(lens), "| chunks per page fingerprint",
              fp([c["page_segments"][0]["page"] for c in chunks]))
        print("first chunk_id:", chunks[0]["chunk_id"], "| last:", chunks[-1]["chunk_id"])
        print("duplicate chunk texts:", n - len({c["text"] for c in chunks}))
        rec = dict(chunks[0])
        rec["text"] = rec["text"][:40] + "…"
        print("first record (text cut to 40 chars):", json.dumps(rec, ensure_ascii=False))

        # ------------------------------------------------------------------ S2
        head("S2 params_hash: determinism and sensitivity")
        again = make_chunks("climate", SNAP, pages, dict(CFG), params_hash)
        print("rebuild with the same inputs: same params_hash", params_hash(CFG) == again[0]["params_hash"],
              "| same chunk ids", sum(a["chunk_id"] == b["chunk_id"] for a, b in zip(chunks, again)), "/", n)
        code = ("import hashlib,json;c=json.loads(%r);print(hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12], hash(json.dumps(c,sort_keys=True)))"
                % json.dumps(CFG))
        outs = []
        for seed in ("1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            outs.append(subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env).stdout.split())
        print("two fresh processes (PYTHONHASHSEED=1, 2): sha256 recipe", outs[0][0], outs[1][0],
              "| builtin hash()", outs[0][1], outs[1][1], "-> equal:", outs[0][1] == outs[1][1])
        changes = {"name recursive_char->recursive": {"name": "recursive"}, "chunk_size 1000->500": {"chunk_size": 500},
                   "chunk_size 1000->1001": {"chunk_size": 1001}, "chunk_overlap 200->100": {"chunk_overlap": 100},
                   "unit chars->tokens": {"unit": "tokens"}, "scope per_page->cross_page": {"scope": "cross_page"},
                   "separators drop \"\"": {"separators": ["\n\n", "\n", " "]}}
        hashes = {params_hash(CFG)}
        for label, ch in changes.items():
            h = params_hash({**CFG, **ch})
            print(f"  {label:28s} params_hash {h}  differs: {h != params_hash(CFG)}")
            hashes.add(h)
        print("distinct hashes over the 8 configs:", len(hashes))
        reordered = dict(reversed(list(CFG.items())))
        h_unsorted = lambda c: hashlib.sha256(json.dumps(c).encode()).hexdigest()[:12]
        print("same config, keys in reverse order: sort_keys=True", params_hash(CFG) == params_hash(reordered),
              "| without sort_keys", h_unsorted(CFG) == h_unsorted(reordered), f"({h_unsorted(CFG)} vs {h_unsorted(reordered)})")
        print("chunk_size as string '1000' vs int 1000: hashes equal?", params_hash({**CFG, "chunk_size": "1000"}) == params_hash(CFG))
        broken = lambda c: hashlib.sha256(json.dumps({"chunk_size": c["chunk_size"], "chunk_overlap": c["chunk_overlap"]}, sort_keys=True).encode()).hexdigest()[:12]
        pp = make_chunks("climate", SNAP, pages, CFG, broken)
        cp = make_chunks("climate", SNAP, pages, {**CFG, "scope": "cross_page"}, broken)
        ids_pp = {c["chunk_id"]: c for c in pp}
        coll = [c for c in cp if c["chunk_id"] in ids_pp]
        diff = sum(ids_pp[c["chunk_id"]]["text"] != c["text"] for c in coll)
        print(f"BROKEN hash (chunk_size+chunk_overlap only): per_page {len(pp)} chunks, cross_page {len(cp)} chunks, same hash "
              f"{broken(CFG) == broken({**CFG, 'scope': 'cross_page'})}; {len(coll)} chunk ids shared, {diff} of them "
              f"name different text")
        cp_ok = make_chunks("climate", SNAP, pages, {**CFG, "scope": "cross_page"}, params_hash)
        print("correct hash: shared ids per_page vs cross_page:", len({c["chunk_id"] for c in cp_ok} & {c["chunk_id"] for c in chunks}))

        # ------------------------------------------------------------------ S3
        head("S3 embedding cache key")
        k0 = embedding_cache_key("hello|world", **SPEC_L6)
        k07 = chunking.embedding_cache_key("hello|world", provider=SPEC_L6["provider"], model_id=SPEC_L6["model_id"],
                                           model_revision=SPEC_L6["revision"], input_type=SPEC_L6["input_type"],
                                           preprocessing_version=SPEC_L6["preproc_version"])
        print("key('hello|world', L6 spec) =", k0[:16] + "…", "| equals 07 H.3 embedding_cache_key:", k0 == k07)
        for f, v in [("provider", "cohere"), ("model_id", L3), ("revision", "other"), ("input_type", "search_query"),
                     ("preproc_version", "tabs_to_spaces")]:
            print(f"  change {f:15s} -> key differs: {embedding_cache_key('hello|world', **{**SPEC_L6, f: v}) != k0}")
        print("  change text by one char -> key differs:", embedding_cache_key("hello|worle", **SPEC_L6) != k0)
        try:
            embedding_cache_key("x", **{**SPEC_L6, "model_id": "a|b"})
            print("  '|' in a meta field: accepted (BAD)")
        except ValueError:
            print("  '|' in a meta field: ValueError (fields are unambiguous; text is last so it may contain '|')")
        ambiguous = sha("|".join(["a", "b|c", "d", "e", "f", "t"])) == sha("|".join(["a|b", "c", "d", "e", "f", "t"]))
        print("  without that guard, ('a','b|c',...) and ('a|b','c',...) give the same key:", ambiguous)

        # ------------------------------------------------------------------ S4
        head("S4 embeddings, cache hits/misses, edits, model switch")
        from sentence_transformers import SentenceTransformer
        m6 = SentenceTransformer(L6, device="cpu")
        m3 = SentenceTransformer(L3, device="cpu")
        print("L6 modules", [type(x).__name__ for x in m6], "max_seq_length", m6.max_seq_length,
              "| L3 modules", [type(x).__name__ for x in m3], "max_seq_length", m3.max_seq_length)
        texts = [c["text"] for c in chunks]
        cache = tmp / "emb"
        enc6 = Counting(m6)
        V, st1 = cached_embed(texts, SPEC_L6, enc6, cache)
        print(f"build 1: {st1} texts sent to model {enc6.n_texts} in {enc6.n_calls} call(s); V {V.shape} {V.dtype}")
        enc6b = Counting(m6)
        V2, st2 = cached_embed(texts, SPEC_L6, enc6b, cache)
        print(f"build 2 (same texts): {st2} texts sent to model {enc6b.n_texts}; V identical: {np.array_equal(V, V2)}")
        print("cache files:", len(list(cache.glob('*.npy'))), "| bytes per cached vector file:",
              (cache / f"{embedding_cache_key(texts[0], **SPEC_L6)}.npy").stat().st_size)
        raw6 = np.stack([np.load(cache / f"{embedding_cache_key(t, **SPEC_L6)}.npy") for t in texts])
        print(f"L6 raw norms min/max {np.linalg.norm(raw6, axis=1).min():.6f}/{np.linalg.norm(raw6, axis=1).max():.6f};"
              f" stored V max|norm-1| {np.abs(np.linalg.norm(V, axis=1) - 1).max():.2e}")
        # edit page 10: insert 9 characters at page offset 100
        ins = " (edited)"
        pages_e = list(pages)
        pages_e[9] = pages[9][:100] + ins + pages[9][100:]
        SNAP_E = snapshot_id_of({"climate": pages_e})
        ch_e = make_chunks("climate", SNAP_E, pages_e, CFG, params_hash)
        enc = Counting(m6)
        _, st_e = cached_embed([c["text"] for c in ch_e], SPEC_L6, enc, cache)
        old_ids = {c["chunk_id"] for c in chunks}
        p10 = sum(c["page_segments"][0]["page"] == 10 for c in chunks)
        print(f"EDIT page 10 (+{len(ins)} chars at page offset 100): new snapshot_id {SNAP_E}; chunks {len(ch_e)} "
              f"(page 10 had {p10}); chunk ids unchanged {len({c['chunk_id'] for c in ch_e} & old_ids)}/{len(ch_e)}; "
              f"cache {st_e}; texts sent {enc.n_texts}")
        # same edit, cross-page windows (cache primed with the cross-page original)
        cfg_x = {**CFG, "scope": "cross_page"}
        cx = make_chunks("climate", SNAP, pages, cfg_x, params_hash)
        _, _ = cached_embed([c["text"] for c in cx], SPEC_L6, Counting(m6), cache)
        cx_e = make_chunks("climate", SNAP_E, pages_e, cfg_x, params_hash)
        enc = Counting(m6)
        _, st_xe = cached_embed([c["text"] for c in cx_e], SPEC_L6, enc, cache)
        print(f"same edit, cross_page windows: {len(cx)} -> {len(cx_e)} chunks; cache {st_xe}")
        pages_s = list(pages)
        pages_s[9] = pages[9][:100] + ("X" if pages[9][100] != "X" else "Y") + pages[9][101:]
        cx_s = make_chunks("climate", snapshot_id_of({"climate": pages_s}), pages_s, cfg_x, params_hash)
        _, st_xs = cached_embed([c["text"] for c in cx_s], SPEC_L6, Counting(m6), cache)
        print(f"same-length edit (1 char replaced) cross_page: cache {st_xs}")
        # contrast: plain fixed windows across pages (07 H.1/H.3 'fixed', cross_page): an insertion shifts every later window
        fx = chunking.ChunkerConfig(name="fixed", size=1000, overlap=200, scope="cross_page")
        fx0 = [c.text for c in chunking.chunk_document("climate", SNAP, pages, fx)]
        fx1 = [c.text for c in chunking.chunk_document("climate", SNAP_E, pages_e, fx)]
        _, _ = cached_embed(fx0, SPEC_L6, Counting(m6), cache)
        _, st_fx = cached_embed(fx1, SPEC_L6, Counting(m6), cache)
        print(f"same edit, FIXED 1000/200 windows across pages (07 'fixed', contrast only): {len(fx0)} -> {len(fx1)} chunks; cache {st_fx}")
        # switch model: correct key vs text-only key
        enc3 = Counting(m3)
        V3, st3 = cached_embed(texts, SPEC_L3, enc3, cache)
        print(f"switch to L3 with the full key: {st3}; texts sent {enc3.n_texts}")
        text_only = {}
        for t, v in zip(texts, raw6):
            text_only[sha(t)] = v
        hits = sum(sha(t) in text_only for t in texts)
        stale = np.stack([text_only[sha(t)] for t in texts])
        print(f"BROKEN text-only key, switch to L3: hits {hits}/{n}; served vectors == L6 vectors: "
              f"{np.array_equal(stale, raw6)}; shape {stale.shape} (L3 dim is also {V3.shape[1]}: no error)")
        # D-002 evidence chunk and ranks
        ev_a = page_starts(pages)[D002_PAGE - 1] + D002_SPAN[0]
        ev_b = page_starts(pages)[D002_PAGE - 1] + D002_SPAN[1]
        ev = [i for i, c in enumerate(chunks) if c["char_start"] <= ev_a and ev_b <= c["char_end"]]
        q6 = m6.encode([Q_D002], normalize_embeddings=True)[0]
        q3 = m3.encode([Q_D002], normalize_embeddings=True)[0]
        s_ok = V @ q6
        order_ok = list(top_k(s_ok, n))
        s_bad = (stale / np.linalg.norm(stale, axis=1, keepdims=True)) @ q3
        order_bad = list(top_k(s_bad, n))
        print(f"D-002 evidence span doc [{ev_a},{ev_b}) lies whole in chunk rows {ev} "
              f"({[chunks[i]['seq'] for i in ev]}); rank with correct index {[order_ok.index(i) + 1 for i in ev]}; "
              f"rank with stale L6 vectors + L3 query {[order_bad.index(i) + 1 for i in ev]}")
        # batch-size determinism
        a = m6.encode(texts, batch_size=64, normalize_embeddings=False)
        b = m6.encode(texts, batch_size=64, normalize_embeddings=False)
        c1 = m6.encode(texts, batch_size=1, normalize_embeddings=False)
        print(f"two encodes, batch 64: bit-identical {np.array_equal(a, b)}; batch 64 vs batch 1: bit-identical "
              f"{np.array_equal(a, c1)}, rows bit-identical {int((a == c1).all(axis=1).sum())}/{n}, max abs diff {np.abs(a - c1).max():.2e}")

        # ------------------------------------------------------------------ S5
        head("S5 normalisation at index time (L3 has no Normalize module)")
        raw3 = m3.encode(texts, normalize_embeddings=False)
        nr = np.linalg.norm(raw3, axis=1)
        print(f"L3 raw norms min/max {nr.min():.4f}/{nr.max():.4f}; after cached_embed max|norm-1| "
              f"{np.abs(np.linalg.norm(V3, axis=1) - 1).max():.2e}")
        heads = [p[:200] for p in pages if p.strip()]
        Q3 = m3.encode(heads + [Q_D002], normalize_embeddings=True)
        same_top4 = sum(list(top_k(raw3 @ q, 4)) == list(top_k(V3 @ q, 4)) for q in Q3)
        same_top1 = sum(int(top_k(raw3 @ q, 1)[0]) == int(top_k(V3 @ q, 1)[0]) for q in Q3)
        print(f"L3 index stored UNnormalised vs normalised, {len(Q3)} queries (33 page heads + D-002): top-4 identical "
              f"{same_top4}/{len(Q3)}, top-1 identical {same_top1}/{len(Q3)}")
        print("D-002 top-4 rows: unnormalised", [int(i) for i in top_k(raw3 @ Q3[-1], 4)], "normalised",
              [int(i) for i in top_k(V3 @ Q3[-1], 4)])

        # ------------------------------------------------------------------ S6
        head("S6 the three index files")
        EMB = {"provider": "sentence_transformers", "model_id": L6, "revision": SPEC_L6["revision"],
               "input_type": {"documents": "none", "queries": "none"}, "preproc_version": "none", "normalize": True,
               "dim": int(V.shape[1]), "max_seq_length": int(m6.max_seq_length)}
        base = {"snapshot_id": SNAP,
                "docs": [{"doc_id": "climate", "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
                          "doc_text_sha256": sha(full)}],
                "parser": {"backend": "pymupdf", "version": pymupdf.VersionBind},
                "chunker": CFG, "params_hash": params_hash(CFG), "embedding": EMB, "embed_hash": embed_hash(EMB),
                "library_versions": {"numpy": vers["numpy"], "sentence-transformers": vers["sentence-transformers"],
                                     "torch": vers["torch"]},
                "created_utc": "2026-10-08T00:00:00Z"}
        RUN = {"snapshot_id": SNAP, "chunker": CFG, "embedding": EMB, "retrieval": {"k": 4},
               "generation": {"provider": "groq", "model_id": "${GROQ_MODEL_ID}", "temperature": 0.0},
               "rerank": None, "prompt_version": "answer_v1"}
        EH = embed_hash(EMB)
        idx = tmp / "index" / SNAP / params_hash(CFG) / EH
        man = write_index(idx, chunks, V, base)
        sizes = {p.name: p.stat().st_size for p in idx.iterdir()}
        print("index dir: index/<snapshot_id>/<params_hash>/<embed_hash>/ =", f"index/{SNAP}/{params_hash(CFG)}/{EH}/")
        emb3 = {**EMB, "model_id": L3, "revision": SPEC_L3["revision"]}
        print("embed_hash L6", EH, "| L3", embed_hash(emb3), "| dim changed only", embed_hash({**EMB, "dim": 999}) == EH,
              "| query input_type changed", embed_hash({**EMB, "input_type": {"documents": "none", "queries": "search_query"}}),
              "| normalize False", embed_hash({**EMB, "normalize": False}))
        idx3 = tmp / "index" / SNAP / params_hash(CFG) / embed_hash(emb3)
        V3n, _ = cached_embed(texts, SPEC_L3, Counting(m3), cache)
        write_index(idx3, chunks, V3n, {**base, "embedding": {**emb3, "max_seq_length": int(m3.max_seq_length)},
                                        "embed_hash": embed_hash(emb3)})
        print("L6 and L3 indexes side by side under one params_hash:",
              sorted(p.name for p in (tmp / "index" / SNAP / params_hash(CFG)).iterdir()), "| L6 files unchanged:",
              file_sha(idx / "vectors.npy") == man["files"]["vectors.npy"]["sha256"])
        try:
            write_index(idx, chunks, V3n, {**base, "embedding": emb3, "embed_hash": embed_hash(emb3)})
            print("overwrite guard: L3 manifest written into the L6 folder (BAD)")
        except FileExistsError:
            print("overwrite guard: writing the L3 index into the L6 folder raises FileExistsError")
        print("file sizes (bytes):", sizes, "| vectors.npy = 128-byte header + n*d*4 =", 128 + n * 384 * 4)
        print("chunks.jsonl mean bytes per line:", round(sizes["chunks.jsonl"] / n, 1))
        print("manifest.json sha256 (a trace's index_manifest_hash):", file_sha(idx / "manifest.json"))
        mm = json.loads((idx / "manifest.json").read_text(encoding="utf-8"))
        mm["files"]["vectors.npy"]["sha256"] = mm["files"]["vectors.npy"]["sha256"][:12] + "…"
        mm["files"]["chunks.jsonl"]["sha256"] = mm["files"]["chunks.jsonl"]["sha256"][:12] + "…"
        mm["docs"][0]["pdf_sha256"] = mm["docs"][0]["pdf_sha256"][:12] + "…"
        mm["docs"][0]["doc_text_sha256"] = mm["docs"][0]["doc_text_sha256"][:12] + "…"
        print("manifest.json (hashes cut):", json.dumps(mm, ensure_ascii=False))
        Vl, cl, ml = load_index(idx, RUN)
        print("round trip: vectors equal", np.array_equal(Vl, V), "| chunks equal", cl == chunks,
              "| text == doc_text slice", sum(full[c["char_start"]:c["char_end"]] == c["text"] for c in cl), "/", n)
        qv = m6.encode([Q_D002], normalize_embeddings=True)[0].astype(np.float32)
        sc = Vl @ qv
        top5 = sorted(range(n), key=lambda i: (-float(sc[i]), cl[i]["chunk_id"]))[:5]
        print("C4-side smoke test, D-002 top-5 (line in chunks.jsonl, page, score):",
              [(i, cl[i]["page_segments"][0]["page"], round(float(sc[i]), 4)) for i in top5])
        # rebuild from cache: byte-identical files?
        idx2 = tmp / "index2"
        V_again, st_again = cached_embed(texts, SPEC_L6, Counting(m6), cache)
        write_index(idx2, again, V_again, base)
        print("rebuild from the cache into a new dir: vectors.npy identical", file_sha(idx2 / "vectors.npy") == file_sha(idx / "vectors.npy"),
              "| chunks.jsonl identical", file_sha(idx2 / "chunks.jsonl") == file_sha(idx / "chunks.jsonl"),
              "| manifest.json identical", file_sha(idx2 / "manifest.json") == file_sha(idx / "manifest.json"), "| cache", st_again)
        print("Cohere embed-v4.0 (1,536 dims, O2 report): vectors.npy would be 128 + n*1536*4 =", 128 + n * 1536 * 4,
              "bytes (derived)")
        # repo pattern: context_enrichment_window_around_chunk.ipynb cell 13 (re-implemented, plain Python)
        content = "".join(pages)                                   # helper_functions.read_pdf_to_string: no join char
        starts_ce, s0 = [], 0
        while s0 < len(content):
            starts_ce.append(s0)
            s0 += 400 - 200
        meta_chars = len(starts_ce) * len(content)
        print(f"repo cell-13 pattern on the same PDF (400/200, metadata={{'index', 'text': whole document}}): "
              f"{len(starts_ce)} chunks x {len(content)} chars = {meta_chars:,} metadata chars "
              f"(our chunks.jsonl: {sizes['chunks.jsonl']:,} bytes for {n} chunks)")

        # ------------------------------------------------------------------ S7
        head("S7 the manifest gate and the rebuild decision")
        scen = {
            "nothing changed": {},
            "k 4 -> 8": {"retrieval": {"k": 8}},
            "LLM model changed": {"generation": {"provider": "groq", "model_id": "other", "temperature": 0.0}},
            "prompt answer_v1 -> v2": {"prompt_version": "answer_v2"},
            "reranker added": {"rerank": {"name": "cross_encoder"}},
            "query input_type changed": {"embedding": {**EMB, "input_type": {"documents": "none", "queries": "search_query"}}},
            "chunk size 1000 -> 2000": {"chunker": {**CFG, "chunk_size": 2000}},
            "overlap 200 -> 100": {"chunker": {**CFG, "chunk_overlap": 100}},
            "scope per_page -> cross_page": {"chunker": {**CFG, "scope": "cross_page"}},
            "PDF text changed (new snapshot)": {"snapshot_id": SNAP_E},
            "embedding model L6 -> L3": {"embedding": {**EMB, "model_id": L3, "revision": SPEC_L3["revision"]}},
            "same model, new revision": {"embedding": {**EMB, "revision": "0000000"}},
            "document input_type changed": {"embedding": {**EMB, "input_type": {"documents": "search_document", "queries": "none"}}},
            "preprocessing (tabs->spaces) added": {"embedding": {**EMB, "preproc_version": "tabs_to_spaces"}},
            "normalize true -> false": {"embedding": {**EMB, "normalize": False}},
            "new snapshot AND new model": {"snapshot_id": SNAP_E, "embedding": {**EMB, "model_id": L3, "revision": SPEC_L3["revision"]}},
        }
        results = {}
        for label, ch in scen.items():
            r = rebuild_reasons(man, {**RUN, **ch})
            results[label] = r
            print(f"  {label:36s} -> {r if r else 'reuse the index'}")
        print("scenario results fingerprint:", fp([results[k] for k in scen]))
        # load_index refusals
        bad_dir = tmp / "bad"
        shutil.copytree(idx, bad_dir)
        lines = (bad_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        (bad_dir / "chunks.jsonl").write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
        for label, d, cfg in [("chunks.jsonl lost its first line", bad_dir, RUN),
                              ("config asks for 2000/400", idx, {**RUN, "chunker": {**CFG, "chunk_size": 2000, "chunk_overlap": 400}}),
                              ("config asks for L3", idx, {**RUN, "embedding": {**EMB, "model_id": L3, "revision": SPEC_L3["revision"]}})]:
            try:
                load_index(d, cfg)
                print(f"  load_index [{label}]: LOADED (BAD)")
            except IndexMismatch as e:
                print(f"  load_index [{label}]: refused -> {e.args[0]}")
        # repo pattern: hierarchical_indices.ipynb cell 13 'if the folder exists, load it'
        stale_dir = tmp / "vector_stores" / "detailed_store"
        write_index(stale_dir, chunks, V, base)
        cfg500 = {**CFG, "chunk_size": 500, "chunk_overlap": 100}
        n500 = len(make_chunks("climate", SNAP, pages, cfg500, params_hash))
        loaded = len((stale_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()) if stale_dir.exists() else 0
        print(f"'exists -> load' pattern after changing the config to 500/100: loads {loaded} chunks built at 1000/200 "
              f"(500/100 would give {n500}); no error. Manifest gate: {rebuild_reasons(man, {**RUN, 'chunker': cfg500})}")

        # ------------------------------------------------------------------ S8
        head("S8 CR-08 probe: chunk size doubles (1000/200 -> 2000/400), and the token ceiling")
        tok = m6.tokenizer
        ntok = lambda t: len(tok(t)["input_ids"])
        CFG2 = {**CFG, "chunk_size": 2000, "chunk_overlap": 400}
        ch2 = make_chunks("climate", SNAP, pages, CFG2, params_hash)
        enc = Counting(m6)
        _, st_2 = cached_embed([c["text"] for c in ch2], SPEC_L6, enc, cache)
        t1 = [ntok(c["text"]) for c in chunks]
        t2 = [ntok(c["text"]) for c in ch2]
        print(f"1000/200: {n} chunks, model tokens max {max(t1)}, > {m6.max_seq_length}: {sum(x > m6.max_seq_length for x in t1)}")
        print(f"2000/400: {len(ch2)} chunks, params_hash {params_hash(CFG2)}, chunk ids shared with 1000/200: "
              f"{len({c['chunk_id'] for c in ch2} & old_ids)}; model tokens max {max(t2)}, > {m6.max_seq_length}: "
              f"{sum(x > m6.max_seq_length for x in t2)}; cache after the 1000/200 build: {st_2}")
        print("pages <= 1000 chars (one identical chunk under both configs):", sum(1 for p in pages if 0 < len(p) <= 1000))
        texts1 = {c["text"] for c in chunks}
        shared = [c for c in ch2 if c["text"] in texts1]
        whole = sum(c["page_segments"][0]["char_start"] == 0 and c["page_segments"][0]["char_end"] == len(pages[c["page_segments"][0]["page"] - 1]) for c in shared)
        print(f"2000/400 chunks whose text equals a 1000/200 chunk: {len(shared)} (whole pages: {whole}; other: {len(shared) - whole}); "
              f"pages > 2000 chars: {sum(len(p) > 2000 for p in pages)}; longest page {max(map(len, pages))}")
        print(f"vectors.npy at 2000/400: {128 + len(ch2) * 384 * 4} bytes (derived from n*d*4 + 128)")

        # ------------------------------------------------------------------ S9
        head("S9 timings (machine-specific)")
        try:
            cpu = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                                 capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception:
            cpu = platform.processor()
        print("cpu:", cpu)
        cold = tmp / "cold"
        ts = []
        for rep in range(3):
            shutil.rmtree(cold, ignore_errors=True)
            t0 = time.perf_counter()
            cached_embed(texts, SPEC_L6, Counting(m6), cold)
            ts.append(time.perf_counter() - t0)
        tw = []
        for rep in range(3):
            t0 = time.perf_counter()
            cached_embed(texts, SPEC_L6, Counting(m6), cold)
            tw.append(time.perf_counter() - t0)
        tl = []
        for rep in range(3):
            t0 = time.perf_counter()
            load_index(idx, RUN)
            tl.append(time.perf_counter() - t0)
        print(f"embed {n} chunks, empty cache (median of 3): {sorted(ts)[1]:.2f} s; all hits: {sorted(tw)[1]*1000:.1f} ms; "
              f"load_index with all checks: {sorted(tl)[1]*1000:.1f} ms")
        print("\nDONE")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
