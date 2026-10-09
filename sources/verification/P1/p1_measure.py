"""P1 (LLM fundamentals) measurements: every number in concepts/P1_llm_fundamentals.md comes from this run.

Local only: no Groq or Cohere calls, no .env read. tiktoken may download an encoding file once.
The MiniLM model is loaded from the local Hugging Face cache (offline mode is forced below).

Run from rag_learning/ (Git Bash or PowerShell):
    uv run python sources/verification/P1/p1_measure.py "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/P1/out_p1_measure.txt  (sections are numbered S1..S10 for P1_FACTS.md)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")          # never hit the network for the HF model
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import hashlib
import importlib.metadata as md
import math
import statistics as st
import sys

import numpy as np
import pymupdf as fitz                                # pinned 1.26.7 (snapshot_id depends on it)
import tiktoken

PDF = sys.argv[1]
MINILM = "sentence-transformers/all-MiniLM-L6-v2"


def head(title):
    print(f"\n=== {title}")


# ---------------------------------------------------------------- S1 environment + snapshot text
head("S1 environment and extraction")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "tiktoken", "transformers", "sentence-transformers", "torch", "numpy", "tokenizers")})
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
# Same extraction as the acceptance suite (corrections/contracts_check.py L764-L766): page.get_text(), pages joined with "\n".
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)
print(f"pages={len(pages)} chars={len(full)} page1_chars={len(pages[0])} pymupdf.VersionBind={fitz.VersionBind}")

# ---------------------------------------------------------------- tokenizers
enc = {n: tiktoken.get_encoding(n) for n in ("cl100k_base", "o200k_base", "o200k_harmony", "gpt2")}
from sentence_transformers import SentenceTransformer  # noqa: E402

model = SentenceTransformer(MINILM, device="cpu")
wp = model.tokenizer                                  # BERT WordPiece (uncased), as used by the embedder


def n_tik(name, text):
    return len(enc[name].encode(text, disallowed_special=()))


def n_wp(text):                                       # content tokens only (no [CLS]/[SEP])
    return len(wp(text, add_special_tokens=False, truncation=False)["input_ids"])


def n_unk(text):
    return wp(text, add_special_tokens=False)["input_ids"].count(wp.unk_token_id)


head("S2 tokenizer identities")
for n, e in enc.items():
    print(f"{n:14s} n_vocab={e.n_vocab}")
print(f"MiniLM WordPiece vocab={wp.vocab_size} do_lower_case={getattr(wp, 'do_lower_case', None)}"
      f" class={type(wp).__name__}")
for m in ("gpt-3.5-turbo", "gpt-4o-mini", "gpt-oss-20b", "gpt2"):
    try:
        print(f"tiktoken.encoding_for_model({m!r}) -> {tiktoken.encoding_for_model(m).name}")
    except KeyError as ex:
        print(f"tiktoken.encoding_for_model({m!r}) -> KeyError {ex}")

# ---------------------------------------------------------------- S3 samples: chars per token
head("S3 chars per token on samples (WordPiece counts exclude [CLS]/[SEP])")
S, O = 1000, 200                                      # simple_rag cell 10 defaults, but PLAIN fixed character windows
windows = [(i, i + S) for i in range(0, len(full), S - O)]
windows = [(a, min(b, len(full))) for a, b in windows if a < len(full)]
CODE = ("def top_k(scores, k=4):\n"
        "    idx = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]\n"
        "    return [(i, round(scores[i], 3)) for i in idx]\n")
NUMBERS = "Run 2026-10-08T14:32:07Z: 3 x 1,000 chars, k=4, cos=0.8731, p95=1.42s, ids 4f9c2a17, 7b0e93d5."
GERMAN = "Der Klimawandel verändert die Niederschlagsmuster in ganz Europa deutlich."
HINDI = "जलवायु परिवर्तन से पूरे भारत में वर्षा के पैटर्न बदल रहे हैं।"
samples = [("whole document", full), ("page 1", pages[0])]
samples += [(f"window {k} [{a},{b})", full[a:b]) for k, (a, b) in enumerate(windows[:3])]
samples += [("code snippet (toy)", CODE), ("numbers line (toy)", NUMBERS),
            ("German sentence", GERMAN), ("Hindi sentence", HINDI)]
print(f"{'sample':24s} {'chars':>6s} | {'cl100k':>6s} {'c/t':>5s} | {'o200k':>6s} {'c/t':>5s} | "
      f"{'WordPc':>6s} {'c/t':>5s} {'[UNK]':>5s} | {'chars/4':>7s} {'err vs cl100k':>13s}")
for label, t in samples:
    a, b, c = n_tik("cl100k_base", t), n_tik("o200k_base", t), n_wp(t)
    est = len(t) / 4
    print(f"{label:24s} {len(t):6d} | {a:6d} {len(t)/a:5.2f} | {b:6d} {len(t)/b:5.2f} | "
          f"{c:6d} {len(t)/c:5.2f} {n_unk(t):5d} | {est:7.0f} {100*(est-a)/a:+12.0f}%")
print(f"whole document gpt2={n_tik('gpt2', full)} c/t={len(full)/n_tik('gpt2', full):.2f};"
      f" o200k_harmony={n_tik('o200k_harmony', full)} (o200k_base={n_tik('o200k_base', full)})")
words = full.split()
print(f"whole document whitespace words={len(words)} chars/word={len(full)/len(words):.2f}")

head("S4 distribution over ALL plain 1000/200 character windows of the document")
print(f"windows={len(windows)} (last one is {windows[-1][1]-windows[-1][0]} chars)")
for name, f in (("cl100k_base", lambda t: n_tik("cl100k_base", t)), ("o200k_base", lambda t: n_tik("o200k_base", t)),
                ("WordPiece", n_wp)):
    r = [(b - a) / f(full[a:b]) for a, b in windows]
    tk = [f(full[a:b]) for a, b in windows[:-1]]       # full-length windows only for token counts
    print(f"{name:12s} chars/token min/median/max = {min(r):.2f}/{st.median(r):.2f}/{max(r):.2f};"
          f" tokens per full 1000-char window min/median/max = {min(tk)}/{st.median(tk)}/{max(tk)}")

# ---------------------------------------------------------------- S5 see the cut
head("S5 see the cut (one short sentence)")
SENT = "Anthropogenic emissions are accelerating deglaciation in Greenland."
print(f"sentence chars={len(SENT)}")
for n in ("cl100k_base", "o200k_base"):
    ids = enc[n].encode(SENT)
    pieces = [enc[n].decode_single_token_bytes(i).decode("utf-8", errors="replace") for i in ids]
    print(f"{n:12s} {len(ids):2d} tokens: {pieces}")
w = wp(SENT)
print(f"WordPiece    {len(w['input_ids'])} ids incl. [CLS]/[SEP]: {wp.convert_ids_to_tokens(w['input_ids'])}")
print(f"same word, other case (cl100k): 'Greenland'->{len(enc['cl100k_base'].encode('Greenland'))} "
      f"' Greenland'->{len(enc['cl100k_base'].encode(' Greenland'))} 'GREENLAND'->{len(enc['cl100k_base'].encode('GREENLAND'))}")

# ---------------------------------------------------------------- S6 truncation in the embedder
head("S6 MiniLM max_seq_length and silent truncation")
from huggingface_hub import snapshot_download  # noqa: E402

print("MiniLM cache snapshot:", os.path.basename(snapshot_download(MINILM, local_files_only=True)))
print(f"model.max_seq_length={model.max_seq_length} tokenizer.model_max_length={wp.model_max_length}"
      f" dim={model.get_embedding_dimension()} modules={[type(m).__name__ for m in model]}")
# Pick a 400-content-token passage whose token 254 ends at a word boundary, so the 254-token prefix
# re-tokenizes to exactly the first 254 tokens ([CLS] + 254 + [SEP] = 256 = max_seq_length).
start0 = len(pages[0]) + 1 + len(pages[1]) + 1         # start of page 3 in the joined text
chosen = None
for start in [m for m in range(start0, start0 + 2000) if full[m - 1].isspace() and not full[m].isspace()]:
    span = full[start:start + 4000]
    tok = wp(span, add_special_tokens=False, return_offsets_mapping=True)
    toks = wp.convert_ids_to_tokens(tok["input_ids"])
    if len(toks) < 401 or toks[254].startswith("##") or toks[400].startswith("##"):
        continue
    long_t = span[:tok["offset_mapping"][399][1]]
    pre254 = span[:tok["offset_mapping"][253][1]]
    pre200 = span[:tok["offset_mapping"][199][1]] if not toks[200].startswith("##") else None
    if n_wp(long_t) == 400 and n_wp(pre254) == 254 and pre200 and n_wp(pre200) == 200:
        chosen = (start, long_t, pre254, pre200)
        break
start, long_t, pre254, pre200 = chosen
tail = long_t[len(pre254):]
other = full[-3000:]                                  # unrelated text from the end of the document
swap = pre254 + " " + " ".join(other.split()[:200])   # same first 254 tokens, different tail
ids_long = model.preprocess([long_t])["input_ids"]   # what the embedder actually receives
print(f"passage start offset={start} chars={len(long_t)} WordPiece content tokens={n_wp(long_t)};"
      f" prefix254 chars={len(pre254)}; prefix200 chars={len(pre200)}; swapped-tail tokens={n_wp(swap)}")
print(f"model.preprocess(long) input_ids shape={tuple(ids_long.shape)} first={int(ids_long[0,0])}"
      f"({wp.cls_token}={wp.cls_token_id}) last={int(ids_long[0,-1])}({wp.sep_token}={wp.sep_token_id})")
# Encode with a FRESH model instance and capture every warning and log record, to test "silent".
import logging, warnings  # noqa: E401,E402


class _Grab(logging.Handler):
    def __init__(self):
        super().__init__(); self.msgs = []

    def emit(self, r):
        self.msgs.append(f"{r.name}: {r.getMessage()[:80]}")


grab = _Grab()
for lg in ("transformers", "sentence_transformers"):
    logging.getLogger(lg).addHandler(grab)
model2 = SentenceTransformer(MINILM, device="cpu")
grab.msgs.clear()
with warnings.catch_warnings(record=True) as wlist:
    warnings.simplefilter("always")
    E = model2.encode([long_t, pre254, swap, pre200, tail], normalize_embeddings=True, convert_to_numpy=True)
print(f"encode() of the 400- and 502-token texts on a fresh model: exceptions=0 python-warnings={len(wlist)}"
      f" log-records={len(grab.msgs)} {grab.msgs}")
cos = lambda i, j: float(E[i] @ E[j])
print(f"cos(long400, prefix254)      = {cos(0,1):.6f}  max|diff| = {np.abs(E[0]-E[1]).max():.2e}")
print(f"cos(long400, swapped tail)   = {cos(0,2):.6f}  max|diff| = {np.abs(E[0]-E[2]).max():.2e}")
print(f"cos(long400, prefix200)      = {cos(0,3):.6f}")
print(f"cos(long400, its own tail)   = {cos(0,4):.6f}   (tail = tokens 255..400, never seen by the vector)")
print("tail starts:", repr(tail[:90]))

# ---------------------------------------------------------------- S7 temperature (toy)
head("S7 temperature: softmax(logits / T)  [TOY logits, not from any model]")
labels = ["YES", "NO", "PARTIAL", "MAYBE"]
z = np.array([2.0, 1.5, 0.5, -1.0])


def softmax_T(z, T):
    s = z / T
    s = s - s.max()
    p = np.exp(s)
    return p / p.sum()


for T in (0.25, 0.5, 1.0, 2.0, 4.0):
    p = softmax_T(z, T)
    H = -float((p * np.log2(p)).sum())
    print(f"T={T:<4} p={np.round(p, 3).tolist()} entropy={H:.2f} bits")
print("T->0 (greedy): argmax =", labels[int(np.argmax(z))], "with probability 1")
rng = np.random.default_rng(0)
for T in (0.5, 1.0, 2.0):
    draws = rng.choice(4, size=1000, p=softmax_T(z, T))
    print(f"T={T}: 1000 seeded draws (rng seed 0) -> counts {dict(zip(labels, np.bincount(draws, minlength=4).tolist()))}")

# ---------------------------------------------------------------- S8 a repo heuristic checked on our corpus
head("S8 contextual_chunk_headers cell 11: 4000 tokens described as ~3000 words")
cl = enc["cl100k_base"]
first4000 = cl.decode(cl.encode(full)[:4000])
print(f"first 4000 cl100k tokens of the document = {len(first4000)} chars = {len(first4000.split())} whitespace words")

# ---------------------------------------------------------------- S9 token counts for a cost estimate
head("S9 token counts for one v0 prompt (06 §3.3 template, 4 sample windows; NOT a retrieval result)")
SYSTEM_V0 = (  # 06 §3.3 prompts/answer_v1.txt, SYSTEM part, verbatim
    "You answer questions using ONLY the numbered sources below.\n"
    "Rules:\n"
    "1. Every factual sentence must end with one or more citations in the form [doc_id:page],\n"
    "   copied exactly from the source headers, e.g. [climate:10].\n"
    "2. If the sources do not contain the answer, reply exactly:\n"
    "   \"I cannot answer this from the provided documents.\"\n"
    "   Do not use outside knowledge.\n"
    "3. Do not cite a source that does not support the sentence.\n"
    "4. Be concise: at most 5 sentences.\n")
QUESTION = ("According to the document, by how much have global temperatures risen "
            "since the late 19th century?")               # 06 seed item D-001
starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
page_of = lambda off: max(i + 1 for i, s0 in enumerate(starts) if s0 <= off)   # 1-based page of a doc offset
ctx = "\n\n".join(f"[{k+1}] (climate:{page_of(a)})\n{full[a:b]}" for k, (a, b) in enumerate(windows[:4]))
user = f"Sources:\n{ctx}\n\nQuestion: {QUESTION}\nAnswer:"
for n in ("o200k_harmony", "cl100k_base"):
    print(f"{n:14s} system={n_tik(n, SYSTEM_V0)} question={n_tik(n, QUESTION)} "
          f"sources(4 x 1000 chars + headers)={n_tik(n, ctx)} user message={n_tik(n, user)}"
          f" system+user={n_tik(n, SYSTEM_V0) + n_tik(n, user)} (chars={len(SYSTEM_V0) + len(user)})")
SMOKE_MSG = "Reply with exactly: smoke test ok"              # labs/O2_smoke_test.py, the logged Groq call
print(f"O2 smoke message: chars={len(SMOKE_MSG)} o200k_harmony tokens={n_tik('o200k_harmony', SMOKE_MSG)};"
      f" reply 'smoke test ok' tokens={n_tik('o200k_harmony', 'smoke test ok')}")

# ---------------------------------------------------------------- S10 cost arithmetic with PLACEHOLDER prices
head("S10 cost formula with placeholder prices (X, Y are NOT real prices)")
n_in = n_tik("o200k_harmony", SYSTEM_V0) + n_tik("o200k_harmony", user)
for max_out in (256, 512):
    print(f"100 queries: input tokens = 100 x {n_in} = {100*n_in:,}; output tokens <= 100 x {max_out} = {100*max_out:,}"
          f" -> cost <= ({100*n_in:,} * X + {100*max_out:,} * Y) / 1,000,000")
n_ctx = n_tik("o200k_harmony", ctx)
print(f"doubling k from 4 to 8 (similar chunks) adds about {n_ctx} tokens per query: {n_in} -> ~{n_in + n_ctx}"
      f" (x{(n_in + n_ctx) / n_in:.2f} input tokens, not x2: the instructions and question do not double)")
print("DONE")
