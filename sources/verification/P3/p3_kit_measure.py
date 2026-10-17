"""P3 study-kit measurements (2026-10-17): the new numbers used by the short reading file, the question file and
the restyled full lesson. Sections K1..K10 of out_p3_kit_measure.txt (P3_FACTS.md, "Added 2026-10-17").

p3_measure.py (S1..S10, 2026-10-08) is left unchanged, so its saved output stays byte-identical.
Local only: no Groq or Cohere calls, no .env read, no network. No embedding model is loaded.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_kit_measure.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" > sources/verification/P3/out_p3_kit_measure.txt
"""
import collections
import hashlib
import importlib.metadata as md
import math
import re
import sys

import numpy as np
import pymupdf                              # pinned 1.26.7
from rank_bm25 import BM25Okapi

PDF = sys.argv[1]
NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")


def tok_norm(text):                         # identical to p3_measure.py (the course tokenizer)
    return NORM_RE.findall(text.lower())


def tok_split(text):                        # the repo's tokenizer
    return text.split()


def tf_part(f, dl_over_avgdl, k1=1.5, b=0.75):
    return f * (k1 + 1) / (f + k1 * (1 - b + b * dl_over_avgdl))


def head(title):
    print(f"\n=== {title}")


def ranked(scores):                         # best first; ties by the lower index
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


# ---------------------------------------------------------------- K1
head("K1 environment and corpus")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("rank-bm25", "numpy", "pymupdf")})
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
full = "\n".join(p.get_text() for p in pymupdf.open(PDF))
W = [full[i:min(i + 1000, len(full))] for i in range(0, len(full), 800)]     # P3's 91 plain windows (S9)
C = [tok_norm(w) for w in W]
bm = BM25Okapi(C)
df = collections.Counter(t for c in C for t in set(c))
print(f"chars={len(full)} windows={len(W)} avgdl={bm.avgdl:.4f} average_idf={bm.average_idf:.6f} "
      f"floor=0.25*average_idf={0.25 * bm.average_idf:.6f}")

# ---------------------------------------------------------------- K2 the running example
head("K2 running example: 'What does BECCS stand for?' on the 91 windows, tok_norm, k1=1.5, b=0.75")
Q = "What does BECCS stand for?"
q = tok_norm(Q)
print("query tokens:", q, "| split() query tokens:", tok_split(Q))
for t in q:
    raw = math.log(len(W) - df[t] + 0.5) - math.log(df[t] + 0.5)
    used = bm.idf.get(t)
    print(f"  token {t!r:8s} df={df[t]:2d} of {len(W)}  raw idf={raw:+.6f}  idf used="
          f"{'not in the index (adds 0)' if used is None else f'{used:.6f}'}")
sc = bm.get_scores(q)
order = ranked(sc)
print(f"windows with score > 0: {int((sc > 0).sum())} of {len(W)}")
print("top 5 (window, score):", [(i, round(float(sc[i]), 4)) for i in order[:5]])
for i in (83, 82, order[2]):
    dl = len(C[i])
    K = 1.5 * (0.25 + 0.75 * dl / bm.avgdl)
    parts = []
    for t in q:
        f = C[i].count(t)
        if f and t in bm.idf:
            parts.append(f"{t}: f={f} tf part={tf_part(f, dl / bm.avgdl):.6f} x idf {bm.idf[t]:.6f} = {bm.get_scores([t])[i]:.6f}")
    print(f"  window {i} (rank {order.index(i) + 1}): dl={dl} K={K:.6f} | " + " | ".join(parts) + f" | total={sc[i]:.6f}")
offs = [m.start() for m in re.finditer("BECCS", full)]
print("character offsets of 'BECCS' in the text:", offs)
for i in (82, 83):
    print(f"  window {i} covers characters {i * 800}..{min(i * 800 + 1000, len(full))}: contains the mention: "
          f"{any(i * 800 <= o < i * 800 + 1000 for o in offs)}")
print("  so df('beccs') = 2 counts ONE mention twice: it lies in the 200-character overlap of windows 82 and 83")
print("  split() tokens of the text that contain BECCS:", sorted({t for t in tok_split(full) if "BECCS" in t}))
print("  split() query tokens found in any window:", [t for t in tok_split(Q) if any(t in tok_split(w) for w in W)])
print(f"  for alone: window 16 has 'for' x{C[16].count('for')} (dl {len(C[16])}) -> {bm.get_scores(['for'])[16]:.6f}; "
      f"the largest possible 'for' contribution is idf x (k1 + 1) = {bm.idf['for'] * 2.5:.6f}")

# ---------------------------------------------------------------- K3 IPCC
head("K3 'IPCC' on the 91 windows")
i = 1
dl = len(C[i])
print(f"df('ipcc')={df['ipcc']}; idf={bm.idf['ipcc']:.6f}; window {i}: f={C[i].count('ipcc')} dl={dl} "
      f"K={1.5 * (0.25 + 0.75 * dl / bm.avgdl):.6f} tf part={tf_part(1, dl / bm.avgdl):.6f} score={bm.get_scores(['ipcc'])[i]:.6f}")
print("  split() token in that window:", [t for t in tok_split(W[i]) if "IPCC" in t])

# ---------------------------------------------------------------- K4 TF-IDF stuffing toy
head("K4 TOY: why linear tf is a problem. Query 'bpa ban'; six 8-token documents (dl = avgdl for every doc)")
STUFF = [
    "The BPA ban covers baby bottles and cans.",          # x: matches both words once
    "BPA BPA BPA BPA BPA BPA in plastics.",                # y: repeats one word six times
    "Sea levels rise and coastal cities flood often.",
    "Greenhouse gas emissions warm the planet every year.",
    "Solar farms on lakes cut water loss too.",
    "Climate policy needs clear targets and fair rules.",
]
ST = [tok_norm(d) for d in STUFF]
print("doc lengths:", [len(t) for t in ST])
sq = tok_norm("bpa ban")
N = len(ST)
dfs = collections.Counter(t for d in ST for t in set(d))
tfidf = [sum(d.count(t) * math.log(N / dfs[t]) for t in sq if dfs[t]) for d in ST]
bms = BM25Okapi(ST).get_scores(sq)
print("textbook TF-IDF  sum of f x ln(N/n):", [round(v, 4) for v in tfidf], "-> order", ranked(tfidf)[:2])
print("BM25 (rank_bm25):                   ", [round(float(v), 4) for v in bms], "-> order", ranked(list(bms))[:2])
print(f"  idf bpa={BM25Okapi(ST).idf['bpa']:.6f} ban={BM25Okapi(ST).idf['ban']:.6f}; tf part at f=6, dl=avgdl: {tf_part(6, 1.0):.6f}")

# ---------------------------------------------------------------- K5 AIQ Q12 claims
head("K5 checks for the AIQ 04 Q12 answer (dl = avgdl, k1=1.5, b=0.75)")
vals = {f: tf_part(f, 1.0) for f in (1, 2, 20, 21)}
print("tf part:", {f: round(v, 6) for f, v in vals.items()})
print(f"gain 1 -> 2: {vals[2] - vals[1]:.6f}   gain 20 -> 21: {vals[21] - vals[20]:.6f}")
K = 1.5
print("the repo's written form f/(f + K) at f = 1, 2, 20, 21:", {f: round(f / (f + K), 6) for f in (1, 2, 20, 21)},
      "| tf part / that form:", sorted({round(vals[f] / (f / (f + K)), 9) for f in vals}), "(= k1 + 1 for every f)")

TOY = [
    "BPA regulation (2019): the EU limits BPA in food-contact plastics.",
    "Climate policy and plastics: a review of chemical safety regulation.",
    "The 2019 BPA ban covers baby bottles; BPA, BPS and BPF are bisphenols.",
    "Climate change raises sea levels and flood risks for coastal cities.",
    "Greenhouse gas emissions and climate targets under the Paris Agreement.",
    "Plastics manufacturing adds climate emissions.",
]

# ---------------------------------------------------------------- K6 code identifiers (question P3-T-02)
head("K6 TOY: code identifiers. Ten function signatures; natural-word query 'user id' and exact query 'getUserId'")
SIGS = [
    "getUserId(token) -> int",
    "get_user_id(session) -> int",
    "getOrderId(order) -> int",
    "delete_user(user_id) -> None",
    "listUsers(team) -> list",
    "parseConfig(path) -> dict",
    "sendEmail(to, body) -> bool",
    "resizeImage(img, width) -> Image",
    "hashPassword(pw) -> str",
    "openSocket(host, port) -> Socket",
]
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def tok_parts(text):                         # TOY code tokenizer: split snake_case and camelCase into lower-case parts
    out = []
    for run in re.findall(r"[A-Za-z0-9_]+", text):
        out += [w.lower() for piece in run.split("_") for w in CAMEL.split(piece) if w]
    return out


def tok_parts_whole(text):                   # TOY: the parts, plus the whole identifier when it has more than one part
    out = []
    for run in re.findall(r"[A-Za-z0-9_]+", text):
        parts = tok_parts(run)
        out += parts + ([run.lower()] if len(parts) > 1 else [])
    return out


for name, tk in (("tok_norm", tok_norm), ("parts", tok_parts), ("parts+whole", tok_parts_whole)):
    corp = [tk(s) for s in SIGS]
    m = BM25Okapi(corp)
    print(f"  {name:11s} tokens of getUserId: {tk('getUserId')}  of get_user_id: {tk('get_user_id')}")
    for q in ("user id", "getUserId"):
        s = m.get_scores(tk(q))
        o = ranked(list(s))
        top = [(SIGS[i].split("(")[0], round(float(s[i]), 4)) for i in o if s[i] > 0][:4]
        print(f"    query {q!r:12s} -> {tk(q)}: signatures > 0: {int((s > 0).sum())}; top: {top}; "
              f"getUserId rank: {o.index(0) + 1 if s[0] > 0 else None}")

# ---------------------------------------------------------------- K7 a question with no rare word
head("K7 a question made of common words only, on the 91 windows")
Q7 = "What can be done about this?"
q7 = tok_norm(Q7)
for t in q7:
    print(f"  token {t!r:6s} df={df[t]:2d} idf used={'not in the index' if t not in bm.idf else f'{bm.idf[t]:.6f}'}")
s7 = bm.get_scores(q7)
o7 = ranked(list(s7))
print(f"windows > 0: {int((s7 > 0).sum())} of {len(W)}; rank 1 {s7[o7[0]]:.4f}, rank 5 {s7[o7[4]]:.4f}, "
      f"rank 10 {s7[o7[9]]:.4f}, rank 40 {s7[o7[39]]:.4f}")
print(f"compare K2: rank 1 {sc[order[0]]:.4f} vs rank 3 {sc[order[2]]:.4f} (the rare word separates the targets)")

# ---------------------------------------------------------------- K8 df under overlap, whole vocabulary
head("K8 how often the 200-character overlap doubles a document frequency (tok_norm, 91 windows)")
once = [t for t, n in collections.Counter(tok_norm(full)).items() if n == 1]
two = [t for t in once if df[t] == 2]
print(f"tokens that occur exactly once in the whole text: {len(once)}; of these, counted in 2 windows: {len(two)} "
      f"({100 * len(two) / len(once):.1f}%)")
whole = set(tok_norm(full))
frag = set(df) - whole
print(f"window vocabulary {len(df)} vs whole-text vocabulary {len(whole)}: {len(frag)} window tokens are not tokens of the "
      f"whole text (words cut at a window edge); whole-text tokens missing from every window: {len(whole - set(df))}")

# ---------------------------------------------------------------- K9 two-document corpora (correction to P3 D.3 / J2)
head("K9 two-document corpora: no score can be above 0")
for corpus, query in (([["bpa", "ban"], ["climate", "policy"]], ["bpa"]),
                      ([["bpa", "ban", "the"], ["climate", "policy", "the"]], ["bpa"]),
                      ([["bpa", "ban", "the"], ["climate", "policy", "the"]], ["the"]),
                      ([["bpa", "ban", "the"], ["climate", "policy", "the"]], ["bpa", "the"])):
    m = BM25Okapi(corpus)
    print(f"  corpus {corpus} query {query}: idf {dict((t, round(v, 6)) for t, v in m.idf.items())} "
          f"scores {np.round(m.get_scores(query), 6).tolist()}")
print("  a word in one of two docs: ln(1.5/1.5) = 0; a word in both: raw ln(0.5/2.5) < 0, floored to 0.25 x mean idf <= 0")

# ---------------------------------------------------------------- K10 hand-computation steps of P3-A-01 and P3-A-05
head("K10 the intermediate steps of P3-A-01 (eu in d0) and P3-A-05 (emissions in d5), six-document toy")
toy = BM25Okapi([tok_norm(d) for d in TOY])
for term, i in (("eu", 0), ("emissions", 5)):
    dl = len(tok_norm(TOY[i]))
    K = 1.5 * (0.25 + 0.75 * dl / toy.avgdl)
    tp = tf_part(1, dl / toy.avgdl)
    print(f"  {term} in d{i}: dl={dl} K={K:.6f} tf part={tp:.6f} idf={toy.idf[term]:.6f} idf x tf part={toy.idf[term] * tp:.6f} "
          f"rank_bm25={toy.get_scores([term])[i]:.6f}")
print("DONE")
