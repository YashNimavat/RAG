"""The C2 lab's GIVEN setup cell, as one string (single source for the notebook, the builder and the runners).

It loads Corpus D with PyMuPDF 1.26.7 exactly as C1 / 06 §5.3 define it (page.get_text(), pages joined with "\n",
no cleaning), recomputes the 06 §5.3 snapshot_id and fails closed if it is not ea07572562ac, and defines the
v0 chunking parameters of 06 §2.4/§3.1 plus the small inputs used by the tasks. Contains no solution code.
"""

PDF_PATH = r"C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf"

SETUP = r'''
import hashlib, json, math, re
import pymupdf

# ---- Corpus D, loaded the way C1 / 06 §5.3 define it (you do not need your C1 code here) ----
PDF = r"__PDF__"
DOC_ID = "climate"
assert pymupdf.VersionBind == "1.26.7", f"PyMuPDF {pymupdf.VersionBind}: the snapshot needs exactly 1.26.7 (pinned)"
with pymupdf.open(PDF) as _d:
    pages = [p.get_text() for p in _d]               # page.get_text(), no cleaning (06 §3.1)
doc_text = "\n".join(pages)                           # ONE coordinate system: document offsets into doc_text
page_starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]   # +1 = the joining "\n"

# 06 §5.3 snapshot_id recipe (fail closed: a different parser or text gives a different id)
_parts = ["snapshot-v1", f"parser=pymupdf@{pymupdf.VersionBind}", "options=" + json.dumps({}, sort_keys=True),
          "cleaning=none", "page_join=\\n",
          f"{DOC_ID}:{hashlib.sha256(doc_text.encode('utf-8')).hexdigest()}"]
SNAPSHOT_ID = hashlib.sha256("|".join(_parts).encode("utf-8")).hexdigest()[:12]
assert SNAPSHOT_ID == "ea07572562ac", f"snapshot {SNAPSHOT_ID} is not the frozen Corpus D snapshot ea07572562ac"

# ---- v0 chunking parameters: the `chunking:` block of 06 §2.4 (= 06 §3.1), copied exactly ----
PARAMS = {
    "name": "recursive_char",
    "unit": "chars",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "separators": ["\n\n", "\n", " ", ""],
    "scope": "per_page",
}
SEPARATORS = PARAMS["separators"]

# ---- small inputs for the tasks (07 Part L and Part F) ----
T = "abcdefghijklmnopqrstuvw"          # 23 characters (C2-A-01)
W = "the cat sat on the mat"           # 22 characters (C2-A-03)
PARA = ("A bi-encoder turns a passage into one vector in three steps. First, a WordPiece tokenizer "
        "splits the text into subword tokens and adds the special [CLS] and [SEP] markers. Second, a "
        "small transformer reads the token sequence and produces one contextual vector per token. "
        "Third, a pooling layer averages those token vectors into a single fixed-size embedding, "
        "which is then scaled to unit length. Two passages are later compared by the cosine of their "
        "vectors. Because the model was trained on short inputs, its "
        "configuration caps the sequence at 256 tokens. Tokens beyond the cap are silently dropped "
        "before the transformer runs. A sentence placed at the end of a long chunk can therefore have "
        "no influence at all on the chunk's embedding, even though the chunk text still contains it.")
FACT = "Tokens beyond the cap are silently dropped before the transformer runs."
FACT_SPAN = (PARA.index(FACT), PARA.index(FACT) + len(FACT))      # (558, 629): 07 Part F

def _fp(x):
    """Fingerprint of a value. The CHECK cells compare fingerprints, not visible answers."""
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]

def _names(fn):
    """Every global or attribute name a function's code uses (also inside nested code)."""
    out, todo = set(), [fn.__code__]
    while todo:
        c = todo.pop()
        out |= set(c.co_names)
        todo += [k for k in c.co_consts if hasattr(k, "co_names")]
    return out

def _spans(chunks):
    """[(char_start, char_end), ...] of a list of chunks."""
    return [(c.char_start, c.char_end) for c in chunks]

import sys
def _limited(fn, *args, steps=300_000):
    """Run fn(*args), but stop it with TimeoutError after `steps` Python steps (catches an infinite loop)."""
    n = [0]
    def _tr(frame, event, arg):
        n[0] += 1
        if n[0] > steps:
            raise TimeoutError(f"stopped after {steps:,} steps: probably an infinite loop")
        return _tr
    old = sys.gettrace()
    sys.settrace(_tr)
    try:
        return fn(*args)
    finally:
        sys.settrace(old)

print(f"{len(pages)} pages, {len(doc_text):,} characters; PyMuPDF {pymupdf.VersionBind}; snapshot {SNAPSHOT_ID}")
print(f"len(PARA) = {len(PARA)}, FACT_SPAN = {FACT_SPAN}")
'''.replace("__PDF__", PDF_PATH).strip("\n")
