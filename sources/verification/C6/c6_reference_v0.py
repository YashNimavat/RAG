"""C6: retrieval-only reference run of v0 (load -> snapshot -> chunk -> embed -> index -> retrieve -> prompt -> trace).

This is the AUTHOR'S reference, used only to measure the numbers in concepts/C6_v0_pipeline.md.
It is a solution: the learner builds v0 from their own C1-C5 code (FT: no).

What it does, stage by stage (06 sec. 3.1):
  Load      PyMuPDF page.get_text() per page; frozen-text snapshot per 06 sec. 5.3 (cleaning: none).
  Chunk     spans from the 07 H.1 + H.3 code, executed EXACTLY as written in 07_SAMPLE_LESSON.md (as contracts_check.py
            does), ChunkerConfig(name="recursive", size=1000, overlap=200), per page. The ids follow the COURSE decision
            (coordinator, 2026-10-08): params_hash = sha256(json.dumps(06 sec. 2.4 chunking block, sort_keys=True))[:12]
            = 1ca9c5a3b548; chunk_id = doc_id:snapshot_id:params_hash:seq. chunks.jsonl uses 06 sec. 2.3 key order, so it
            can be compared byte for byte with the C2 lab's output.
  Embed     LOCAL fallback only: sentence-transformers/all-MiniLM-L6-v2 (pinned revision), normalized, float32.
            The default Cohere embedder is NOT called (no paid API calls).
  Index     vectors.npy + chunks.jsonl + manifest.json (row i of vectors.npy <-> line i of chunks.jsonl).
  Retrieve  exact cosine scores = V @ q, k = 4, ties broken by chunk_id.
  Prompt    06 sec. 3.3 template, built and hashed (o200k_harmony token count, local).
  Generate  NOT RUN. One query (D-002) carries a HAND-WRITTEN TOY answer, labelled as such, so that the citation
            fields of the trace can be shown. All other answers are null with an explanatory error.
  Log       one trace record per query (06 sec. 2.5, v0 subset) appended to results.jsonl.

Usage (from rag_learning/):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C6/c6_reference_v0.py <pdf> <out_dir>
Writes the index and run files under <out_dir> (keep it OUTSIDE the workspace: chunks.jsonl holds corpus text).
Prints a report to stdout. .env is never read.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import platform
import re
import sys
import time
import types
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")          # local cache only; no network
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np          # noqa: E402
import pymupdf              # noqa: E402

PDF, OUT = Path(sys.argv[1]), Path(sys.argv[2])
WS = Path(__file__).resolve().parents[3]                # rag_learning/
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
MINILM_REV = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
K = 4
DOC_ID = "climate"
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}   # 06 sec. 2.4 `chunking:` block, exactly
TOY_QID = "D-002"
TOY_ANSWER = "The Paris Agreement was adopted in 2015 [climate:10]."      # HAND-WRITTEN TOY, not a model output
ABSTAIN = "I cannot answer this from the provided documents."
SYSTEM_V0 = (
    "You answer questions using ONLY the numbered sources below.\n"
    "Rules:\n"
    "1. Every factual sentence must end with one or more citations in the form [doc_id:page],\n"
    "   copied exactly from the source headers, e.g. [climate:10].\n"
    "2. If the sources do not contain the answer, reply exactly:\n"
    "   \"I cannot answer this from the provided documents.\"\n"
    "   Do not use outside knowledge.\n"
    "3. Do not cite a source that does not support the sentence.\n"
    "4. Be concise: at most 5 sentences.\n")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def prompt_sha256(system: str, user: str) -> str:
    """prompt.sha256 = sha256 of the chat messages, json.dumps(messages, sort_keys=True, ensure_ascii=False)
    (the C5 recipe, labs/C5_generation_lab.ipynb Task 6; 06 sec. 2.5 names the field but gives no recipe)."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return sha(json.dumps(msgs, sort_keys=True, ensure_ascii=False))


def section(title: str) -> None:
    print(f"\n=== {title}")


def ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 3)


# --------------------------------------------------------------------------------------------- 07 code
def code_blocks(md: str, lang: str) -> list[str]:
    return re.findall(r"^```" + re.escape(lang) + r"[ \t]*\n(.*?)^```", md, flags=re.S | re.M)


def md_section(md: str, heading_prefix: str) -> str:
    lines, fence, start, level = md.splitlines(), False, None, None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#+)\s+(.*)$", ln)
        if not m:
            continue
        if start is None and m.group(2).startswith(heading_prefix):
            start, level = i, len(m.group(1))
        elif start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:])


def load_07():
    md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
    h1 = code_blocks(md_section(md07, "H.1 Minimal implementation"), "python")[0]
    h3 = code_blocks(md_section(md07, "H.3 Reusable design"), "python")[0]
    pkg = types.ModuleType("ragkit")
    pkg.__path__ = []
    sys.modules["ragkit"] = pkg
    core = types.ModuleType("ragkit._core")
    sys.modules["ragkit._core"] = core
    exec(compile(h1, "07_H1", "exec"), core.__dict__)
    chunking = types.ModuleType("ragkit.chunking")
    sys.modules["ragkit.chunking"] = chunking
    exec(compile(h3, "07_H3", "exec"), chunking.__dict__)
    return core, chunking, sha(h1), sha(h3)


# --------------------------------------------------------------------------------------------- seeds
def load_seeds() -> list[dict]:
    md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
    items = [json.loads(ln) for ln in md06.splitlines() if ln.startswith('{"qid":"D-00')]
    items = sorted({it["qid"]: it for it in items}.values(), key=lambda it: it["qid"])
    items.append({"qid": "R-001", "question": "What is the main cause of climate change?", "answerable": None,
                  "evidence_groups": [], "notes": "repo test query, simple_rag.ipynb cell 15; no gold label"})
    return items


def main() -> int:
    t_all = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    core, chunking, h1_sha, h3_sha = load_07()

    # ------------------------------------------------------------------ S1 load + snapshot
    section("S1 environment, load, snapshot (06 sec. 5.3)")
    import sentence_transformers
    import tiktoken
    import torch
    vers = {"python": platform.python_version(), "pymupdf": pymupdf.__version__ if hasattr(pymupdf, "__version__") else pymupdf.VersionBind,
            "numpy": np.__version__, "sentence-transformers": sentence_transformers.__version__,
            "torch": torch.__version__, "tiktoken": tiktoken.__version__}
    print("versions:", json.dumps(vers, sort_keys=True))
    pdf_bytes = PDF.read_bytes()
    t0 = time.perf_counter()
    pages = [p.get_text() for p in pymupdf.open(PDF)]
    lat_load = ms(t0)
    doc_text, starts = core.join_pages(pages)
    parser = {"backend": "pymupdf", "version": vers["pymupdf"], "call": "page.get_text()", "options": {}}
    parts = ["snapshot-v1", f"parser={parser['backend']}@{parser['version']}",
             "options=" + json.dumps(parser["options"], sort_keys=True), "cleaning=none", "page_join=\\n",
             f"{DOC_ID}:{sha(doc_text)}"]
    snapshot_id = sha("|".join(parts))[:12]
    page_table, pos = [], 0
    for i, t in enumerate(pages, 1):
        page_table.append({"page": i, "doc_char_start": pos, "doc_char_end": pos + len(t), "text_sha256": sha(t)})
        pos += len(t) + 1
    snap_manifest = {"snapshot_id": snapshot_id, "corpus": "D", "corpus_version": "1.0", "created_utc": "<set by snapshot tool>",
                     "parser": parser, "cleaning": {"version": "none", "steps": []}, "encoding": "utf-8",
                     "newline": "\n", "page_join": "\n",
                     "docs": [{"doc_id": DOC_ID, "pdf_sha256": sha_bytes(pdf_bytes), "bytes": len(pdf_bytes),
                               "pages": len(pages), "doc_text_sha256": sha(doc_text), "page_table": page_table}]}
    snap_bytes = json.dumps(snap_manifest, indent=2, ensure_ascii=False).encode("utf-8")
    print(f"pdf sha256 {sha_bytes(pdf_bytes)}  bytes {len(pdf_bytes)}")
    print(f"pages {len(pages)}  doc_text chars {len(doc_text)}  doc_text_sha256 {sha(doc_text)}")
    print(f"snapshot_id {snapshot_id}  (06 sec. 5.3 states ea07572562ac: {'MATCH' if snapshot_id == 'ea07572562ac' else 'MISMATCH'})")
    print(f"page 10 starts at doc offset {page_table[9]['doc_char_start']} (06 sec. 5.3 states 20,555)")
    print(f"tab characters in doc_text: {doc_text.count(chr(9))}  (upstream replace_t_with_space would change {doc_text.count(chr(9))} chars)")
    print(f"load latency_ms {lat_load}")

    # ------------------------------------------------------------------ S2 chunk
    section("S2 chunk (spans from the 07 H.1 + H.3 code as written; ids from the course params_hash)")
    cfg = chunking.ChunkerConfig(name="recursive", size=1000, overlap=200)
    params_hash = sha(json.dumps(CHUNKING, sort_keys=True))[:12]      # course decision: hash of the 06 sec. 2.4 block
    t0 = time.perf_counter()
    chunks = [dataclasses.replace(c, chunk_id=f"{DOC_ID}:{snapshot_id}:{params_hash}:{c.seq:05d}", params_hash=params_hash,
                                  chunker=CHUNKING["name"])
              for c in chunking.chunk_document(DOC_ID, snapshot_id, pages, cfg)]
    lat_chunk = ms(t0)
    print(f"07 H.1 code sha256 {h1_sha[:16]}  07 H.3 code sha256 {h3_sha[:16]}")
    print("07 ChunkerConfig used for the spans:", json.dumps(asdict(cfg), sort_keys=True), "-> 07 params_hash()", cfg.params_hash())
    print("CHUNKING (06 sec. 2.4 block, hashed):", json.dumps(CHUNKING, sort_keys=True))
    print(f"params_hash {params_hash}  (course decision value 1ca9c5a3b548: {'MATCH' if params_hash == '1ca9c5a3b548' else 'MISMATCH'})")
    lens = [len(c.text) for c in chunks]
    per_page = [sum(1 for c in chunks if c.page_start == p) for p in range(1, len(pages) + 1)]
    ok_text = all(doc_text[c.char_start:c.char_end] == c.text for c in chunks)
    ok_seg = all(len(c.page_segments) == 1 for c in chunks)
    ok_sha = all(c.text_sha256 == sha(c.text) for c in chunks)
    ok_size = all(0 < n <= 1000 for n in lens)
    print(f"chunks {len(chunks)}  length min/median/max {min(lens)}/{int(np.median(lens))}/{max(lens)}")
    print(f"chunks per page min/max {min(per_page)}/{max(per_page)}; pages with 3+ chunks {sum(1 for n in per_page if n >= 3)}")
    print(f"invariants: text==doc_text[a:b] {ok_text}; one page_segment each {ok_seg}; text_sha256 {ok_sha}; 0<len<=1000 {ok_size}")
    print(f"first chunk_id {chunks[0].chunk_id}")
    print(f"last  chunk_id {chunks[-1].chunk_id}")
    ids_fp = sha(json.dumps([c.chunk_id for c in chunks]))[:16]
    print(f"fingerprint of the chunk_id list {ids_fp}")
    print(f"chunk latency_ms {lat_chunk}")

    # ------------------------------------------------------------------ S3 embed
    section("S3 embed (LOCAL MiniLM fallback; Cohere default not called)")
    from sentence_transformers import SentenceTransformer
    t0 = time.perf_counter()
    model = SentenceTransformer(MINILM, device="cpu", revision=MINILM_REV)
    lat_model = ms(t0)
    snap_dirs = sorted(p.name for p in (Path.home() / ".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots").iterdir())
    print(f"model {MINILM}  cache snapshots {snap_dirs}  max_seq_length {model.max_seq_length}  dim {model.get_embedding_dimension()}")
    texts = [c.text for c in chunks]
    t0 = time.perf_counter()
    V = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, batch_size=64).astype(np.float32)
    lat_embed = ms(t0)
    ntok = [len(model.tokenizer(t, add_special_tokens=True)["input_ids"]) for t in texts]
    trunc = sum(1 for n in ntok if n > model.max_seq_length)
    print(f"V shape {V.shape} dtype {V.dtype}  max|norm-1| {np.abs(np.linalg.norm(V, axis=1) - 1).max():.2e}")
    print(f"MiniLM tokens per chunk (with [CLS]/[SEP]) min/median/max {min(ntok)}/{int(np.median(ntok))}/{max(ntok)}; chunks over {model.max_seq_length}: {trunc}")
    ck = chunking.embedding_cache_key(texts[0], provider="sentence_transformers", model_id=MINILM, model_revision=MINILM_REV,
                                      input_type="none", preprocessing_version="none")
    keys = {chunking.embedding_cache_key(t, provider="sentence_transformers", model_id=MINILM, model_revision=MINILM_REV,
                                         input_type="none", preprocessing_version="none") for t in texts}
    print(f"embedding cache key of chunk 0: {ck[:16]}...  distinct keys {len(keys)} for {len(texts)} chunks")
    print(f"model load latency_ms {lat_model}  embed {len(texts)} chunks latency_ms {lat_embed}")

    # ------------------------------------------------------------------ S4 index files
    section("S4 index files (vectors.npy, chunks.jsonl, manifest.json)")
    # course decision (coordinator, 2026-10-08): index/<snapshot_id>/<params_hash>/<embed_hash>/,
    # embed_hash = 12 hex of sha256(json.dumps({provider, model_id, revision, input_type, normalize, preproc_version}, sort_keys=True))
    # Field VALUES follow the C3 measure script's embedding block (interface assumption until C3 H.4 states them).
    EMB = {"provider": "sentence_transformers", "model_id": MINILM, "revision": MINILM_REV,
           "input_type": {"documents": "none", "queries": "none"}, "normalize": True, "preproc_version": "none"}
    embed_hash = sha(json.dumps(EMB, sort_keys=True))[:12]
    idx = OUT / "index" / snapshot_id / params_hash / embed_hash
    idx.mkdir(parents=True, exist_ok=True)
    (OUT / "snapshot_manifest.json").write_bytes(snap_bytes)
    np.save(idx / "vectors.npy", V)
    KEYS = ["doc_id", "snapshot_id", "chunk_id", "seq", "char_start", "char_end", "page_segments", "text", "text_sha256",
            "chunker", "params_hash", "meta"]                     # 06 sec. 2.3 field order (same as the C2 lab output)
    lines = [json.dumps({k: ([asdict(s) for s in c.page_segments] if k == "page_segments" else {} if k == "meta" else getattr(c, k))
                         for k in KEYS}, ensure_ascii=False) for c in chunks]
    (idx / "chunks.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    cj = sha_bytes((idx / "chunks.jsonl").read_bytes())
    c2 = "d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b"
    print(f"chunks.jsonl sha256 {cj}; C2 lab chunks.jsonl (C2LAB_FACTS) {c2[:16]}...: {'IDENTICAL' if cj == c2 else 'DIFFERENT'}")
    manifest = {
        "index_version": "v0", "corpus": "D", "snapshot_id": snapshot_id,
        "snapshot_manifest_sha256": sha_bytes(snap_bytes),
        "parser": parser, "cleaning": "none",
        "chunker": CHUNKING, "params_hash": params_hash, "embed_hash": embed_hash,
        "embedding": {**EMB, "dim": int(V.shape[1]), "max_seq_length": int(model.max_seq_length)},
        "n_chunks": len(chunks),
        "chunks_jsonl_sha256": sha_bytes((idx / "chunks.jsonl").read_bytes()),
        "vectors_npy_sha256": sha_bytes((idx / "vectors.npy").read_bytes()),
        "library_versions": {k: vers[k] for k in ("pymupdf", "numpy", "sentence-transformers", "torch")},
    }
    mbytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    (idx / "manifest.json").write_bytes(mbytes)
    index_manifest_hash = "sha256:" + sha_bytes(mbytes)
    for f in ("vectors.npy", "chunks.jsonl", "manifest.json"):
        print(f"{f:14s} {(idx / f).stat().st_size:>9,d} bytes  sha256 {sha_bytes((idx / f).read_bytes())[:16]}")
    print(f"embedding block hashed for embed_hash: {json.dumps(EMB, sort_keys=True)}")
    print(f"index dir: index/{snapshot_id}/{params_hash}/{embed_hash}/")
    print(f"index_manifest_hash {index_manifest_hash[:23]}...")

    # ------------------------------------------------------------------ config
    config = {"run": {"id": "E000_v0_baseline", "version": "v0", "seed": 0},
              "corpus": {"name": "D", "snapshot_id": snapshot_id},
              "parsing": {"backend": "pymupdf", "mode": "text", "cleaning": "none"},
              "chunking": CHUNKING,
              "embedding": EMB,
              "retrieval": {"method": "dense", "similarity": "cosine_exact", "k": K},
              "generation": {"provider": "NOT RUN (reference run)", "temperature": 0.0, "max_tokens": 512,
                             "prompt_version": "answer_v1"}}
    cbytes = json.dumps(config, indent=2, sort_keys=True).encode("utf-8")
    (OUT / "config.json").write_bytes(cbytes)
    config_hash = "sha256:" + sha_bytes(cbytes)

    # ------------------------------------------------------------------ S5 retrieve + trace
    section("S5 retrieve (k=4, exact cosine, ties by chunk_id), prompt, trace")
    enc = tiktoken.get_encoding("o200k_harmony")
    ntk = lambda s: len(enc.encode(s, disallowed_special=()))
    seeds = load_seeds()
    cid = [c.chunk_id for c in chunks]
    results_path = OUT / "results.jsonl"
    rec_sizes, summary = [], []
    with results_path.open("w", encoding="utf-8", newline="\n") as fh:
        for it in seeds:
            q = it["question"]
            t_q = time.perf_counter()
            t0 = time.perf_counter()
            qv = model.encode([q], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]
            lat_eq = ms(t0)
            t0 = time.perf_counter()
            scores = V @ qv
            order = sorted(range(len(chunks)), key=lambda i: (-float(scores[i]), cid[i]))
            top = order[:K]
            lat_dense = ms(t0)
            t0 = time.perf_counter()
            blocks = [f"[{r}] ({chunks[i].doc_id}:{chunks[i].page_start})\n{chunks[i].text}" for r, i in enumerate(top, 1)]
            user = "Sources:\n" + "\n\n".join(blocks) + f"\n\nQuestion: {q}\nAnswer:"
            prompt_sha = prompt_sha256(SYSTEM_V0, user)
            lat_ctx = ms(t0)
            ctx_ids = [cid[i] for i in top]
            # gold: page-relative -> document offsets through the page table (gold_to_doc rule)
            gold_report = []
            for g in it.get("evidence_groups", []):
                for alt in g["alternatives"]:
                    for s in alt["segments"]:
                        pt = page_table[s["page"] - 1]
                        assert 0 <= s["char_start"] < s["char_end"] <= pt["doc_char_end"] - pt["doc_char_start"]
                        a, b = pt["doc_char_start"] + s["char_start"], pt["doc_char_start"] + s["char_end"]
                        quote_ok = " ".join(doc_text[a:b].split()).startswith(" ".join(alt["quote"].split())[:60])
                        contain = [r for r, i in enumerate(order, 1) if chunks[i].char_start <= a and b <= chunks[i].char_end]
                        overlap = [r for r, i in enumerate(order, 1) if chunks[i].char_start < b and a < chunks[i].char_end]
                        gold_report.append({"group": g["group_id"], "alt": alt["alt_id"], "page": s["page"],
                                            "doc": [a, b], "quote_matches_text": quote_ok,
                                            "first_rank_containing": contain[0] if contain else None,
                                            "first_rank_overlapping": overlap[0] if overlap else None})
            # CE@4: every group has an alternative whose segments are all wholly inside some top-4 chunk
            ce4 = None
            if it.get("evidence_groups"):
                ce4 = int(all(any(all(any(chunks[i].char_start <= gr["doc"][0] and gr["doc"][1] <= chunks[i].char_end for i in top)
                                      for gr in gold_report if gr["group"] == g["group_id"] and gr["alt"] == alt["alt_id"])
                                  for alt in g["alternatives"]) for g in it["evidence_groups"]))
            # generation: NOT RUN; a hand-written toy answer for one query only
            if it["qid"] == TOY_QID:
                text = TOY_ANSWER
                cits = []
                for m in re.finditer(r"\[([A-Za-z0-9_\-]+):(\d+)\]", text):
                    d, p = m.group(1), int(m.group(2))
                    cits.append({"marker": m.group(0), "doc_id": d, "page": p,
                                 "resolved_chunk_ids": [cid[i] for i in top if chunks[i].doc_id == d and chunks[i].page_start == p]})
                answer = {"text": text, "abstained": text.strip() == ABSTAIN, "citations": cits, "output_tokens": None}
                llm = {"provider": "toy", "model_id": "handwritten-toy-v1", "cache_hit": False, "temperature": None}
                errors = ["TOY: answer.text is hand-written for the lesson, not a model output"]
            else:
                answer = {"text": None, "abstained": None, "citations": [], "output_tokens": None}
                llm = {"provider": None, "model_id": None, "cache_hit": False, "temperature": None}
                errors = ["generation not run: retrieval-only reference run"]
            rec = {
                "trace_version": "1.0", "run_id": "E000_v0_baseline_reference", "qid": it["qid"],
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "config_hash": config_hash, "index_manifest_hash": index_manifest_hash, "snapshot_id": snapshot_id,
                "query": {"original": q, "transformed": [{"method": "none", "text": q}]},
                "candidates": {"dense": [{"rank": r, "chunk_id": cid[i], "doc_id": chunks[i].doc_id,
                                          "page": chunks[i].page_start, "char_start": chunks[i].char_start,
                                          "char_end": chunks[i].char_end, "score": float(scores[i])}
                                         for r, i in enumerate(top, 1)]},
                "context": {"chunk_ids": ctx_ids, "context_tokens": sum(ntk(chunks[i].text) for i in top),
                            "tokenizer": "o200k_harmony", "truncated_chunks": sum(1 for i in top if ntok[i] > model.max_seq_length)},
                "prompt": {"template_version": "answer_v1", "sha256": prompt_sha, "input_tokens": ntk(SYSTEM_V0) + ntk(user)},
                "answer": answer,
                "latency_ms": {"embed_query": lat_eq, "dense": lat_dense, "context": lat_ctx, "llm": None,
                               "total": ms(t_q)},
                "cost_usd_estimate": {"llm": None, "judge": None, "price_table_version": None},
                "llm": llm, "errors": errors,
            }
            line = json.dumps(rec, ensure_ascii=False)
            fh.write(line + "\n")
            rec_sizes.append(len(line.encode("utf-8")) + 1)
            summary.append((it, top, scores, order, gold_report, ce4, rec))
    for it, top, scores, order, gold_report, ce4, rec in summary:
        top_desc = ", ".join(f"p.{chunks[i].page_start}#{chunks[i].seq}({float(scores[i]):.4f})" for i in top)
        gap = float(scores[order[K - 1]]) - float(scores[order[K]])
        print(f"{it['qid']}: top-4 = {top_desc}; gap rank4-rank5 {gap:.4f}; CE@4 {ce4}")
        for gr in gold_report:
            print(f"    gold {gr['group']}/{gr['alt']} p.{gr['page']} doc[{gr['doc'][0]},{gr['doc'][1]}) quote_ok={gr['quote_matches_text']} "
                  f"first rank wholly containing={gr['first_rank_containing']} first rank overlapping={gr['first_rank_overlapping']}")
        print(f"    prompt input_tokens {rec['prompt']['input_tokens']}  context_tokens {rec['context']['context_tokens']}  "
              f"truncated {rec['context']['truncated_chunks']}")
    toy = next(r for *_, r in summary if r["qid"] == TOY_QID)
    (OUT / f"trace_{TOY_QID}.json").write_text(json.dumps(toy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"\nTOY trace {TOY_QID}: answer (hand-written) {toy['answer']['text']!r}")
    print(f"    citations {json.dumps(toy['answer']['citations'])}")
    print(f"\ntrace records {len(rec_sizes)}; bytes per record min/median/max {min(rec_sizes)}/{int(np.median(rec_sizes))}/{max(rec_sizes)}; "
          f"results.jsonl {results_path.stat().st_size:,d} bytes")
    print(f"embed_query latency_ms (this run) {[r['latency_ms']['embed_query'] for *_, r in summary]}")
    print(f"dense latency_ms (this run) {[r['latency_ms']['dense'] for *_, r in summary]}")

    # ------------------------------------------------------------------ S6 one trace, every artifact (D-002)
    section("S6 one query through every artifact (D-002)")
    it, top, scores, order, gold_report, ce4, rec = next(s for s in summary if s[0]["qid"] == TOY_QID)
    qv = model.encode([it["question"]], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]
    for r, i in enumerate(top, 1):
        c = chunks[i]
        seg = c.page_segments[0]
        pt = page_table[seg.page - 1]
        back = (pt["doc_char_start"] + seg.char_start, pt["doc_char_start"] + seg.char_end)
        recomputed = float(V[i] @ qv)
        print(f"rank {r}: chunk_id {c.chunk_id}  row {i}  page {seg.page} page-rel [{seg.char_start},{seg.char_end}) -> doc [{back[0]},{back[1]})"
              f" == chunk doc [{c.char_start},{c.char_end}) {back == (c.char_start, c.char_end)}")
        print(f"        vector row {i}: first 3 dims {[round(float(x), 4) for x in V[i][:3]]} norm {np.linalg.norm(V[i]):.6f}; "
              f"score stored {rec['candidates']['dense'][r-1]['score']:.6f} recomputed {recomputed:.6f}")
        print(f"        text starts {c.text[:60]!r}")
    print(f"query vector first 3 dims {[round(float(x), 4) for x in qv[:3]]} norm {np.linalg.norm(qv):.6f}")
    print(f"gold D-002: {gold_report}")

    # ------------------------------------------------------------------ S7 params_hash sensitivity
    section("S7 what changes params_hash (course recipe over the 06 block; 07 ChunkerConfig.params_hash for contrast)")
    for k_, v_ in {"06 block (v0, course decision)": CHUNKING, "06 block, chunk_overlap 100": {**CHUNKING, "chunk_overlap": 100},
                   "06 block, scope cross_page": {**CHUNKING, "scope": "cross_page"}}.items():
        print(f"{k_:62s} params_hash {sha(json.dumps(v_, sort_keys=True))[:12]}")
    variants = {
        "07 ChunkerConfig recursive 1000/200 (07 defaults)": cfg,
        "overlap 200 -> 100": chunking.ChunkerConfig(name="recursive", size=1000, overlap=100),
        "size 1000 -> 2000, overlap 400": chunking.ChunkerConfig(name="recursive", size=2000, overlap=400),
        "scope cross_page": chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="cross_page"),
        "06 YAML spelling: name recursive_char + separators with ''": chunking.ChunkerConfig(
            name="recursive_char", size=1000, overlap=200, separators=("\n\n", "\n", " ", "")),
    }
    for k_, v_ in variants.items():
        print(f"{k_:62s} params_hash {v_.params_hash()}")
    cross = chunking.chunk_document(DOC_ID, snapshot_id, pages, variants["scope cross_page"])
    print(f"cross_page scope: {len(cross)} chunks, {sum(1 for c in cross if len(c.page_segments) > 1)} span two pages")
    print(f"\nstage latency_ms (this run): load {lat_load} | chunk {lat_chunk} | model load {lat_model} | embed {lat_embed} | "
          f"whole script {ms(t_all)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
