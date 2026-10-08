"""Minimal, framework-free chunkers proposed for the C2 lesson (Part H.1). Python 3.12, stdlib only.

Conventions: character offsets, half-open spans [char_start, char_end); chunk.text == doc[char_start:char_end].
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    text: str
    char_start: int  # inclusive offset into the source text
    char_end: int    # exclusive offset
    page_start: int | None = None  # 1-based page of char_start (page-aware chunker only)
    page_end: int | None = None    # 1-based page of char_end - 1


def fixed_window_chunks(text: str, size: int, overlap: int = 0) -> list[Chunk]:
    """Windows of `size` chars, each starting `size - overlap` chars after the previous one."""
    if size <= 0:
        raise ValueError("size must be > 0")
    if not 0 <= overlap < size:
        raise ValueError(f"need 0 <= overlap < size, got overlap={overlap}, size={size}")
    stride = size - overlap
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(Chunk(len(chunks), text[start:end], start, end))
        if end == len(text):
            break
        start += stride
    return chunks


DEFAULT_SEPARATORS = ("\n\n", "\n", " ")


def _split_spans(text: str, start: int, end: int, seps: tuple[str, ...], size: int) -> list[tuple[int, int]]:
    """Recursively cut [start, end) into contiguous pieces of <= size chars, preferring early separators.
    A separator stays attached to the END of the piece before it, so pieces tile the text exactly."""
    if end - start <= size:
        return [(start, end)]
    if not seps:  # last resort (like LangChain's "" separator): single characters, merged later
        return [(s, s + 1) for s in range(start, end)]
    sep, rest = seps[0], seps[1:]
    pieces, i = [], start
    while i < end:
        j = text.find(sep, i, end)
        if j == -1:
            pieces.append((i, end))
            break
        pieces.append((i, j + len(sep)))
        i = j + len(sep)
    out: list[tuple[int, int]] = []
    for a, b in pieces:
        out.extend([(a, b)] if b - a <= size else _split_spans(text, a, b, rest, size))
    return out


def recursive_chunks(text: str, size: int, overlap: int = 0,
                     separators: tuple[str, ...] = DEFAULT_SEPARATORS) -> list[Chunk]:
    """Simplified recursive splitter: split on the coarsest separator that works, then greedily merge
    pieces up to `size`; the next chunk re-starts with whole trailing pieces totalling <= `overlap`.
    Unlike LangChain it never strips whitespace, so offsets stay exact."""
    if not 0 <= overlap < size:
        raise ValueError(f"need 0 <= overlap < size, got overlap={overlap}, size={size}")
    if not text:
        return []
    pieces = _split_spans(text, 0, len(text), separators, size)
    spans: list[tuple[int, int]] = []
    cur: list[tuple[int, int]] = []
    for p in pieces:
        if cur and p[1] - cur[0][0] > size:  # adding p would overflow: emit current chunk
            spans.append((cur[0][0], cur[-1][1]))
            keep = []
            for q in reversed(cur):  # whole trailing pieces that fit in the overlap budget
                if cur[-1][1] - q[0] <= overlap:
                    keep.insert(0, q)
                else:
                    break
            cur = keep
            while cur and p[1] - cur[0][0] > size:  # make room for p
                cur.pop(0)
        cur.append(p)
    if cur:
        spans.append((cur[0][0], cur[-1][1]))
    return [Chunk(i, text[a:b], a, b) for i, (a, b) in enumerate(spans)]


def join_pages(pages: list[str], sep: str = "\n") -> tuple[str, list[int]]:
    """Concatenate page texts; return the full text and the start offset of each page."""
    starts, parts, pos = [], [], 0
    for i, p in enumerate(pages):
        if i:
            parts.append(sep)
            pos += len(sep)
        starts.append(pos)
        parts.append(p)
        pos += len(p)
    return "".join(parts), starts


def page_of(offset: int, page_starts: list[int]) -> int:
    """1-based page number containing character `offset`."""
    return bisect.bisect_right(page_starts, offset)


def page_aware_chunks(pages: list[str], size: int, overlap: int, chunker=recursive_chunks) -> list[Chunk]:
    """Chunk ACROSS page breaks (so a sentence cut by a page break can still land in one chunk)
    while recording which pages each chunk spans."""
    full, starts = join_pages(pages)
    out = []
    for c in chunker(full, size, overlap):
        out.append(Chunk(c.chunk_id, c.text, c.char_start, c.char_end,
                         page_of(c.char_start, starts), page_of(c.char_end - 1, starts)))
    return out


def check_chunks(text: str, chunks: list[Chunk], size: int) -> None:
    """Property checks: offsets reproduce text, size limit, full coverage, no gaps, non-negative overlap."""
    assert chunks, "no chunks"
    assert chunks[0].char_start == 0 and chunks[-1].char_end == len(text), "must start at 0 and end at len"
    for c in chunks:
        assert text[c.char_start:c.char_end] == c.text, f"offsets wrong for chunk {c.chunk_id}"
        assert 0 < len(c.text) <= size, f"chunk {c.chunk_id} has length {len(c.text)}"
    for a, b in zip(chunks, chunks[1:]):
        assert b.char_start <= a.char_end, f"gap between chunk {a.chunk_id} and {b.chunk_id}"
        assert b.char_start > a.char_start, "no forward progress"
    # rebuild the document by dropping each chunk's overlap with its predecessor
    rebuilt = chunks[0].text + "".join(b.text[a.char_end - b.char_start:] for a, b in zip(chunks, chunks[1:]))
    assert rebuilt == text, "overlap-removed concatenation must reproduce the document"


def chunks_containing(chunks: list[Chunk], start: int, end: int) -> list[int]:
    """ids of chunks that wholly contain the span [start, end)."""
    return [c.chunk_id for c in chunks if c.char_start <= start and end <= c.char_end]
