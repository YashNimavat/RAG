"""P3 (lexical retrieval: TF-IDF and BM25) measurements: every number in concepts/P3_bm25.md comes from this run.

Local only: no Groq or Cohere calls, no .env read, no network.
Run from rag_learning/ (Git Bash or PowerShell):
    uv run python sources/verification/P3/p3_measure.py "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/P3/out_p3_measure.txt  (sections S1..S10 for P3_FACTS.md)

This file is the REFERENCE SOLUTION for labs/P3_bm25_lab.ipynb. Do not show it to the learner before an attempt (CR-04).
"""
import collections
import hashlib
import importlib.metadata as md
import inspect
import math
import re
import sys
import warnings

import numpy as np
import pymupdf as fitz                     # pinned 1.26.7
from rank_bm25 import BM25Okapi

PDF = sys.argv[1]


def head(title):
    print(f"\n=== {title}")


# ---------------------------------------------------------------- tokenizers used in the lesson
def tok_split(text):                       # the repo's tokenizer (fusion_retrieval.ipynb cells 14 and 17)
    return text.split()


def tok_lower_split(text):                 # case only
    return text.lower().split()


def tok_word(text):                        # case + punctuation, the common \w+ regex
    return re.findall(r"\w+", text.lower())


NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")


def tok_norm(text):                        # case + punctuation, but keeps 1.5 and 650,000 whole
    return NORM_RE.findall(text.lower())


def fold(t):                               # TOY plural folding. Not Porter, not Snowball.
    return t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t


def tok_norm_fold(text):
    return [fold(t) for t in tok_norm(text)]


TOKENIZERS = {"split": tok_split, "lower+split": tok_lower_split, r"lower+\w+": tok_word,
              "norm": tok_norm, "norm+fold(toy)": tok_norm_fold}


# ---------------------------------------------------------------- reference NumPy BM25 (matches rank_bm25 0.2.2 BM25Okapi)
def bm25_numpy(corpus_tokens, query_tokens, k1=1.5, b=0.75, epsilon=0.25):
    vocab = {w: j for j, w in enumerate(sorted({w for d in corpus_tokens for w in d}))}
    N, V = len(corpus_tokens), len(vocab)
    tf = np.zeros((N, V))
    for i, d in enumerate(corpus_tokens):
        for w in d:
            tf[i, vocab[w]] += 1
    dl = tf.sum(axis=1)
    avgdl = dl.mean()
    n = (tf > 0).sum(axis=0)
    idf = np.log(N - n + 0.5) - np.log(n + 0.5)
    eps = epsilon * idf.mean()                 # floor = epsilon x mean idf over ALL terms (before flooring)
    idf = np.where(idf < 0, eps, idf)          # strictly negative only: idf == 0 stays 0
    K = k1 * (1 - b + b * dl / avgdl)
    scores = np.zeros(N)
    for q in query_tokens:                     # a repeated query term is added again
        j = vocab.get(q)
        if j is None:
            continue
        f = tf[:, j]
        scores += idf[j] * f * (k1 + 1) / (f + K)
    return scores


def tf_part(f, dl_over_avgdl, k1=1.5, b=0.75):
    return f * (k1 + 1) / (f + k1 * (1 - b + b * dl_over_avgdl))


# ---------------------------------------------------------------- S1
head("S1 environment and corpus")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("rank-bm25", "numpy", "pymupdf", "scikit-learn")})
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)                    # same extraction as the acceptance suite and P1
print(f"pages={len(pages)} chars={len(full)}")

# ---------------------------------------------------------------- S2 what rank_bm25 actually computes
head("S2 rank_bm25 BM25Okapi: defaults and formulas (read from the installed source)")
import rank_bm25  # noqa: E402

print("file:", rank_bm25.__file__.split("site-packages")[-1])
print("signature:", inspect.signature(BM25Okapi.__init__))
src = inspect.getsource(BM25Okapi)
for needle in ("idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)",
               "if idf < 0:", "eps = self.epsilon * self.average_idf",
               "self.average_idf = idf_sum / len(self.idf)",
               "(q_freq * (self.k1 + 1) /", "(q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))",
               "for q in query:", "(self.idf.get(q) or 0)"):
    print(f"  source contains {needle!r}: {needle in src}")
base_src = inspect.getsource(rank_bm25.BM25._initialize)
print("  doc_len = len(document) (tokens, duplicates counted):", "self.doc_len.append(len(document))" in base_src)
print("  avgdl = total tokens / number of docs:", "self.avgdl = num_doc / self.corpus_size" in base_src)
print("  tokenizer= argument uses multiprocessing Pool:", "Pool(cpu_count())" in inspect.getsource(rank_bm25.BM25))

# ---------------------------------------------------------------- S3 toy corpus
head("S3 TOY corpus (made up for P3; the BPA story follows Ch12 p.1/14)")
TOY = [
    "BPA regulation (2019): the EU limits BPA in food-contact plastics.",
    "Climate policy and plastics: a review of chemical safety regulation.",
    "The 2019 BPA ban covers baby bottles; BPA, BPS and BPF are bisphenols.",
    "Climate change raises sea levels and flood risks for coastal cities.",
    "Greenhouse gas emissions and climate targets under the Paris Agreement.",
    "Plastics manufacturing adds climate emissions.",
]
TT = [tok_norm(d) for d in TOY]
for i, t in enumerate(TT):
    print(f"d{i} len={len(t):2d} {t}")
bm = BM25Okapi(TT)
print(f"N={bm.corpus_size} total tokens={sum(bm.doc_len)} avgdl={bm.avgdl}")
df = collections.Counter(w for t in TT for w in set(t))
raw_idf = {w: math.log(len(TT) - n + 0.5) - math.log(n + 0.5) for w, n in df.items()}
print(f"vocabulary={len(df)} average_idf (all terms, before floor)={bm.average_idf:.6f} eps=0.25*average_idf={0.25 * bm.average_idf:.6f}")
for w in ("bpa", "regulation", "2019", "eu", "plastics", "the", "climate", "and", "emissions"):
    print(f"  term {w!r:12s} n={df[w]} raw idf=ln(({len(TT)}-{df[w]}+0.5)/({df[w]}+0.5))={raw_idf[w]:+.6f} -> rank_bm25 idf={bm.idf[w]:.6f}")

# ---------------------------------------------------------------- S4 one term score by hand, then code
head("S4 hand computation: term 'bpa' in d0 (k1=1.5, b=0.75)")
N, n, f, dl, avgdl, k1, b = 6, df["bpa"], TT[0].count("bpa"), len(TT[0]), bm.avgdl, 1.5, 0.75
idf = math.log((N - n + 0.5) / (n + 0.5))
K = k1 * (1 - b + b * dl / avgdl)
tfp = f * (k1 + 1) / (f + K)
hand = idf * tfp
lib = bm.get_scores(["bpa"])[0]
print(f"N={N} n={n} f={f} dl={dl} avgdl={avgdl}")
print(f"idf = ln(({N}-{n}+0.5)/({n}+0.5)) = ln({N - n + 0.5}/{n + 0.5}) = {idf:.6f}")
print(f"K = k1*(1-b+b*dl/avgdl) = 1.5*(0.25+0.75*{dl}/{avgdl:g}) = {K:.6f}")
print(f"tf part = f*(k1+1)/(f+K) = {f}*2.5/({f}+{K:.4f}) = {tfp:.6f}")
print(f"score = {hand:.6f}; rank_bm25 = {lib:.6f}; |diff| = {abs(hand - lib):.1e}")
q = tok_norm("BPA regulation 2019")
s_lib, s_np = bm.get_scores(q), bm25_numpy(TT, q)
print(f"query {q}: rank_bm25 scores per doc = {np.round(s_lib, 6).tolist()}")
print(f"  NumPy reference scores per doc     = {np.round(s_np, 6).tolist()}  max|diff|={np.abs(s_lib - s_np).max():.1e}")
for w in q:
    print(f"  d0 contribution of {w!r}: {bm.get_scores([w])[0]:.6f}")
# extra single-term scores used by the worked example and assessment items
for w, i in (("bpa", 2), ("2019", 2), ("eu", 0), ("regulation", 1), ("emissions", 5), ("emissions", 4)):
    print(f"  term {w!r} in d{i} (f={TT[i].count(w)}, dl={len(TT[i])}): score={bm.get_scores([w])[i]:.6f}")

# ---------------------------------------------------------------- S5 saturation (k1) and length normalisation (b)
head("S5 tf saturation and length normalisation (tf part only; multiply by idf for the score)")
print("tf part at dl = avgdl, k1=1.5, b=0.75:", {fq: round(tf_part(fq, 1.0), 4) for fq in (0, 1, 2, 3, 5, 10, 100, 1000)})
print("limit tf -> infinity = k1 + 1 =", 1.5 + 1)
print("tf part, f=1, by dl/avgdl (b=0.75):", {r: round(tf_part(1, r), 4) for r in (0.5, 1.0, 2.0, 4.0)})
print("tf part, f=1, dl=2*avgdl, by b:", {bb: round(tf_part(1, 2.0, b=bb), 4) for bb in (0.0, 0.375, 0.75, 1.0)})
print("tf part, f=1, dl=0.5*avgdl, by b:", {bb: round(tf_part(1, 0.5, b=bb), 4) for bb in (0.0, 0.375, 0.75, 1.0)})
print("tf part at dl=avgdl by k1, for f=1,2,5:",
      {kk: [round(tf_part(fq, 1.0, k1=kk), 4) for fq in (1, 2, 5)] for kk in (0.0, 0.75, 1.5, 3.0)})
print("CR-08 k1 1.5 -> 3.0, f=2, dl=avgdl:", round(tf_part(2, 1.0, 1.5), 4), "->", round(tf_part(2, 1.0, 3.0), 4))
print("CR-08 b 0.75 -> 0.375, f=1, dl=2*avgdl:", round(tf_part(1, 2.0, b=0.75), 4), "->", round(tf_part(1, 2.0, b=0.375), 4))
# The same limits checked through rank_bm25 itself, with a padded synthetic document
pad = lambda fq, length: ["x"] * fq + ["pad"] * (length - fq)
for fq in (1, 10, 100, 1000):
    corpus = [pad(fq, 2000), ["y"] * 2000, ["z"] * 2000]   # all docs length 2000, so dl = avgdl
    s = BM25Okapi(corpus).get_scores(["x"])[0]
    print(f"  rank_bm25, x in 1 of 3 docs, f={fq:4d}, dl=avgdl: score={s:.6f}  score/idf={s / BM25Okapi(corpus).idf['x']:.6f}")
# x once in a 20-token doc and once in a 5-token doc; four 15-token docs without x (all other words unique,
# so every idf is positive). Lengths 20, 5, 15, 15, 15, 15 -> avgdl 85/6.
long_short = ([["x"] + [f"a{j}" for j in range(19)], ["x"] + [f"b{j}" for j in range(4)]]
              + [[f"c{i}_{j}" for j in range(15)] for i in range(4)])
for bb in (0.75, 0.0):
    m = BM25Okapi(long_short, b=bb)
    s = m.get_scores(["x"])
    print(f"  rank_bm25, x once in a 20-token doc and once in a 5-token doc (avgdl={m.avgdl:.4f}), b={bb}:"
          f" long={s[0]:.6f} short={s[1]:.6f}")

# ---------------------------------------------------------------- S6 IDF quirks of this exact implementation
head("S6 IDF quirks of rank_bm25 0.2.2 (toy corpora)")
print(f"toy: 'plastics' n=3 of 6 -> idf {bm.idf['plastics']:.6f}; 'climate' n=4 of 6 -> idf {bm.idf['climate']:.6f} (the floor)")
print(f"  scores for 'plastics' = {np.round(bm.get_scores(['plastics']), 6).tolist()}")
print(f"  scores for 'climate'  = {np.round(bm.get_scores(['climate']), 6).tolist()}")
two = BM25Okapi([["bpa", "ban"], ["climate", "policy"]])
print(f"two-document corpus, query ['bpa']: idf={two.idf['bpa']:.6f} scores={two.get_scores(['bpa']).tolist()}")
three = BM25Okapi([["a", "b", "c"], ["a", "b"], ["a", "b"]])
print(f"three docs ['a','b','c'],['a','b'],['a','b']: raw idf a=b={math.log(0.5 / 3.5):.6f}, c={math.log(2.5 / 1.5):.6f};"
      f" average_idf={three.average_idf:.6f}; eps={three.average_idf * 0.25:.6f}; idf['a'] after floor={three.idf['a']:.6f};"
      f" scores for ['a']={np.round(three.get_scores(['a']), 6).tolist()}")
print(f"repeated query term: score('bpa')={bm.get_scores(['bpa'])[0]:.6f}, score('bpa bpa')={bm.get_scores(['bpa', 'bpa'])[0]:.6f}")
print(f"out-of-vocabulary term 'ipcc': scores={bm.get_scores(['ipcc']).tolist()}")
with warnings.catch_warnings(record=True) as wl:
    warnings.simplefilter("always")
    s_k0 = BM25Okapi(TT, k1=0.0).get_scores(["bpa"])
print(f"k1=0 (binary tf in theory), query ['bpa']: scores={s_k0.tolist()} (0/0 for docs without the term);"
      f" numpy warnings={len(wl)}")

# ---------------------------------------------------------------- S7 TF-IDF next to BM25
head("S7 TF-IDF (textbook tf x ln(N/n)) next to the BM25 tf part, term 'bpa' (n=2 of 6), dl = avgdl")
idf_tfidf = math.log(6 / 2)
for fq in (1, 2, 4, 8, 16):
    print(f"  f={fq:2d}: tf-idf={fq * idf_tfidf:.4f}   BM25={raw_idf['bpa'] * tf_part(fq, 1.0):.4f}")
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

vec = TfidfVectorizer()
X = vec.fit_transform(TOY)
an = vec.build_analyzer()
print("sklearn TfidfVectorizer defaults:", {k: vec.get_params()[k] for k in ("lowercase", "token_pattern", "smooth_idf", "sublinear_tf", "norm")})
SAMPLE = "Limit warming to 1.5 degrees; CO2, BPA (IPCC) & a 2019 ban."
print(f"  sklearn analyzer on {SAMPLE!r}: {an(SAMPLE)}")
print(f"  tok_norm on the same: {tok_norm(SAMPLE)}")
print(f"  tok_split on the same: {tok_split(SAMPLE)}")
print(f"  tok_word (lower+\\w+) on the same: {tok_word(SAMPLE)}")
IDS = "Upgrade to v2.10.3 if you see ERR_CONN_RESET."   # identifiers for the P3-T-01 practice item
for name, tk in (("split", tok_split), ("lower+\\w+", tok_word), ("norm", tok_norm), ("sklearn", an)):
    print(f"  identifiers under {name:10s}: {tk(IDS)}")
j = vec.vocabulary_["bpa"]
print(f"  sklearn idf_['bpa']={vec.idf_[j]:.6f}; ln((1+6)/(1+2))+1={math.log(7 / 3) + 1:.6f}")

# ---------------------------------------------------------------- S8 tokenization on the toy query
head("S8 the same toy query under split() and tok_norm")
TS = [tok_split(d) for d in TOY]
print("split tokens of d0:", TS[0])
print("split tokens of d2:", TS[2])
for name, tk in (("split", tok_split), ("norm", tok_norm)):
    corp = [tk(d) for d in TOY]
    print(f"  {name:6s} query={tk('BPA regulation 2019')} scores={np.round(BM25Okapi(corp).get_scores(tk('BPA regulation 2019')), 4).tolist()}")
print(f"  split, lower-case query 'bpa regulation 2019': scores={np.round(BM25Okapi(TS).get_scores('bpa regulation 2019'.split()), 4).tolist()}")

# ---------------------------------------------------------------- S9 climate PDF: tokenization and exact terms
head("S9 climate PDF, plain 1000/200 character windows (as in P1), five tokenizers")
S, O = 1000, 200
wins = [(i, min(i + S, len(full))) for i in range(0, len(full), S - O)]
W = [full[a:c] for a, c in wins]
print(f"windows={len(W)}")
for name, tk in TOKENIZERS.items():
    print(f"  whole-document vocabulary under {name:15s}: {len(set(tk(full)))} distinct tokens")
raw = collections.Counter(tok_split(full))
print("  split() variants of 'emissions':", {k: v for k, v in raw.items() if k.lower().strip('.,;:()"') == "emissions"})
print("  split() tokens containing 'IPCC':", {k: v for k, v in raw.items() if "IPCC" in k},
      "| containing 'BECCS':", {k: v for k, v in raw.items() if "BECCS" in k},
      "| containing 'CH4':", {k: v for k, v in raw.items() if "CH4" in k})
print("  toy fold: 'beccs'->", fold("beccs"), "'emissions'->", fold("emissions"), "'gases'->", fold("gases"),
      "'this'->", fold("this"), "'ccs'->", fold("ccs"))
QUERIES = [("IPCC", "IPCC"), ("What does BECCS stand for?", "BECCS"), ("methane CH4", "CH4"),
           ("Kyoto Protocol 1997", "1997"), ("limit warming to 1.5 degrees", "1.5")]
for qtext, target in QUERIES:
    tw = [i for i, w in enumerate(W) if target in w]
    print(f"query {qtext!r}: target string {target!r} occurs in windows {tw}")
    for name, tk in TOKENIZERS.items():
        corp = [tk(w) for w in W]
        sc = BM25Okapi(corp).get_scores(tk(qtext))
        st = max(sc[i] for i in tw)
        rank = (1 + int((sc > st).sum())) if st > 0 else None
        print(f"    {name:15s} q={tk(qtext)!s:42s} windows>0={int((sc > 0).sum()):2d} best target rank={rank}"
              f" target score={st:.4f} top score={sc.max():.4f}")
corp_w = [tok_word(w) for w in W]
print("  under lower+\\w+, windows containing token '1':", sum("1" in c for c in corp_w), "| token '5':", sum("5" in c for c in corp_w),
      "| of", len(W))
# What the repo code does with an all-zero score vector (IPCC under split())
sc0 = BM25Okapi([tok_split(w) for w in W]).get_scores(tok_split("IPCC"))
print(f"  IPCC under split(): all scores zero = {bool((sc0 == 0).all())}; repo-style np.argsort(scores)[::-1][:5] = "
      f"{np.argsort(sc0)[::-1][:5].tolist()} (k chunks returned anyway)")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    nan_norm = (sc0 - sc0.min()) / (sc0.max() - sc0.min())
eps_norm = (sc0 - sc0.min()) / (sc0.max() - sc0.min() + 1e-8)
print(f"  min-max without epsilon: NaN count={int(np.isnan(nan_norm).sum())} of {len(sc0)};"
      f" with +1e-8 (notebook cell 17): all zero={bool((eps_norm == 0).all())}")

# ---------------------------------------------------------------- S10 NumPy BM25 vs rank_bm25 on real data; negative idf
head("S10 NumPy reference vs rank_bm25 on the 91 windows; negative-idf terms")
worst = 0.0
for name in ("split", "norm"):
    tk = TOKENIZERS[name]
    corp = [tk(w) for w in W]
    lib = BM25Okapi(corp)
    for qtext, _ in QUERIES + [("greenhouse gas emissions", ""), ("the climate", "")]:
        d = np.abs(lib.get_scores(tk(qtext)) - bm25_numpy(corp, tk(qtext))).max()
        worst = max(worst, d)
print(f"max |NumPy - rank_bm25| over 7 queries x 2 tokenizers x 91 windows = {worst:.1e}")
corp = [tok_norm(w) for w in W]
lib = BM25Okapi(corp)
dfw = collections.Counter(t for c in corp for t in set(c))
neg = sorted([w for w, n in dfw.items() if math.log(len(W) - n + 0.5) - math.log(n + 0.5) < 0], key=lambda w: -dfw[w])
print(f"norm tokenizer: vocabulary={len(dfw)} avgdl={lib.avgdl:.2f} average_idf={lib.average_idf:.6f} eps={0.25 * lib.average_idf:.6f}")
print(f"terms in more than half of the 91 windows (raw idf < 0, floored to eps): {len(neg)}: {[(w, dfw[w]) for w in neg]}")
print(f"idf of 'climate' (n={dfw['climate']}) = {lib.idf['climate']:.6f}; idf of 'ipcc' (n={dfw['ipcc']}) = {lib.idf['ipcc']:.6f};"
      f" idf of 'emissions' (n={dfw['emissions']}) = {lib.idf['emissions']:.6f}")
print("DONE")
