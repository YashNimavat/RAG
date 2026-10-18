"""I-CMP: measurements K1-K12 for the granularity-family lesson, notebook, tool and quiz (offline, 0 API calls).

What this measures, on Corpus D (the course's climate PDF, PyMuPDF text, pages joined with "\\n"):
  K1  environment and corpus identity
  K2  units: characters per token for four tokenizers, regex "words", I3-regex sentences, I6a word windows
  K3  the heading tree from font size + bold (PyMuPDF "dict"); repeated heading names
  K4  every buildable arm: N, size distribution in characters and MiniLM WordPiece tokens, truncation shares,
      index bytes (v0, I1 grid points, pages, uncapped sections, an I3-style semantic probe)
  K5  the deterministic I5 header on v0's chunks: distinct values, token share, truncation
  K6  retrieval on the 8 answerable draft seeds per arm (MiniLM, exact cosine): ranks, Hit@4, MRR@10,
      CE@4 at fixed k = 4 and at an equal token budget B (07 I.2 take_within_budget), realized tokens, unique chars
  K7  paired comparison of each arm with v0 on the seeds: discordant counts, Δ CE@4, paired bootstrap CI
  K8  comparability: the comparison-key check refuses a subset run and accepts the champion rerun on its qids
  K9  family statistics: FWER, Holm thresholds and a worked Holm, MDE at the dev n
  K10 the cost ladder on Corpus D (index-time LLM calls, input tokens, embeds, vectors, bytes, USD)
  K11 the I6 vs Q2 crossover arithmetic
  K12 a toy: duplicate parents eating an equal budget (HyPE-style multi-vector, made-up numbers)
The draft seeds are `llm-draft` (06 §6.7): every rank and CE value here is an OBSERVATION, never a result.

Run from rag_learning/ (Git Bash), offline caches already present:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I-CMP/icmp_kit_measure.py \\
        "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \\
        > sources/verification/I-CMP/out_icmp_kit_measure.txt 2> sources/verification/I-CMP/out_icmp_kit_measure.stderr.txt
"""
from __future__ import annotations

import bisect
import hashlib
import importlib.metadata as md
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import pymupdf
import tiktoken

WS = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WS / "study" / "tools"))
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
from embed_fit_check import recursive_spans  # noqa: E402  (07 H.1, reproduces v0's 97 chunks)

PDF = Path(sys.argv[1])
SEEDS = WS / "study" / "tools" / "examples" / "climate_seed_spans.jsonl"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SENT_RE = re.compile(r"(?<=[.?!])\s+")          # I3's splitter (research I3 §6; LangChain SemanticChunker)
WORD_RE = re.compile(r"\b\w+\b")                # document_augmentation cell 6 "tokens"
L_MINILM = 256


def sec(name):
    print(f"\n=== {name} ===")


def q(xs, p):
    """Nearest-rank percentile (p in 0..100) of a sorted copy."""
    s = sorted(xs)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)]


def dist(xs):
    return f"min {min(xs)} / median {statistics.median(xs):g} / p95 {q(xs, 95)} / max {max(xs)} / mean {sum(xs) / len(xs):.1f}"


# ---------------------------------------------------------------------------------------------------- K1
sec("K1 environment and corpus")
print("python", sys.version.split()[0])
for p in ("pymupdf", "numpy", "tiktoken", "tokenizers", "transformers", "sentence-transformers", "torch"):
    print(p, md.version(p))
raw = PDF.read_bytes()
print("pdf sha256", hashlib.sha256(raw).hexdigest(), "bytes", len(raw))
doc = pymupdf.open(PDF)
pages = [pg.get_text() for pg in doc]
doc_text = "\n".join(pages)
starts = []
pos = 0
for pg in pages:
    starts.append(pos)
    pos += len(pg) + 1
print("pages", len(pages), "chars", len(doc_text), "page length", dist([len(p) for p in pages]))
assert len(pages) == 33 and len(doc_text) == 72593

# ---------------------------------------------------------------------------------------------------- tokenizers
from tokenizers import Tokenizer  # noqa: E402
from huggingface_hub import snapshot_download  # noqa: E402

snap = Path(snapshot_download(MODEL, local_files_only=True))
wp = Tokenizer.from_file(str(snap / "tokenizer.json"))
wp.no_truncation()
wp.no_padding()
ENC = {n: tiktoken.get_encoding(n) for n in ("cl100k_base", "o200k_harmony")}
try:
    ENC["gpt2"] = tiktoken.get_encoding("gpt2")
except Exception:                                # gpt2 and r50k_base share the same ranks in tiktoken
    ENC["gpt2"] = tiktoken.get_encoding("r50k_base")
print("gpt2 encoding loaded as", ENC["gpt2"].name)


def n_wp(text, specials=True):
    return len(wp.encode(text, add_special_tokens=specials).ids)


def n_tok(text, enc="o200k_harmony"):
    return len(ENC[enc].encode(text, disallowed_special=()))


# ---------------------------------------------------------------------------------------------------- K2
sec("K2 units")
tot = {"WordPiece (no specials)": n_wp(doc_text, False)}
for n in ("cl100k_base", "gpt2", "o200k_harmony"):
    tot[n] = n_tok(doc_text, n)
for n, v in tot.items():
    print(f"{n}: {v} tokens = {len(doc_text) / v:.2f} chars/token")
words = WORD_RE.findall(doc_text)
print("regex words \\b\\w+\\b:", len(words), f"= {len(doc_text) / len(words):.2f} chars/word")


def sentence_spans(text):
    out, i = [], 0
    for m in SENT_RE.finditer(text):
        if m.start() > i:
            out.append((i, m.start()))
        i = m.end()
    if i < len(text):
        out.append((i, len(text)))
    return [(a, b) for a, b in out if text[a:b].strip()]


sents = sentence_spans(doc_text)
slen = [b - a for a, b in sents]
print("I3 regex sentences (document scope):", len(sents), "chars", dist(slen))
print("segments under 20 chars:", sum(x < 20 for x in slen))


def word_windows(n_words, size, overlap):
    """document_augmentation cell 6 split_document: windows of `size` words, step size - overlap."""
    return len(range(0, n_words, size - overlap))


print("I6a document-level windows 4000/100 words:", word_windows(len(words), 4000, 100),
      "· fragments 128/16 words:", word_windows(len(words), 128, 16))
g = ENC["gpt2"].encode(doc_text)
print("I4 base chunks, gpt2-token windows 200/50 (from_tiktoken_encoder-style count):", len(range(0, len(g), 150)))

# ---------------------------------------------------------------------------------------------------- K3
sec("K3 heading tree (size + bold)")
LEVEL = {24.0: "title", 18.0: "chapter", 13.56: "section", 12.0: "sub"}
heads = []                                      # (level, text, page_no)
for pno, pg in enumerate(doc, 1):
    for b in pg.get_text("dict")["blocks"]:
        prev = None
        for ln in b.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if not sp or not all(s["flags"] & 16 for s in sp):
                prev = None
                continue
            size = round(sp[0]["size"], 2)
            txt = " ".join("".join(s["text"] for s in ln["spans"]).split())
            if prev is not None and prev[0] == LEVEL[size] and prev[2] == pno:   # a heading wrapped onto two lines
                heads[-1] = (prev[0], prev[1] + " " + txt, pno)
            else:
                heads.append((LEVEL[size], txt, pno))
            prev = heads[-1]
cnt = {lv: sum(h[0] == lv for h in heads) for lv in ("title", "chapter", "section", "sub")}
print("headings by level:", cnt, "total", len(heads))
print("bold at body size (12 pt):", cnt["sub"], f"of {len(heads) - 1} below the title = {cnt['sub'] / (len(heads) - 1):.0%}")
names = {}
for lv, t, p in heads:
    names.setdefault(t.lower(), []).append((lv, p))
rep = {k: v for k, v in names.items() if len(v) > 1}
print("heading names that repeat:", len(rep))
for k in sorted(rep):
    print("  ", k, rep[k])
# map headings to doc_text offsets (search forward in reading order)
hpos, cur = [], 0
for lv, t, p in heads:
    pat = re.compile(r"\s+".join(map(re.escape, t.split())))
    m = pat.search(doc_text, max(cur, starts[p - 1]))
    assert m, t
    hpos.append((m.start(), lv, t, p))
    cur = m.end()
print("headings located in doc_text:", len(hpos), "of", len(heads))
glued = 0
for o, lv, t, p in hpos:
    j = bisect.bisect_right([a for a, b in sents], o) - 1
    a, b = sents[j]
    if a <= o < b and doc_text[a:o].strip():
        glued += 1
print("headings glued inside an I3 regex sentence (not at its start):", glued, "of", len(hpos))

# ---------------------------------------------------------------------------------------------------- K4
sec("K4 arms and size distributions")


def per_page_chunks(size, overlap):
    out = []
    for pi, pg in enumerate(pages):
        for a, b in recursive_spans(pg, size, overlap):
            if pg[a:b].strip():
                out.append((starts[pi] + a, starts[pi] + b))
    return out


def section_units(levels=("title", "chapter", "section")):
    cuts = sorted({0} | {o for o, lv, t, p in hpos if lv in levels})
    out = [(a, b) for a, b in zip(cuts, cuts[1:] + [len(doc_text)]) if doc_text[a:b].strip()]
    return out


ARMS = {
    "v0 recursive 1000/200 per page": per_page_chunks(1000, 200),
    "I1 grid 500/100": per_page_chunks(500, 100),
    "I1 grid 1500/300": per_page_chunks(1500, 300),
    "I1 grid 2000/400": per_page_chunks(2000, 400),
    "page (one unit per page)": [(starts[i], starts[i] + len(p)) for i, p in enumerate(pages)],
    "sections, uncapped (chapter + section headings)": section_units(),
}

# I3-style semantic probe: MiniLM sentence-window embeddings, buffer 1, percentile 90, document scope, no size cap
from sentence_transformers import SentenceTransformer  # noqa: E402

model = SentenceTransformer(MODEL, device="cpu")
win = [" ".join(doc_text[a:b] for a, b in sents[max(0, i - 1): i + 2]) for i in range(len(sents))]
E = model.encode(win, normalize_embeddings=True, batch_size=64)
dists = 1 - np.sum(E[:-1] * E[1:], axis=1)
thr = float(np.percentile(dists, 90))
brk = [i for i, d in enumerate(dists) if d > thr]
groups, s0 = [], 0
for i in brk:
    groups.append((sents[s0][0], sents[i][1]))
    s0 = i + 1
groups.append((sents[s0][0], sents[-1][1]))
ARMS["I3 probe: semantic, MiniLM, p90, uncapped"] = groups
print(f"I3 probe: {len(sents)} sentence windows embedded, {len(dists)} distances, threshold (p90) {thr:.4f},",
      f"{len(brk)} breakpoints -> {len(groups)} chunks")

SIZE = {}
for name, spans in ARMS.items():
    texts = [doc_text[a:b] for a, b in spans]
    ch = [len(t) for t in texts]
    wpn = [n_wp(t) for t in texts]
    oh = [n_tok(t) for t in texts]
    cross = sum(1 for a, b in spans if bisect.bisect_right(starts, a) != bisect.bisect_right(starts, max(a, b - 1)))
    SIZE[name] = {"n": len(spans), "chars": ch, "wp": wpn, "o200k": oh}
    print(f"{name}: N {len(spans)}")
    print(f"   chars {dist(ch)}")
    print(f"   WordPiece incl. specials {dist(wpn)}")
    print(f"   o200k_harmony {dist(oh)} · cl100k mean {sum(n_tok(t, 'cl100k_base') for t in texts) / len(texts):.1f}")
    print(f"   over 256 (MiniLM cap): {sum(x > 256 for x in wpn)} = {sum(x > 256 for x in wpn) / len(wpn):.1%}",
          f"· over 128: {sum(x > 128 for x in wpn)} · over 512: {sum(x > 512 for x in wpn)}",
          f"· chars past the 256 cap: {sum(len(t) - wp.encode(t, add_special_tokens=False).offsets[253][1] for t, x in zip(texts, wpn) if x > 256)}")
    print(f"   stored chars / doc chars {sum(ch) / len(doc_text):.3f} · units crossing a page break {cross}")
    print(f"   index bytes: 384-d {128 + len(spans) * 384 * 4:,} · 1536-d {128 + len(spans) * 1536 * 4:,}")

# ---------------------------------------------------------------------------------------------------- K5
sec("K5 deterministic I5 header on v0's chunks")
v0 = ARMS["v0 recursive 1000/200 per page"]
hoff = [h[0] for h in hpos]


def path_at(off):
    path = {}
    for o, lv, t, p in hpos:
        if o > off:
            break
        if lv == "title":
            path = {"title": t}
        elif lv == "chapter":
            path = {"title": path.get("title"), "chapter": t}
        elif lv == "section":
            path = {k: path.get(k) for k in ("title", "chapter")} | {"section": t}
    return " > ".join(v for v in (path.get("title"), path.get("chapter"), path.get("section")) if v)


title_h = [heads[0][1]] * len(v0)
path_h = [path_at(a) for a, b in v0]
print("title header distinct values:", len(set(title_h)), "of", len(v0))
print("path header (title > chapter > section at the chunk start) distinct values:", len(set(path_h)), "of", len(v0))
print("example (seq 27):", path_h[27])
hw = [n_wp(h + "\n", False) for h in path_h]
cw = [n_wp(doc_text[a:b]) for a, b in v0]
share = [h / (h + c) for h, c in zip(hw, cw)]
print("path header WordPiece tokens", dist(hw), "· share h/(h+c)", f"mean {sum(share) / len(share):.3f} max {max(share):.3f}")
print("chunks over 256 after prepending the path:", sum(h + c > 256 for h, c in zip(hw, cw)))
print("embeds needed: all", len(v0), "(new text = new cache keys); LLM calls 0")

# ---------------------------------------------------------------------------------------------------- K6
sec("K6 retrieval on the 8 answerable draft seeds (observation, not a result)")
seeds = [json.loads(x) for x in SEEDS.read_text(encoding="utf-8").splitlines() if x.strip()]
ans = [s for s in seeds if s["answerable"]]
print("seeds", len(seeds), "answerable", len(ans), [s["qid"] for s in ans])
GROUPS = {s["qid"]: [[[(starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                       for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]] for s in ans}


def covered(segs, chunks):
    tot = hit = 0
    for a, b in segs:
        for i in range(a, b):
            if doc_text[i].isspace():
                continue
            tot += 1
            hit += any(x <= i < y for x, y in chunks)
    return 1.0 if tot == 0 else hit / tot


def ce(qid, chunks):
    return int(all(max(covered(alt, chunks) for alt in g) == 1.0 for g in GROUPS[qid]))


def span_cov(qid, chunks):
    gs = [max(covered(alt, chunks) for alt in g) for g in GROUPS[qid]]
    return sum(gs) / len(gs)


def relevant(qid, span):
    x, y = span
    return any(not doc_text[i].isspace() for g in GROUPS[qid] for alt in g for a, b in alt for i in range(max(a, x), min(b, y)))


def take_within_budget(ranked, ntok, budget):   # 07 I.2, verbatim logic (`break` at the first chunk that does not fit)
    kept, used = [], 0
    for c in ranked:
        if used + ntok[c] > budget:
            break
        kept.append(c)
        used += ntok[c]
    return kept, used


Q = model.encode([s["question"] for s in ans], normalize_embeddings=True)
RANK = {}
for name, spans in ARMS.items():
    V = model.encode([doc_text[a:b] for a, b in spans], normalize_embeddings=True, batch_size=64)
    S_ = Q @ V.T
    RANK[name] = [sorted(range(len(spans)), key=lambda j, r=r: (-r[j], j)) for r in S_]

v0_name = "v0 recursive 1000/200 per page"
ntok_v0 = SIZE[v0_name]["o200k"]
ctx4 = [sum(ntok_v0[j] for j in RANK[v0_name][i][:4]) for i in range(len(ans))]
B = round(sum(ctx4) / len(ctx4))
print("v0 top-4 context o200k_harmony tokens per seed:", ctx4, "-> B = mean =", B)
RES = {}
for name, spans in ARMS.items():
    ntok = SIZE[name]["o200k"]
    rows = {"rank": [], "ce4": [], "cov4": [], "ceB": [], "kB": [], "usedB": [], "tok4": [], "uniq4": [], "uniqB": []}
    for i, s in enumerate(ans):
        order = RANK[name][i]
        fr = next((r + 1 for r, j in enumerate(order) if relevant(s["qid"], spans[j])), None)
        rows["rank"].append(fr)
        top4 = [spans[j] for j in order[:4]]
        rows["ce4"].append(ce(s["qid"], top4))
        rows["cov4"].append(span_cov(s["qid"], top4))
        rows["tok4"].append(sum(ntok[j] for j in order[:4]))
        cov = set()
        for a, b in top4:
            cov.update(range(a, b))
        rows["uniq4"].append(len(cov))
        kept, used = take_within_budget(order, ntok, B)
        kc = [spans[j] for j in kept]
        rows["ceB"].append(ce(s["qid"], kc) if kc else 0)
        rows["kB"].append(len(kept))
        rows["usedB"].append(used)
        cov = set()
        for a, b in kc:
            cov.update(range(a, b))
        rows["uniqB"].append(len(cov))
    RES[name] = rows
    hit4 = sum(r is not None and r <= 4 for r in rows["rank"])
    mrr = sum(1 / r for r in rows["rank"] if r is not None and r <= 10) / len(ans)
    print(f"{name}:")
    print(f"   first relevant rank {rows['rank']} · Hit@4 {hit4}/8 · MRR@10 {mrr:.3f}")
    print(f"   fixed k=4: CE@4 {rows['ce4']} = {sum(rows['ce4'])}/8 · Span-Coverage@4 mean {sum(rows['cov4']) / 8:.3f}",
          f"· context tokens mean {sum(rows['tok4']) / 8:.0f} · unique chars mean {sum(rows['uniq4']) / 8:.0f}")
    print(f"   equal budget B={B}: k per seed {rows['kB']} (mean {sum(rows['kB']) / 8:.2f}) · CE@B {rows['ceB']} = {sum(rows['ceB'])}/8",
          f"· realized tokens mean {sum(rows['usedB']) / 8:.0f} (min {min(rows['usedB'])}, max {max(rows['usedB'])}) · unique chars mean {sum(rows['uniqB']) / 8:.0f}")
    print(f"   largest unit {max(ntok)} o200k tokens; B >= largest unit: {B >= max(ntok)}")

# ---------------------------------------------------------------------------------------------------- K7
sec("K7 paired comparison with v0 on the seeds (CE@4, fixed k and equal budget)")
import contracts_check as cc  # noqa: E402

qids = [s["qid"] for s in ans]
for metric in ("ce4", "ceB"):
    base = dict(zip(qids, RES[v0_name][metric]))
    for name in ARMS:
        if name == v0_name:
            continue
        arm = dict(zip(qids, RES[name][metric]))
        b_ = sum(base[x] == 1 and arm[x] == 0 for x in qids)
        c_ = sum(base[x] == 0 and arm[x] == 1 for x in qids)
        m, (lo, hi) = cc.ref_paired_bootstrap(base, arm, n_boot=2000, seed=0)
        verdict = "CI spans 0" if lo <= 0 <= hi else ("CI above 0" if lo > 0 else "CI below 0")
        nd = b_ + c_
        p_ex = min(1.0, 2 * sum(math.comb(nd, i) for i in range(min(b_, c_) + 1)) / 2 ** nd) if nd else 1.0
        print(f"{metric} {name}: b (v0 only) {b_}, c (arm only) {c_}, Δ {m:+.3f}, bootstrap 95% CI [{lo:+.3f}, {hi:+.3f}] ({verdict}),"
              f" exact McNemar two-sided p {p_ex:.4f}")
print("MDE at n = 8, b + c = 4: 2.8*sqrt(4)/8 =", round(2.8 * 2 / 8, 3))

# ---------------------------------------------------------------------------------------------------- K8
sec("K8 comparability: a subset run against the full run")
common = dict(dataset_sha256="d" * 64, snapshot_id="ea07572562ac", labels_sha256="l" * 64, split="dev", scorer_version="1")
full = cc.make_comparison_meta(qids=qids, **common)
subset_q = [x for x in qids if x in ("D-002", "D-003", "D-004")]
sub = cc.make_comparison_meta(qids=subset_q, **common)
try:
    cc.comparison_keys_match(full, sub)
    print("full vs subset: ACCEPTED (unexpected)")
except ValueError as e:
    print("full vs subset: REFUSED:", e)
rerun = cc.make_comparison_meta(qids=list(reversed(subset_q)), **common)
print("subset vs champion rerun on the subset qids (order reversed):", cc.comparison_keys_match(sub, rerun))

# ---------------------------------------------------------------------------------------------------- K9
sec("K9 family statistics (FORMULA)")
for m in (1, 3, 5, 12, 37, 48):
    print(f"FWER at alpha 0.05, m = {m}: {1 - 0.95 ** m:.4f}")
print("Holm thresholds, 3 arms: ", [round(0.05 / (3 - i), 4) for i in range(3)])
pv = {"A1": 0.030, "A2": 0.012, "A3": 0.200}                # toy p-values
order = sorted(pv, key=pv.get)
dec, stop = {}, False
for i, a in enumerate(order):
    t = 0.05 / (len(pv) - i)
    ok = not stop and pv[a] <= t
    stop = stop or not ok
    dec[a] = (pv[a], round(t, 4), "reject H0" if ok else "keep H0")
print("Holm on toy p-values", dec)
print("Bonferroni on the same toy: threshold", round(0.05 / 3, 4), {a: ("reject" if p <= 0.05 / 3 else "keep") for a, p in pv.items()})
for n, bc in ((12, 4), (16, 4), (12, 9), (40, 9), (8, 4)):
    print(f"MDE ≈ 2.8*sqrt(b+c)/n, n = {n}, b + c = {bc}: {2.8 * math.sqrt(bc) / n:.4f}")
print("one item on n = 12 moves CE by", round(1 / 12, 4))

# ---------------------------------------------------------------------------------------------------- K10
sec("K10 cost ladder on Corpus D (DERIVED from the counts above; prices LLMOPS §6.2, checked 2026-10-17)")
N = len(v0)
doc_cl = n_tok(doc_text, "cl100k_base")
mean_chunk_cl = sum(n_tok(doc_text[a:b], "cl100k_base") for a, b in v0) / N
PROMPT = 100                                    # ASSUMPTION: instruction tokens per context call
i5_in = N * (doc_cl + mean_chunk_cl + PROMPT)
print(f"N v0 chunks {N}; S sentences {len(sents)}; doc cl100k tokens {doc_cl}; mean chunk cl100k {mean_chunk_cl:.1f}")
print(f"I3: embeds S + N = {len(sents)} + {N} = {len(sents) + N}; Cohere calls at 96 texts each ceil(S/96) + ceil(N/96) = {math.ceil(len(sents) / 96) + math.ceil(N / 96)}")
base4 = len(range(0, len(g), 150))
for per in (10,):
    P = base4 * per
    print(f"I4 (ASSUMPTION {per} propositions per 200-gpt2-token chunk): generate calls {base4}, grade calls per proposition {P},"
          f" total {base4 + P}; embeds {P}; vectors {P}; bytes 1536-d {128 + P * 1536 * 4:,}")
print(f"I5 deterministic header: LLM calls 0; embeds {N}")
print(f"I5 per-chunk context (whole document in each call): calls {N}; input tokens ≈ {N} × ({doc_cl} + {mean_chunk_cl:.0f} + {PROMPT}) = {i5_in:,.0f}")
print(f"   Groq gpt-oss-20b at $0.075/M: ${i5_in * 0.075 / 1e6:.3f} · Haiku 5.5 at $0.10/M: ${i5_in * 0.10 / 1e6:.3f}",
      f"· one request ≈ {doc_cl + mean_chunk_cl + PROMPT:,.0f} tokens vs an 8,000 TPM limit: fits = {doc_cl + mean_chunk_cl + PROMPT <= 8000}")
nw = word_windows(len(words), 4000, 100)
nf = word_windows(len(words), 128, 16)
wtoks = []
wd = [m.start() for m in WORD_RE.finditer(doc_text)] + [len(doc_text)]
for st in range(0, len(words), 3900):
    seg = doc_text[wd[st]: wd[min(st + 4000, len(words))]]
    wtoks.append(n_tok(seg, "cl100k_base"))
print(f"I6a input tokens ≈ Σ window cl100k tokens {sum(wtoks):,} + {nw} × {PROMPT} = {sum(wtoks) + nw * PROMPT:,}")
print(f"I6b HyPE input tokens ≈ {N} × ({mean_chunk_cl:.0f} + {PROMPT}) = {N * (mean_chunk_cl + PROMPT):,.0f}")
print(f"I6a document level: LLM calls {nw} (one per 4,000-word window); fragments {nf}; questions 40 per window -> {40 * nw}; vectors {nf} + {40 * nw} = {nf + 40 * nw}")
for qn in (5, 8):
    print(f"I6b HyPE: LLM calls {N}; q = {qn} questions per chunk -> vectors {N * qn}; bytes 1536-d {128 + N * qn * 1536 * 4:,}; 384-d {128 + N * qn * 384 * 4:,}")
print("v0 index bytes at 1536-d", f"{128 + N * 1536 * 4:,}", "(C3 S6: 596,096)")

# ---------------------------------------------------------------------------------------------------- K11
sec("K11 I6 (index-time) vs Q2 (query-time) calls (FORMULA)")
for qtot, reb in ((50, 1), (500, 1), (500, 12), (5000, 12)):
    idx = N * reb
    print(f"Q_total {qtot}, rebuilds {reb}: index-side {idx} calls vs query-side {qtot} -> cheaper: {'index-side' if idx < qtot else 'query-side'}")
print("with replay caching, repeated eval runs of either cost 0 new calls")

# ---------------------------------------------------------------------------------------------------- K12
sec("K12 TOY: duplicate parents and the budget")
toy_rank = ["q→P3", "q→P3", "q→P7", "q→P3", "q→P1", "q→P7", "q→P2"]   # 7 question vectors, parents in rank order
ptok = {"P1": 160, "P2": 150, "P3": 170, "P7": 140}
naive, used = [], 0
for h in toy_rank:
    p = h.split("→")[1]
    if used + ptok[p] > 640:
        break
    naive.append(p)
    used += ptok[p]
print("no dedup, B = 640:", naive, "used", used, "distinct", len(set(naive)))
seen, ded = [], []
for h in toy_rank:
    p = h.split("→")[1]
    if p not in seen:
        seen.append(p)
kept, used = take_within_budget(seen, ptok, 640)
print("dedup parents first, B = 640:", kept, "used", used, "distinct", len(kept))
print("\nDONE")
