# Independent alternative solution (different code style), to test that the CHECKs accept any correct implementation.

# == T1
my_spans_10_3 = [[0, 10], [7, 17], [14, 21]]   # deliberately wrong last span (a learner's honest mistake)
my_spans_8_4 = [(0, 8), (4, 12), (8, 16), (12, 20), (16, 23)]
my_confidence_t1 = 2

# == T2
import dataclasses


@dataclasses.dataclass(frozen=True)
class Chunk:
    chunk_id: int
    text: str
    char_start: int
    char_end: int


def fixed_window_chunks(text, size, overlap=0):
    if not (size > 0 and 0 <= overlap < size):
        raise ValueError("bad size/overlap")
    n = len(text)
    if n == 0:
        return []
    stride = size - overlap
    count = 1 if n <= size else -(-(n - overlap) // stride)
    return [Chunk(k, text[k * stride:min(k * stride + size, n)], k * stride, min(k * stride + size, n)) for k in range(count)]

# == T3
def check_chunks(text, chunks, size):
    assert len(chunks) > 0
    assert chunks[0].char_start == 0
    assert chunks[-1].char_end == len(text)
    prev = None
    for c in chunks:
        assert c.text == text[c.char_start:c.char_end]
        assert 1 <= c.char_end - c.char_start <= size and len(c.text) == c.char_end - c.char_start
        if prev is not None:
            assert prev.char_start < c.char_start <= prev.char_end
        prev = c

# == T4p
my_fact_chunks_o0 = [1]
my_fact_chunks_o60 = [2]
my_largest_guaranteed_f = 200
my_confidence_t4 = 3

# == T4
import bisect


def chunks_containing(chunks, start, end):
    out = []
    for c in chunks:
        if c.char_start <= start and c.char_end >= end:
            out.append(c.chunk_id)
    return out


def p_formula(S, O, F):
    v = (S - F + 1) / (S - O)
    return 1.0 if v > 1 else v


def p_brute(L, S, O, F):
    ch = fixed_window_chunks("." * L, S, O)
    starts = [c.char_start for c in ch]
    good = 0
    for p in range(L - F + 1):
        k = bisect.bisect_right(starts, p) - 1          # last chunk starting at or before p
        good += ch[k].char_end >= p + F
    return good / (L - F + 1)

# == T5p
my_w_spans = [(0, 8), (4, 12), (8, 15), (12, 22)]
my_confidence_t5 = 2

# == T5
def split_spans(text, start, end, separators, size):
    if end - start <= size:
        return [(start, end)]
    for k, sep in enumerate(separators):
        if sep == "":
            return [(i, i + 1) for i in range(start, end)]
        if text.find(sep, start, end) == -1:
            continue
        cuts, i = [], start
        while True:
            j = text.find(sep, i, end)
            if j < 0:
                break
            cuts.append(j + len(sep))
            i = j + len(sep)
        bounds = [start] + [c for c in cuts if c < end] + [end]
        res = []
        for a, b in zip(bounds, bounds[1:]):
            res += split_spans(text, a, b, separators[k + 1:], size)
        return res
    return [(i, i + 1) for i in range(start, end)]


def recursive_chunks(text, size, overlap=0, separators=SEPARATORS):
    if not (size > 0 and 0 <= overlap < size):
        raise ValueError("bad size/overlap")
    pieces = split_spans(text, 0, len(text), list(separators), size) if text else []
    result, lo, hi = [], 0, 0          # current chunk = pieces[lo:hi]
    while hi < len(pieces):
        if lo < hi and pieces[hi][1] - pieces[lo][0] > size:
            result.append((pieces[lo][0], pieces[hi - 1][1]))
            end = pieces[hi - 1][1]
            new_lo = hi
            while new_lo - 1 >= lo and end - pieces[new_lo - 1][0] <= overlap:
                new_lo -= 1
            lo = new_lo
            while lo < hi and pieces[hi][1] - pieces[lo][0] > size:
                lo += 1
        hi += 1
    if lo < hi:
        result.append((pieces[lo][0], pieces[hi - 1][1]))
    return [Chunk(i, text[a:b], a, b) for i, (a, b) in enumerate(result)]

# == T6p
my_guess_per_page_count = 92

# == T6
from itertools import accumulate


def chunk_pages(pages, size, overlap):
    offs = [0] + list(accumulate(len(p) + 1 for p in pages))[:-1]
    return [(o + c.char_start, o + c.char_end, n) for n, (o, p) in enumerate(zip(offs, pages), start=1)
            for c in recursive_chunks(p, size, overlap)]

# == T7
import hashlib as _h


def params_hash(params):
    blob = json.dumps(params, sort_keys=True)
    return _h.sha256(blob.encode("utf-8")).hexdigest()[:12]


def make_records(doc_id, snapshot_id, pages, params):
    ph = params_hash(params)
    offs = [0] + list(accumulate(len(p) + 1 for p in pages))[:-1]
    joined = "\n".join(pages)
    recs = []
    for seq, (a, b, pg) in enumerate(chunk_pages(pages, params["chunk_size"], params["chunk_overlap"])):
        t = joined[a:b]
        recs.append(dict(doc_id=doc_id, snapshot_id=snapshot_id, chunk_id=f"{doc_id}:{snapshot_id}:{ph}:{seq:05d}",
                         seq=seq, char_start=a, char_end=b,
                         page_segments=[dict(page=pg, char_start=a - offs[pg - 1], char_end=b - offs[pg - 1])],
                         text=t, text_sha256=_h.sha256(t.encode("utf-8")).hexdigest(), chunker=params["name"],
                         params_hash=ph, meta={}))
    return recs

# == T8p
my_guess_all_200 = True

# == T8
def achieved_overlaps(records):
    out = []
    for prev, nxt in zip(records, records[1:]):
        if prev["page_segments"][0]["page"] == nxt["page_segments"][0]["page"]:
            out.append(prev["char_end"] - nxt["char_start"])
    return out
