"""C3 study-kit measurements (K1-K10): the numbers the HTML lesson adds on top of c3_measure.py (S1-S9).

Why a second script: the 2026-10-17/18 Phase 2 research (study/research/phase_02_core_rag_baseline.md, Concept C3)
found ideas the old lesson never measured: the four request fields missing from the cache key (Foundation E2), the
token and byte bounds behind truncation, model identity beyond the revision, near-duplicates, mixed-model indexes,
and the identity grid. c3_measure.py is not changed, so its saved output stays as it was. The reference functions
(chunker, params_hash, embed_hash, the v1 cache key, cached_embed, write_index, load_index, rebuild_reasons, top_k)
are imported from it, not re-typed.

Local only: no Groq, Cohere or Claude call, no .env read. MiniLM-L6 and paraphrase-MiniLM-L3 load from the local
Hugging Face cache (offline). Index and cache files go to a temporary folder that is deleted at the end.
Labels: the 06 section 6.7 draft seeds are LLM-drafted and not human-verified, so every rank below is an
observation, never an evaluation result.

Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C3/c3_kit_measure.py \
        "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        > sources/verification/C3/out_c3_kit_measure.txt 2> sources/verification/C3/out_c3_kit_measure.stderr.txt
Every section is deterministic (no timings).
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import logging
import math
import pathlib
import shutil
import sys
import tempfile

import numpy as np
import pymupdf                                        # pinned 1.26.7

HERE = pathlib.Path(__file__).resolve().parent
WS = HERE.parents[2]
sys.path.insert(0, str(HERE))
import c3_measure as m                                # noqa: E402  (reference functions; its main() is not run)

cc = m.cc
PDF = pathlib.Path(sys.argv[1])
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
HUB = pathlib.Path.home() / ".cache" / "huggingface" / "hub"


def head(t):
    print(f"\n=== {t}")


def f4(x):
    return f"{x:.4f}"


def canon(obj) -> bytes:
    """Foundation section 2.3 canonical JSON."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


# The 10-field key the research proposes (C3 section 6 idea 5; Foundation E2). Not yet a course decision: the
# study/llmops helper package settles the final form. Fields a provider does not have are recorded as "none".
KEY2_FIELDS = ("provider", "model_id", "revision", "input_type", "output_dimension", "embedding_type", "truncate",
               "max_tokens", "preproc_version")


def key_v2(text, spec):
    return hashlib.sha256(canon({**{f: spec[f] for f in KEY2_FIELDS}, "text": text})).hexdigest()


SPEC2_L6 = {**m.SPEC_L6, "output_dimension": "none", "embedding_type": "float", "truncate": "none", "max_tokens": "none"}
SPEC2_COHERE = {"provider": "cohere", "model_id": "embed-v4.0", "revision": "none", "input_type": "search_document",
                "output_dimension": 1536, "embedding_type": "float", "truncate": "NONE", "max_tokens": "none",
                "preproc_version": "none"}


def main():
    md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
    cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
    PARSER = {"backend": "pymupdf", "version": pymupdf.VersionBind, "call": "page.get_text()", "options": {}}

    def snapshot_id_of(pages_by_doc):
        return cc.snapshot_id_06(PARSER, cc.CLEANING_NONE, {d: m.sha("\n".join(p)) for d, p in pages_by_doc.items()})

    pdf_bytes = PDF.read_bytes()
    pages = [p.get_text() for p in pymupdf.open(PDF)]
    full = "\n".join(pages)
    starts = m.page_starts(pages)
    SNAP = snapshot_id_of({"climate": pages})
    CFG = dict(m.CHUNKING)
    chunks = m.make_chunks("climate", SNAP, pages, CFG, m.params_hash)
    N = len(chunks)
    texts = [c["text"] for c in chunks]
    jl = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")

    seeds = [json.loads(x) for x in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines() if x.strip()]
    for s in seeds:
        s["G"] = [[[("climate", starts[g["page"] - 1] + g["char_start"], starts[g["page"] - 1] + g["char_end"])
                    for g in alt["segments"]] for alt in grp["alternatives"]] for grp in s["evidence_groups"]]
    ans = [s for s in seeds if s["answerable"]]
    REL = {s["qid"]: [i for i in range(N) if cc.rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]),
                                                     s["G"], {"climate": full})] for s in ans}

    def ranking(scores):
        return sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))

    def first_rel(order, qid):
        return next((r for r, i in enumerate(order, 1) if i in REL[qid]), None)

    def summary(ranks, k=4):
        return (sum(r is not None and r <= 1 for r in ranks), sum(r is not None and r <= k for r in ranks),
                round(sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks), 3))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="c3_kit_"))
    try:
        # ------------------------------------------------------------------ K1
        head("K1 environment and the v0 records")
        vers = {k: md.version(k) for k in ("pymupdf", "numpy", "sentence-transformers", "transformers", "tokenizers", "torch")}
        print("versions", vers)
        print(f"snapshot_id {SNAP} | params_hash {m.params_hash(CFG)} | records {N} | chunks.jsonl {len(jl)} bytes, "
              f"sha256 {hashlib.sha256(jl).hexdigest()[:16]}… equals the C2 lab file: {hashlib.sha256(jl).hexdigest() == m.C2_JSONL_SHA256}")
        print("record fields (06 section 2.3 order):", list(chunks[0].keys()))
        print(f"chunk seq 27 (holds D-002's evidence): id {chunks[27]['chunk_id']} | doc [{chunks[27]['char_start']}, "
              f"{chunks[27]['char_end']}) | page_segments {chunks[27]['page_segments']} | {len(texts[27])} chars | "
              f"text_sha256 {chunks[27]['text_sha256'][:12]}… | slice check {full[chunks[27]['char_start']:chunks[27]['char_end']] == texts[27]}")
        print("relevant chunk seqs per answerable draft seed:", REL)

        # ------------------------------------------------------------------ K2
        head("K2 the cache key: v1 (six fields, '|' string, v0 today) and the proposed 10-field canonical-JSON key")
        t = "hello|world"
        k1 = m.embedding_cache_key(t, **m.SPEC_L6)
        k2 = key_v2(t, SPEC2_L6)
        print(f"v1 key('hello|world', L6) {k1[:16]}… | v2 key {k2[:16]}… | different namespaces: {k1 != k2}")
        changes = [("provider", "cohere"), ("model_id", m.L3), ("revision", "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"),
                   ("input_type", "search_query"), ("output_dimension", 256), ("embedding_type", "int8"),
                   ("truncate", "END"), ("max_tokens", 512), ("preproc_version", "tabs_to_spaces")]
        moved = 0
        for f, v in changes:
            d = key_v2(t, {**SPEC2_L6, f: v}) != k2
            moved += d
            print(f"  v2: change {f:16s} -> key differs: {d}")
        dt = key_v2("hello|worle", SPEC2_L6) != k2
        print(f"  v2: change the text by one character -> key differs: {dt}")
        print(f"v2 fields that move the key: {moved + dt} of {len(changes) + 1}")
        v1_blind = [f for f, v in changes if f not in m.SPEC_L6]
        print("fields the v1 key cannot see (not among its arguments):", v1_blind)
        amb = key_v2("t", {**SPEC2_L6, "model_id": "a|b", "revision": "c"}) == key_v2("t", {**SPEC2_L6, "model_id": "a", "revision": "b|c"})
        print(f"v2 with '|' inside fields: ('a|b','c') vs ('a','b|c') collide: {amb} (JSON quotes each field)")
        print("Cohere spec example (the four new fields sent explicitly):", json.dumps(SPEC2_COHERE, sort_keys=True))
        # local stand-in for output_dimension: MiniLM with truncate_dim=256 (an illustration, not Cohere)
        from sentence_transformers import SentenceTransformer
        m6 = SentenceTransformer(m.L6, device="cpu")
        m3 = SentenceTransformer(m.L3, device="cpu")
        cache1 = tmp / "v1"
        V384, st = m.cached_embed(texts, m.SPEC_L6, m.Counting(m6), cache1)
        _, st_v1 = m.cached_embed(texts, m.SPEC_L6, m.Counting(m6), cache1)   # a "256" run with the v1 key: same key
        print(f"stand-in: build at 384 {st}; then ask for 256 numbers with the v1 key -> {st_v1} "
              f"(the key cannot see the dimension), served shape {V384.shape} while 256 were asked")
        k384 = [key_v2(x, SPEC2_L6) for x in texts]
        k256 = [key_v2(x, {**SPEC2_L6, "output_dimension": 256}) for x in texts]
        print(f"same with the v2 key: keys shared between the 384 and the 256 runs: {len(set(k384) & set(k256))} of {N} "
              f"-> {N} misses, nothing stale")

        # ------------------------------------------------------------------ K3
        head("K3 FORMULA: calls, bytes and work per query")
        for n in (97, 1000, 5000, 10000):
            print(f"  Cohere calls for {n:>6,} texts at 96 per call: ceil({n}/96) = {math.ceil(n / 96)}")
        for n, d in ((97, 384), (97, 1536), (97, 256), (65, 384), (5000, 384), (5000, 1536)):
            print(f"  vectors.npy {n:>5,} x {d:>4}: 128 + {n}*{d}*4 = {128 + n * d * 4:,} bytes")
        for n, d in ((97, 384), (97, 1536), (5000, 1536), (1_000_000, 1536)):
            print(f"  exact search, one question: {n:,} x {d} = {n * d:,} multiply-adds")

        # ------------------------------------------------------------------ K4
        head("K4 truncation: MiniLM token counts (own tokenizer, [CLS]/[SEP] included) and UTF-8 bytes per chunk")
        tok = m6.tokenizer
        ntok = lambda x: len(tok(x)["input_ids"])
        bins = [0, 64, 128, 192, 256, 320, 384, 448]
        for size, ov in ((1000, 200), (1500, 300), (2000, 400)):
            cf = {**CFG, "chunk_size": size, "chunk_overlap": ov}
            ch = m.make_chunks("climate", SNAP, pages, cf, m.params_hash)
            tk = [ntok(c["text"]) for c in ch]
            hist = np.histogram(tk, bins=bins + [10_000])[0].tolist()
            print(f"  {size}/{ov}: {len(ch)} chunks, params_hash {m.params_hash(cf)}, tokens min {min(tk)} median "
                  f"{int(np.median(tk))} max {max(tk)}, over 256: {sum(x > 256 for x in tk)}, over 128: {sum(x > 128 for x in tk)}; "
                  f"histogram bins {bins}+: {hist}")
        b = [len(x.encode("utf-8")) for x in texts]
        nonascii = sum(ch > "\x7f" for x in texts for ch in x)
        print(f"v0 chunks: characters {min(map(len, texts))}..{max(map(len, texts))}; UTF-8 bytes {min(b)}..{max(b)}; "
              f"non-ASCII characters in all 97: {nonascii}")
        print(f"bound (assumption: a byte-level tokenizer gives at most one token per UTF-8 byte): max tokens <= {max(b)} "
              f"< 8,192 (Models API figure) < 128k (docs figure); a 1,000-character chunk is at most {4 * 1000:,} bytes")
        print(f"MiniLM max_seq_length {m6.max_seq_length}; L3 max_seq_length {m3.max_seq_length}")

        # ------------------------------------------------------------------ K5
        head("K5 model identity: the two cached MiniLM-L6 snapshots")
        snapdir = HUB / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots"
        ref = (HUB / "models--sentence-transformers--all-MiniLM-L6-v2" / "refs" / "main").read_text().strip()
        snaps = sorted(p.name for p in snapdir.iterdir())
        print("snapshots:", [s[:8] for s in snaps], "| refs/main:", ref[:8])
        for fn in ("model.safetensors", "tokenizer.json", "modules.json", "README.md"):
            hs = [hashlib.sha256((snapdir / s / fn).read_bytes()).hexdigest() for s in snaps]
            print(f"  {fn:18s} sha256 {[h[:8] for h in hs]} identical: {len(set(hs)) == 1}")
        weights = {s: hashlib.sha256((snapdir / s / "model.safetensors").read_bytes()).hexdigest() for s in snaps}
        print("embed_hash with revision = each snapshot (all else v0):",
              {s[:8]: m.embed_hash({"provider": "sentence_transformers", "model_id": m.L6, "revision": s,
                                    "input_type": {"documents": "none", "queries": "none"}, "preproc_version": "none",
                                    "normalize": True}) for s in snaps},
              "| weights_sha256 equal:", len(set(weights.values())) == 1)

        # ------------------------------------------------------------------ K6
        head("K6 duplicates and near-duplicates in the v0 index (L6 vectors)")
        hs = [c["text_sha256"] for c in chunks]
        print(f"equal text_sha256 pairs: {N - len(set(hs))}")
        S = V384 @ V384.T
        iu = np.triu_indices(N, 1)
        pv = S[iu]
        for th in (0.98, 0.95, 0.90, 0.85, 0.80):
            print(f"  pairs with cosine >= {th:.2f}: {int((pv >= th).sum())}")
        top = np.argsort(-pv, kind="stable")[:3]
        print("top 3 pairs (seq, seq, page, page, cosine):",
              [(int(iu[0][j]), int(iu[1][j]), chunks[iu[0][j]]["page_segments"][0]["page"],
                chunks[iu[1][j]]["page_segments"][0]["page"], f4(pv[j])) for j in top])
        # a duplicate made on purpose (TOY edit): copy chunk 27's text into a 98th record
        dup = np.vstack([V384, V384[27:28]])
        print(f"toy check: append a copy of seq 27 -> equal text_sha256 pairs 1; its cosine to seq 27 "
              f"{f4(float(dup[-1] @ dup[27]))}; D-002 top-4 then holds "
              f"{sum(i in (27, N) for i in ranking(dup @ m6.encode([m.Q_D002], normalize_embeddings=True)[0])[:4])} copies")

        # ------------------------------------------------------------------ K7
        head("K7 a mixed-model index: odd rows from L3, even rows from L6, written with the L6 manifest")
        V3n, _ = m.cached_embed(texts, m.SPEC_L3, m.Counting(m3), cache1)
        mixed = V384.copy()
        odd = np.arange(1, N, 2)
        mixed[odd] = V3n[odd]
        EMB = {"provider": "sentence_transformers", "model_id": m.L6, "revision": m.SPEC_L6["revision"],
               "input_type": {"documents": "none", "queries": "none"}, "preproc_version": "none", "normalize": True,
               "dim": 384, "max_seq_length": 256}
        base = {"snapshot_id": SNAP, "docs": [{"doc_id": "climate", "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
                                               "doc_text_sha256": m.sha(full)}],
                "parser": {"backend": "pymupdf", "version": pymupdf.VersionBind}, "chunker": CFG,
                "params_hash": m.params_hash(CFG), "embedding": EMB, "embed_hash": m.embed_hash(EMB),
                "library_versions": {"numpy": vers["numpy"], "sentence-transformers": vers["sentence-transformers"],
                                     "torch": vers["torch"]}, "created_utc": "2026-10-08T00:00:00Z"}
        RUN = {"snapshot_id": SNAP, "chunker": CFG, "embedding": EMB}
        d_mix = tmp / "mixed"
        m.write_index(d_mix, chunks, mixed, base)
        try:
            Vl, _, _ = m.load_index(d_mix, RUN)
            print(f"load_index (hashes, dtype, shape, unit rows, records, manifest vs run): LOADED, no error; "
                  f"rows {Vl.shape}, max|norm-1| {np.abs(np.linalg.norm(Vl, axis=1) - 1).max():.2e}")
        except m.IndexMismatch as e:
            print("load_index refused:", e.args[0])
        # (a) recompute each row's key from the manifest and compare with the cached vector
        raw = {k: np.load(cache1 / f"{k}.npy") for k in (m.embedding_cache_key(x, **m.SPEC_L6) for x in texts)}
        cached_rows = np.stack([raw[m.embedding_cache_key(x, **m.SPEC_L6)] for x in texts])
        cached_rows = cached_rows / np.linalg.norm(cached_rows, axis=1, keepdims=True)
        diff_rows = [i for i in range(N) if not np.allclose(cached_rows[i], mixed[i], atol=1e-6)]
        print(f"(a) key recompute: rows whose cached L6 vector differs from the stored row: {len(diff_rows)} "
              f"(odd rows {len(odd)}); first five {diff_rows[:5]}")
        # (b) re-embed a fixed sample of 5 rows with the manifest's model
        rng = np.random.default_rng(0)
        sample = sorted(int(i) for i in rng.choice(N, 5, replace=False))
        fresh = m6.encode([texts[i] for i in sample], normalize_embeddings=True)
        cs = [float(fresh[j] @ mixed[i]) for j, i in enumerate(sample)]
        print(f"(b) re-embed sample (rng seed 0) rows {sample}: cosine to stored row {[f'{c:.6f}' for c in cs]}; "
              f"below 0.9999: {sum(c < 0.9999 for c in cs)} of 5")
        same = [float(V384[i] @ V3n[i]) for i in range(N)]
        print(f"cosine between L6 and L3 vectors of the same chunk: min {min(same):.4f} median {np.median(same):.4f} "
              f"max {max(same):.4f} (two spaces: the numbers are not comparable)")
        # (c) raw norms before normalisation, if recorded
        r3 = np.linalg.norm(m3.encode([texts[i] for i in odd], normalize_embeddings=False), axis=1)
        r6 = np.linalg.norm(m6.encode([texts[i] for i in range(0, N, 2)], normalize_embeddings=False), axis=1)
        print(f"(c) raw norms: even rows (L6) {r6.min():.6f}..{r6.max():.6f}; odd rows (L3) {r3.min():.4f}..{r3.max():.4f}: two groups")
        q6 = {s["qid"]: m6.encode([s["question"]], normalize_embeddings=True)[0] for s in ans}
        r_ok = [first_rel(ranking(V384 @ q6[s["qid"]]), s["qid"]) for s in ans]
        r_mx = [first_rel(ranking(mixed @ q6[s["qid"]]), s["qid"]) for s in ans]
        print(f"8 answerable draft seeds, L6 question vectors: first relevant rank, clean {r_ok} -> {summary(r_ok)}; "
              f"mixed {r_mx} -> {summary(r_mx)} (Hit@1, Hit@4 counts; MRR@10)")
        o = ranking(mixed @ q6["D-002"])
        print(f"D-002 on the mixed index: top-5 {o[:5]}, rank of seq 27 {o.index(27) + 1}")

        # ------------------------------------------------------------------ K8
        head("K8 the identity grid: which identity moves for which change (v0 = L6, 1000/200, per_page)")
        SNAP_E = snapshot_id_of({"climate": pages[:9] + [pages[9][:100] + " (edited)" + pages[9][100:]] + pages[10:]})
        EMB2 = {**EMB, "output_dimension": "none", "embedding_type": "float", "truncate": "none", "max_tokens": "none"}
        DOC_FIELDS = ("provider", "model_id", "revision", "preproc_version", "normalize", "output_dimension",
                      "embedding_type", "truncate", "max_tokens")

        def embed_hash2(e):     # the current six fields plus the four new ones (proposed; not a course decision)
            return hashlib.sha256(json.dumps({k: e[k] for k in m.EMBED_FIELDS + DOC_FIELDS[5:]}, sort_keys=True)
                                  .encode("utf-8")).hexdigest()[:12]

        def doc_key(e, text):   # the v2 key of one chunk text, document side
            return key_v2(text, {"provider": e["provider"], "model_id": e["model_id"], "revision": str(e["revision"]),
                                 "input_type": e["input_type"]["documents"], "preproc_version": e["preproc_version"],
                                 **{f: e[f] for f in DOC_FIELDS[5:]}})

        def rebuild2(man, run):
            r = []
            if man["snapshot_id"] != run["snapshot_id"]:
                r.append("snapshot")
            if m.params_hash(man["chunker"]) != m.params_hash(run["chunker"]):
                r.append("chunker")
            a, b2 = man["embedding"], run["embedding"]
            if any(a[f] != b2[f] for f in DOC_FIELDS) or a["input_type"]["documents"] != b2["input_type"]["documents"]:
                r.append("embedding")
            return r

        RUN2 = {"snapshot_id": SNAP, "chunker": CFG, "embedding": EMB2}
        L3E = {"model_id": m.L3, "revision": m.SPEC_L3["revision"]}
        scen = [
            ("nothing changed", {}), ("k 4 -> 8", {}), ("LLM model changed", {}), ("prompt v1 -> v2", {}),
            ("reranker added", {}),
            ("query input_type changed", {"embedding": {**EMB2, "input_type": {"documents": "none", "queries": "search_query"}}}),
            ("chunk size 1000 -> 2000", {"chunker": {**CFG, "chunk_size": 2000}}),
            ("overlap 200 -> 100", {"chunker": {**CFG, "chunk_overlap": 100}}),
            ("scope per_page -> cross_page", {"chunker": {**CFG, "scope": "cross_page"}}),
            ("PDF text changed", {"snapshot_id": SNAP_E}),
            ("model L6 -> L3", {"embedding": {**EMB2, **L3E}}),
            ("same model, new revision", {"embedding": {**EMB2, "revision": "0000000"}}),
            ("document input_type changed", {"embedding": {**EMB2, "input_type": {"documents": "search_document", "queries": "none"}}}),
            ("preprocessing added", {"embedding": {**EMB2, "preproc_version": "tabs_to_spaces"}}),
            ("normalize true -> false", {"embedding": {**EMB2, "normalize": False}}),
            ("snapshot AND model", {"snapshot_id": SNAP_E, "embedding": {**EMB2, **L3E}}),
            ("output_dimension -> 256", {"embedding": {**EMB2, "output_dimension": 256}}),
            ("embedding_type float -> int8", {"embedding": {**EMB2, "embedding_type": "int8"}}),
            ("truncate none -> END", {"embedding": {**EMB2, "truncate": "END"}}),
        ]
        man2 = {"snapshot_id": SNAP, "chunker": CFG, "embedding": EMB2}
        rows = []
        print(f"  {'change':32s} snapshot params embed_hash(v0) embed_hash(+4) doc_key  rebuild")
        for label, ch in scen:
            run = {**RUN2, **ch}
            e = run["embedding"]
            row = (run["snapshot_id"] != SNAP, m.params_hash(run["chunker"]) != m.params_hash(CFG),
                   m.embed_hash(e) != m.embed_hash(EMB2), embed_hash2(e) != embed_hash2(EMB2),
                   doc_key(e, texts[0]) != doc_key(EMB2, texts[0]), rebuild2(man2, run))
            rows.append([label, *row])
            yn = lambda x: "moves" if x else "  -  "
            print(f"  {label:32s} {yn(row[0])}    {yn(row[1])}  {yn(row[2])}          {yn(row[3])}          "
                  f"{yn(row[4])}    {row[5] if row[5] else 'reuse'}")
        print("grid fingerprint:", m.fp(rows), "| rows:", len(rows))
        same16 = all(rebuild2(man2, {**RUN2, **ch}) == m.rebuild_reasons(
            {"snapshot_id": SNAP, "chunker": CFG, "params_hash": m.params_hash(CFG), "embedding": EMB},
            {**RUN2, **ch, "embedding": {k: v for k, v in ({**RUN2, **ch}["embedding"]).items()}}) for _, ch in scen[:16])
        print("the first 16 rows give the same decisions as c3_measure.rebuild_reasons (S7):", same16)
        print("note: the first five rows are query-time changes; the run config's embedding block is unchanged for them")

        # ------------------------------------------------------------------ K9
        head("K9 a local canary: 3 fixed sentences, embedded twice (cache bypassed), and batch-size noise")
        canary = ["Greenhouse gases trap heat in the atmosphere.", "The Paris Agreement was adopted in 2015.",
                  "Renewable energy sources include solar and wind power."]
        a = m6.encode(canary, normalize_embeddings=True)
        b2 = m6.encode(canary, normalize_embeddings=True)
        print(f"same model twice: min cosine {min(float(x @ y) for x, y in zip(a, b2)):.9f}; bit-identical {np.array_equal(a, b2)}")
        a64 = m6.encode(texts, batch_size=64, normalize_embeddings=True)
        a1 = m6.encode(texts, batch_size=1, normalize_embeddings=True)
        c = np.sum(a64 * a1, axis=1)
        print(f"batch 64 vs batch 1 over the 97 chunks: min cosine {c.min():.9f}; 1 - min = {1 - c.min():.2e}")
        aR = SentenceTransformer(m.L6, device="cpu", revision=sorted(p.name for p in snapdir.iterdir())[1]).encode(canary, normalize_embeddings=True)
        print(f"the other cached snapshot (c9745ed1) on the canary: min cosine to refs/main {min(float(x @ y) for x, y in zip(a, aR)):.9f}")
        a3 = m3.encode(canary, normalize_embeddings=True)
        print(f"a different model (L3) on the canary: cosine to L6 {[f4(float(x @ y)) for x, y in zip(a, a3)]}")

        # ------------------------------------------------------------------ K10
        head("K10 the old-cache rule: v1 entries are read as if they carry the server defaults")
        print("Foundation correction (research phase notes): an old v1 Cohere entry was produced with output_dimension 1536, "
              "embedding_type float, truncate END; mapping it to the v2 key with those values keeps it valid:")
        old = {"provider": "cohere", "model_id": "embed-v4.0", "revision": "none", "input_type": "search_document",
               "preproc_version": "none"}
        as_v2 = {**old, "output_dimension": 1536, "embedding_type": "float", "truncate": "END", "max_tokens": "none"}
        print(f"  v1 key {m.embedding_cache_key('x', **old)[:12]}… -> v2 key with defaults {key_v2('x', as_v2)[:12]}…; "
              f"a v2 request with truncate NONE has another key: {key_v2('x', as_v2) != key_v2('x', {**as_v2, 'truncate': 'NONE'})}")
        print("\nDONE")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
