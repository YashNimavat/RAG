"""P2 (information-retrieval framing) measurements: every number in concepts/P2_ir_framing.md comes from this run.

Local only: no Groq or Cohere calls, no .env read. The MiniLM model is loaded from the local Hugging Face
cache (offline mode is forced below). The toy corpus is p2_toy_corpus.json in this folder (written for P2).

Run from rag_learning/ (Git Bash or PowerShell):
    uv run python sources/verification/P2/p2_measure.py "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/P2/out_p2_measure.txt  (sections S1..S11 for P2_FACTS.md)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")          # never hit the network for the HF model
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import hashlib
import importlib.metadata as md
import inspect
import json
import re
import sys
from collections import Counter

import numpy as np
import pymupdf as fitz                                # pinned 1.26.7

PDF = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
TOY = os.path.join(HERE, "p2_toy_corpus.json")
MINILM = "sentence-transformers/all-MiniLM-L6-v2"


def head(title):
    print(f"\n=== {title}")


def _fp(x):
    """Same fingerprint as the lab's CHECK cells."""
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- S1 environment and toy corpus
head("S1 environment and toy corpus")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "numpy", "sentence-transformers", "transformers", "torch", "rank-bm25")})
raw = open(TOY, "rb").read()
print("toy corpus file sha256", hashlib.sha256(raw).hexdigest())
toy = json.loads(raw)
DOCS, QUERIES = toy["docs"], toy["queries"]
GRADE = {(r["qid"], r["did"]): r["grade"] for r in toy["qrels"]}
print(f"docs={len(DOCS)} queries={len(QUERIES)} listed qrels={len(toy['qrels'])} "
      f"pairs={len(DOCS) * len(QUERIES)} (unlisted pairs are grade 0)")
print("fp(DOCS)", _fp(DOCS), "fp(QUERIES)", _fp(QUERIES))


# ---------------------------------------------------------------- S2 tokenization
def tokenize(text):
    """Lowercase; a token is a maximal run of a-z or 0-9; everything else separates tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


head("S2 tokenization (lowercase, runs of [a-z0-9]; no stemming, no stopword list)")
toks = {d: tokenize(t) for d, t in DOCS.items()}
for d in sorted(toks):
    print(f"{d} {len(toks[d]):2d} tokens, {len(set(toks[d])):2d} distinct: {toks[d]}")
print("unit test tokenize('Sea-level RISE, 2019!') ->", tokenize("Sea-level RISE, 2019!"))
print("total tokens", sum(len(v) for v in toks.values()))
for q in sorted(QUERIES):
    print(f"{q} tokens {tokenize(QUERIES[q])}")


# ---------------------------------------------------------------- S3 inverted index
def build_index(docs_tokens):
    idx = {}
    for d in sorted(docs_tokens):
        for term in sorted(set(docs_tokens[d])):
            idx.setdefault(term, []).append(d)
    return idx


head("S3 inverted index over the 10 toy docs (term -> sorted doc ids)")
index = build_index(toks)
n_postings = sum(len(v) for v in index.values())
print(f"vocabulary size={len(index)} total postings={n_postings}")
df = {t: len(p) for t, p in index.items()}
print("terms with df >= 2:", sorted(((t, n) for t, n in df.items() if n >= 2), key=lambda x: (-x[1], x[0])))
print("df == 1 terms:", sum(1 for n in df.values() if n == 1))
for t in ("climate", "change", "of", "the", "carbon", "heat", "methane", "rise", "rising", "renewable", "energy"):
    print(f"postings[{t!r}] = {index.get(t, [])}")
print("fp(index)", _fp(index))
# brute-force cross-check: postings equal a scan of every doc
assert all(index[t] == sorted(d for d in toks if t in toks[d]) for t in index)
print("cross-check: every postings list equals a full scan of the docs: OK")


# ---------------------------------------------------------------- S4 Boolean AND / OR
def search_or(query, idx):
    out = set()
    for t in set(tokenize(query)):
        out |= set(idx.get(t, []))
    return sorted(out)


def search_and(query, idx):
    terms = set(tokenize(query))
    if not terms:
        return []
    out = None
    for t in terms:
        p = set(idx.get(t, []))
        out = p if out is None else out & p
    return sorted(out)


head("S4 Boolean retrieval with the index")
AND = {q: search_and(QUERIES[q], index) for q in sorted(QUERIES)}
OR = {q: search_or(QUERIES[q], index) for q in sorted(QUERIES)}
for q in sorted(QUERIES):
    terms = sorted(set(tokenize(QUERIES[q])))
    touched = sum(df.get(t, 0) for t in terms)
    missing = [t for t in terms if t not in index]
    print(f"{q} {QUERIES[q]!r}: AND={AND[q]} OR={OR[q]} postings touched={touched} of {len(DOCS)} docs; "
          f"terms not in index={missing}")
print("search_and('', index) ->", search_and("", index), "| search_or('photosynthesis', index) ->",
      search_or("photosynthesis", index))
print("fp(AND)", _fp(AND), "fp(OR)", _fp(OR))


# ---------------------------------------------------------------- S5 ranked retrieval from the index
def rank_by_overlap(query, idx):
    """Score = number of distinct query terms in the doc, accumulated from postings. Ties: doc id ascending.
    Only docs with score >= 1 are returned (the candidates the index can find)."""
    acc = Counter()
    for t in set(tokenize(query)):
        for d in idx.get(t, []):
            acc[d] += 1
    return sorted(acc.items(), key=lambda x: (-x[1], x[0]))


head("S5 overlap ranking (distinct query terms matched), from the index")
LEX = {q: rank_by_overlap(QUERIES[q], index) for q in sorted(QUERIES)}
for q in sorted(QUERIES):
    print(f"{q}: {LEX[q]}")
print("fp(LEX)", _fp(LEX))


# ---------------------------------------------------------------- S6 dense similarity (MiniLM cosine)
head("S6 dense similarity: MiniLM cosine over all 10 docs (toy illustration)")
from sentence_transformers import SentenceTransformer  # noqa: E402

model = SentenceTransformer(MINILM, device="cpu")
dids = sorted(DOCS)
qids = sorted(QUERIES)
D = model.encode([DOCS[d] for d in dids], normalize_embeddings=True)
Q = model.encode([QUERIES[q] for q in qids], normalize_embeddings=True)
S = Q @ D.T
DENSE = {}
for i, q in enumerate(qids):
    order = sorted(range(len(dids)), key=lambda j: (-S[i, j], dids[j]))
    DENSE[q] = [(dids[j], round(float(S[i, j]), 4)) for j in order]
    print(f"{q}: " + ", ".join(f"{d} {s:.4f}" for d, s in DENSE[q]))
print("embedding dim", D.shape[1], "| norms ~1:", bool(np.allclose(np.linalg.norm(D, axis=1), 1, atol=1e-5)))


# ---------------------------------------------------------------- S7 qrels
head("S7 reference qrels (guideline v1; grade >= 1 = relevant)")
REL = {q: sorted(d for d in dids if GRADE.get((q, d), 0) >= 1) for q in qids}
for q in qids:
    graded = {d: GRADE[(q, d)] for d in dids if GRADE.get((q, d), 0) >= 1}
    print(f"{q}: relevant={REL[q]} grades={graded}")
print("relevant pairs", sum(len(v) for v in REL.values()), "of", len(qids) * len(dids))
binary_ref = sorted(_fp([q, d, int(GRADE.get((q, d), 0) >= 1)]) for q in qids for d in dids)
print("fp(binary reference hashes)", _fp(binary_ref))


# ---------------------------------------------------------------- S8 set quality vs ranking quality
def set_precision(retrieved, relevant):
    return 0.0 if not retrieved else len(set(retrieved) & set(relevant)) / len(retrieved)


def set_recall(retrieved, relevant):
    return len(set(retrieved) & set(relevant)) / len(relevant)


def first_relevant_rank(retrieved, relevant):
    for i, d in enumerate(retrieved, 1):
        if d in relevant:
            return i
    return None


head("S8 set quality vs ranking quality")
print("system  query  k  retrieved                      rel_retrieved/retrieved  /relevant  precision recall first_rel_rank")
for name, runs in (("lexical", LEX), ("dense", DENSE)):
    for q in qids:
        for k in (3, 6):
            ret = [d for d, _ in runs[q]][:k]
            r = len(set(ret) & set(REL[q]))
            print(f"{name:7s} {q:5s} {k:2d}  {str(ret):30s} {r}/{len(ret)}  /{len(REL[q])}  "
                  f"{set_precision(ret, REL[q]):.3f} {set_recall(ret, REL[q]):.3f} {first_relevant_rank(ret, REL[q])}")
for name, runs in (("lexical", LEX), ("dense", DENSE)):
    for k in (3, 6):
        rec = [set_recall([d for d, _ in runs[q]][:k], REL[q]) for q in qids]
        print(f"{name} mean set recall at k={k}: {np.mean(rec):.3f}  per query {[round(x, 3) for x in rec]}")

print("\nHand-made toy runs for q1 (relevant = {})".format(REL["q1"]))
RUNS = {"A": ["d02", "d01", "d08"], "B": ["d01", "d08", "d02"], "C": ["d01", "d03", "d09"]}
TOYRUNS = {}
for n, ret in RUNS.items():
    TOYRUNS[n] = [round(set_precision(ret, REL["q1"]), 4), round(set_recall(ret, REL["q1"]), 4),
                  first_relevant_rank(ret, REL["q1"])]
    print(f"run {n} {ret}: precision={TOYRUNS[n][0]} recall={TOYRUNS[n][1]} first_relevant_rank={TOYRUNS[n][2]}")
print("fp(TOYRUNS)", _fp(TOYRUNS))
print("edge cases: precision([])", set_precision([], REL["q1"]), "| first_relevant_rank(['d02'])",
      first_relevant_rank(["d02"], REL["q1"]))

# CR-08 probe values (lab Task 7)
lex_q1 = [d for d, _ in LEX["q1"]]
k3, k6 = set_recall(lex_q1[:3], REL["q1"]), set_recall(lex_q1[:6], REL["q1"])
den_q1 = [d for d, _ in DENSE["q1"]]
print(f"CR-08 q1 lexical: candidates={len(lex_q1)} recall@3={k3:.4f} recall@6={k6:.4f} | "
      f"dense recall@3={set_recall(den_q1[:3], REL['q1']):.4f} recall@6={set_recall(den_q1[:6], REL['q1']):.4f}")
print("fp(CR08 lexical [len, r3, r6])", _fp([len(lex_q1), round(k3, 4), round(k6, 4)]))


# ---------------------------------------------------------------- S9 the same index on the climate PDF
head("S9 inverted index over the climate PDF windows (1,000 chars, overlap 200, as in P1)")
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)
windows = [full[i:i + 1000] for i in range(0, len(full), 800)]
wids = [f"w{i:02d}" for i in range(len(windows))]
wtoks = dict(zip(wids, (tokenize(w) for w in windows)))
pindex = build_index(wtoks)
print(f"chars={len(full)} windows={len(windows)} last window chars={len(windows[-1])}")
print(f"vocabulary size={len(pindex)} total postings={sum(len(v) for v in pindex.values())} "
      f"total tokens={sum(len(v) for v in wtoks.values())}")
pdf_df = {t: len(p) for t, p in pindex.items()}
for t in ("the", "of", "and", "climate", "change", "carbon", "greenhouse", "methane", "renewable", "energy",
          "rise", "rising"):
    print(f"df[{t!r}] = {pdf_df.get(t, 0)} of {len(windows)}")
top = sorted(pdf_df.items(), key=lambda x: (-x[1], x[0]))[:10]
print("10 highest-df terms:", top)
print("df == 1 terms:", sum(1 for n in pdf_df.values() if n == 1))
for qtext in ("methane emissions", "main cause of climate change", "renewable energy"):
    terms = sorted(set(tokenize(qtext)))
    o, a = search_or(qtext, pindex), search_and(qtext, pindex)
    touched = sum(pdf_df.get(t, 0) for t in terms)
    scan = sorted(w for w in wids if set(terms) & set(wtoks[w]))
    assert scan == o
    print(f"{qtext!r}: OR candidates={len(o)} AND={len(a)} postings touched={touched} "
          f"(a full scan reads all {len(windows)} windows); OR equals the full scan: OK")
PDFFACTS = [len(windows), len(pindex), pdf_df["the"], pdf_df.get("methane", 0),
            len(search_or("methane emissions", pindex))]
print("fp(PDFFACTS [windows, vocab, df_the, df_methane, OR('methane emissions')])", _fp(PDFFACTS))


# ---------------------------------------------------------------- S10 rank_bm25: an 'index' with no inverted index
head("S10 rank_bm25.BM25Okapi internals (the library behind fusion_retrieval.ipynb cell 14)")
from rank_bm25 import BM25Okapi  # noqa: E402

bm = BM25Okapi([toks[d] for d in dids])
print("rank-bm25", md.version("rank-bm25"))
print("type(doc_freqs)", type(bm.doc_freqs).__name__, "len", len(bm.doc_freqs),
      "element type", type(bm.doc_freqs[0]).__name__, "(one term-count dict per document)")
print("has an attribute mapping term -> documents:",
      any(isinstance(v, dict) and v and isinstance(next(iter(v.values())), (list, set)) for v in vars(bm).values()))
src = inspect.getsource(BM25Okapi.get_scores)
print("get_scores loops over every document:", "for doc in self.doc_freqs" in src)
sc = bm.get_scores(tokenize(QUERIES["q4"]))
print("get_scores(q4) length", len(sc), "| docs with score != 0:", [dids[i] for i in np.nonzero(sc)[0]])


# ---------------------------------------------------------------- S11 lab fingerprints
head("S11 fingerprints used by labs/P2_ir_framing_lab.ipynb")
print("fp(tokenize per doc)", _fp([tokenize(DOCS[d]) for d in dids]))
print("fp(index)", _fp(index), "| vocab", len(index))
print("fp(AND)", _fp(AND), "| fp(OR)", _fp(OR))
print("fp(LEX)", _fp(LEX))
print("fp(TOYRUNS)", _fp(TOYRUNS))
print("fp(CR08)", _fp([len(lex_q1), round(k3, 4), round(k6, 4)]))
print("fp(PDFFACTS)", _fp(PDFFACTS))
print("binary reference hashes (one per pair, 50):")
print(json.dumps(binary_ref))
