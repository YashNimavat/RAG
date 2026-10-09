# C2 lab REFERENCE SOLUTION (throwaway; never copy into the notebook).
# Format: blocks that start with '# == <task id>' replace the notebook cell whose metadata "task" has that id.
# Written for the lab from 07 Part D.2-D.4 and H.1 (behaviour), with the 06 §2.3/§3.1 record contract.
# The builder (c2_build_lab.py) executes the setup cell + these blocks to compute the CHECK fingerprints;
# c2_measure.py cross-checks the results against 07 H.1/H.3 executed from the lesson text.

# == T1
my_spans_10_3 = [(0, 10), (7, 17), (14, 23)]
my_spans_8_4 = [(0, 8), (4, 12), (8, 16), (12, 20), (16, 23)]
my_confidence_t1 = 3

# == T2
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    text: str
    char_start: int
    char_end: int


def fixed_window_chunks(text, size, overlap=0):
    if size <= 0:
        raise ValueError("size must be > 0")
    if not 0 <= overlap < size:
        raise ValueError(f"need 0 <= overlap < size, got overlap={overlap}, size={size}")
    stride = size - overlap
    out, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        out.append(Chunk(len(out), text[start:end], start, end))
        if end == len(text):
            break
        start += stride
    return out

# == T3
def check_chunks(text, chunks, size):
    assert chunks, "no chunks"
    assert chunks[0].char_start == 0 and chunks[-1].char_end == len(text), "must start at 0 and end at len(text)"
    for c in chunks:
        assert text[c.char_start:c.char_end] == c.text, f"offsets wrong for chunk {c.chunk_id}"
        assert 0 < len(c.text) <= size, f"chunk {c.chunk_id} has length {len(c.text)}"
    for a, b in zip(chunks, chunks[1:]):
        assert b.char_start <= a.char_end, f"gap between chunk {a.chunk_id} and {b.chunk_id}"
        assert b.char_start > a.char_start, "no forward progress"
    rebuilt = chunks[0].text + "".join(b.text[a.char_end - b.char_start:] for a, b in zip(chunks, chunks[1:]))
    assert rebuilt == text, "overlap-removed concatenation must rebuild the text"

# == T4p
my_fact_chunks_o0 = []
my_fact_chunks_o60 = [2]
my_largest_guaranteed_f = 201
my_confidence_t4 = 2

# == T4
def chunks_containing(chunks, start, end):
    return [c.chunk_id for c in chunks if c.char_start <= start and end <= c.char_end]


def p_formula(S, O, F):
    return min(1.0, (S - F + 1) / (S - O))


def p_brute(L, S, O, F):
    chunks = fixed_window_chunks("x" * L, S, O)
    total = L - F + 1
    hit = sum(1 for p in range(total) if chunks_containing(chunks, p, p + F))
    return hit / total

# == T5p
my_w_spans = [(0, 8), (4, 12), (8, 15), (12, 22)]
my_confidence_t5 = 1

# == T5
def split_spans(text, start, end, separators, size):
    if end - start <= size:
        return [(start, end)]
    if not separators:
        return [(s, s + 1) for s in range(start, end)]
    sep, rest = separators[0], separators[1:]
    if sep == "":
        return [(s, s + 1) for s in range(start, end)]
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


def recursive_chunks(text, size, overlap=0, separators=SEPARATORS):
    if not 0 <= overlap < size:
        raise ValueError(f"need 0 <= overlap < size, got overlap={overlap}, size={size}")
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
    return [Chunk(i, text[a:b], a, b) for i, (a, b) in enumerate(spans)]

# == T6p
my_guess_per_page_count = 97

# == T6
def chunk_pages(pages, size, overlap):
    out, start = [], 0
    for i, page in enumerate(pages):
        for c in recursive_chunks(page, size, overlap):
            out.append((start + c.char_start, start + c.char_end, i + 1))
        start += len(page) + 1
    return out

# == T7
def params_hash(params):
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def make_records(doc_id, snapshot_id, pages, params):
    h = params_hash(params)
    starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
    full = "\n".join(pages)
    out = []
    for seq, (a, b, page) in enumerate(chunk_pages(pages, params["chunk_size"], params["chunk_overlap"])):
        text = full[a:b]
        out.append({
            "doc_id": doc_id,
            "snapshot_id": snapshot_id,
            "chunk_id": f"{doc_id}:{snapshot_id}:{h}:{seq:05d}",
            "seq": seq,
            "char_start": a,
            "char_end": b,
            "page_segments": [{"page": page, "char_start": a - starts[page - 1], "char_end": b - starts[page - 1]}],
            "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "chunker": params["name"],
            "params_hash": h,
            "meta": {},
        })
    return out


records = make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS)

# == T8p
my_guess_all_200 = False

# == T8
def achieved_overlaps(records):
    return [a["char_end"] - b["char_start"] for a, b in zip(records, records[1:])
            if a["page_segments"][0]["page"] == b["page_segments"][0]["page"]]
