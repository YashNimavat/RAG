"""P1 study-kit measurements (K1-K8): the numbers the HTML lesson adds on top of p1_measure.py (S1-S11).

Local only: no Groq, Cohere or Claude call, no .env read. tiktoken may download an encoding file once.
p1_measure.py is not changed, so its saved output stays byte-identical.

Run from rag_learning/:
    uv run python sources/verification/P1/p1_kit_measure.py "<Book RAG>/upstream/RAG_Techniques"
Saved output: sources/verification/P1/out_p1_kit_measure.txt  (sections K1..K8 for P1_FACTS.md section 1b)
"""
import importlib.metadata as md
import json
import sys
from pathlib import Path

import pymupdf as fitz                                # pinned 1.26.7
import tiktoken
from tokenizers import Tokenizer, models, pre_tokenizers, trainers

REPO = Path(sys.argv[1])
PDF = REPO / "data" / "Understanding_Climate_Change.pdf"


def head(title):
    print(f"\n=== {title}")


def pieces(enc, text):
    return [enc.decode_single_token_bytes(i).decode("utf-8", errors="replace").replace(" ", "·") for i in enc.encode(text)]


harmony = tiktoken.get_encoding("o200k_harmony")
cl100k = tiktoken.get_encoding("cl100k_base")
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)

# ---------------------------------------------------------------- K1 environment
head("K1 environment")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "tiktoken", "tokenizers")})
print(f"pdf chars={len(full)} pages={len(pages)}")

# ---------------------------------------------------------------- K2 the encoding-name trap
head("K2 which encoding a model id maps to (tiktoken.encoding_for_model)")
for m in ("gpt-oss-20b", "openai/gpt-oss-20b", "gpt-4o-mini", "gpt-3.5-turbo"):
    try:
        print(f"encoding_for_model({m!r}) -> {tiktoken.encoding_for_model(m).name}")
    except KeyError as ex:
        print(f"encoding_for_model({m!r}) -> KeyError: {str(ex)[:90]}")
mid = "openai/gpt-oss-20b"
print(f"fix 1: get_encoding('o200k_harmony') -> {tiktoken.get_encoding('o200k_harmony').name}")
print(f"fix 2: encoding_for_model({mid!r}.split('/')[-1]) -> {tiktoken.encoding_for_model(mid.split('/')[-1]).name}")

# ---------------------------------------------------------------- K3 special tokens in documents
head("K3 special-token strings inside ordinary text")
specials = sorted(harmony.special_tokens_set)
print(f"o200k_harmony n_vocab={harmony.n_vocab} special tokens={len(specials)}")
print("harmony chat-format tokens present:", [t for t in ("<|start|>", "<|channel|>", "<|message|>", "<|end|>", "<|return|>", "<|call|>")
                                              if t in harmony.special_tokens_set])
for s in ("<|endoftext|>", "<|start|>"):
    try:
        harmony.encode(s)
        print(f"encode({s!r}) -> ok (unexpected)")
    except ValueError as ex:
        print(f"encode({s!r}) -> ValueError: {str(ex).splitlines()[0][:80]}")
    ids = harmony.encode(s, disallowed_special=())
    print(f"encode({s!r}, disallowed_special=()) -> {len(ids)} ordinary tokens: "
          f"{[harmony.decode_single_token_bytes(i).decode() for i in ids]}")

# ---------------------------------------------------------------- K4 code and numbers
head("K4 chars per token on real repo code, and how digits are cut (o200k_harmony / cl100k)")
for rel in ("helper_functions.py", "evaluation/evalute_rag.py"):
    t = (REPO / rel).read_text(encoding="utf-8")
    a, b = len(harmony.encode(t, disallowed_special=())), len(cl100k.encode(t, disallowed_special=()))
    print(f"{rel:28s} chars={len(t):6d} o200k_harmony={a:5d} ({len(t)/a:.2f} c/t) cl100k={b:5d} ({len(t)/b:.2f} c/t)")
for s in ("1234567", "1,234,567", "2023-11-07", "650,000", "1.5"):
    print(f"{s!r:14s} o200k_harmony {len(harmony.encode(s))} tokens {pieces(harmony, s)}")

# ---------------------------------------------------------------- K5 bytes vs characters (where "divide by 4" comes from)
head("K5 UTF-8 bytes vs characters per token (o200k_harmony)")
HINDI = "जलवायु परिवर्तन से पूरे भारत में वर्षा के पैटर्न बदल रहे हैं।"     # same sentence as p1_measure.py S3
for label, t in (("whole climate PDF", full), ("Hindi sentence (S3)", HINDI)):
    n, nb = len(harmony.encode(t, disallowed_special=())), len(t.encode("utf-8"))
    print(f"{label:22s} chars={len(t):6d} bytes={nb:6d} tokens={n:6d} chars/token={len(t)/n:.2f} bytes/token={nb/n:.2f}")

# ---------------------------------------------------------------- K6 where the pieces come from: a tiny BPE trained on the PDF
head("K6 a tiny BPE trained on the climate PDF (tokenizers BpeTrainer, whitespace pre-tokenizer, vocab 300)")


def train():
    tok = Tokenizer(models.BPE(unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.train_from_iterator([full], trainers.BpeTrainer(vocab_size=300, min_frequency=2, special_tokens=["[UNK]"],
                                                        show_progress=False))
    return tok


def merges_of(t):
    return [" + ".join(m) if isinstance(m, list) else m.replace(" ", " + ") for m in json.loads(t.to_str())["model"]["merges"]]


tok = train()
merges = merges_of(tok)
print(f"vocab={tok.get_vocab_size()} merges learned={len(merges)}")
print("first 12 merges, in order:", merges[:12])
print("second training run gives identical merges:", merges_of(train()) == merges)
for w in ("the", "climate", "greenhouse", "emissions", "deglaciation"):
    print(f"{w:13s} tiny BPE {len(tok.encode(w).tokens)} {tok.encode(w).tokens} | o200k_harmony (after a space) "
          f"{len(harmony.encode(' ' + w))} {pieces(harmony, ' ' + w)}")

# ---------------------------------------------------------------- K7 the dated price sheet (Groq and Claude Haiku, read 2026-10-17)
head("K7 cost and run time with dated prices (per 1M tokens; LLMOPS_FOUNDATION section 6.2, read 2026-10-17)")
N_IN, CAP, OVERHEAD = 976, 512, 71        # S9 counted input; v0 output cap (06 section 3.1); B.3 inferred template overhead
for name, p_in, p_out in (("Groq openai/gpt-oss-20b", 0.075, 0.30), ("Claude Haiku 5.5", 0.10, 0.50)):
    one = (N_IN * p_in + CAP * p_out) / 1e6
    out_share = CAP * p_out / (N_IN * p_in + CAP * p_out)
    print(f"{name:24s} one call <= ${one:.6f} ; 100 calls <= ${100*one:.4f} ; output share of the bill = {100*out_share:.1f}%")
print(f"output price / input price: Groq {0.30/0.075:.1f}x ; Haiku {0.50/0.10:.1f}x")
per_call = N_IN + OVERHEAD + CAP
for calls, tpm in ((100, 8000), (55, 8000)):
    print(f"{calls} calls x ({N_IN} + {OVERHEAD} + {CAP} = {per_call}) tokens = {calls*per_call:,} tokens ; at {tpm:,} tokens/min >= {calls*per_call/tpm:.1f} min")

# ---------------------------------------------------------------- K8 the window inequality for v0
head("K8 v0 call inside the gpt-oss-20b window (Groq model page: window 131,072, max output 65,536)")
W = 131072
print(f"input {N_IN} + template ~{OVERHEAD} + output cap {CAP} = {N_IN+OVERHEAD+CAP} tokens = {100*(N_IN+OVERHEAD+CAP)/W:.2f}% of {W:,}")
print(f"sources share of the counted input: 842 / {N_IN} = {100*842/N_IN:.0f}%")
print("DONE")
