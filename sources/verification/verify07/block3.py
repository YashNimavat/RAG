"""ragkit/chunking.py — design sketch (the H.1 functions live in ragkit/_core.py)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Callable, Protocol

from ragkit._core import join_pages, page_of, recursive_chunks, fixed_window_chunks


@dataclass(frozen=True)
class ChunkerConfig:
    name: str                      # registry key: "fixed" | "recursive"
    size: int
    overlap: int
    unit: str = "chars"            # this sketch supports only "chars"
    scope: str = "per_page"        # "per_page" | "cross_page"
    separators: tuple[str, ...] = ("\n\n", "\n", " ")

    def params_hash(self) -> str:
        blob = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class DocChunk:
    doc_id: str
    chunk_id: str                  # f"{doc_id}:{params_hash}:{seq:05d}" — same input + config -> same id
    seq: int
    text: str
    char_start: int                # offsets into the document text = pages joined with "\n"
    char_end: int
    page_start: int                # 1-based
    page_end: int
    chunker: str
    params_hash: str


class Chunker(Protocol):
    def __call__(self, text: str, size: int, overlap: int) -> list: ...


REGISTRY: dict[str, Callable[[ChunkerConfig], Chunker]] = {
    "fixed": lambda cfg: fixed_window_chunks,
    "recursive": lambda cfg: (lambda t, s, o: recursive_chunks(t, s, o, cfg.separators)),
}


def chunk_document(doc_id: str, pages: list[str], cfg: ChunkerConfig) -> list[DocChunk]:
    if cfg.unit != "chars":
        raise NotImplementedError("token units arrive with I1 (length measured by a named tokenizer)")
    split = REGISTRY[cfg.name](cfg)
    full, starts = join_pages(pages)
    if cfg.scope == "cross_page":
        spans = [(c.char_start, c.char_end) for c in split(full, cfg.size, cfg.overlap)]
    elif cfg.scope == "per_page":
        spans = [(starts[i] + c.char_start, starts[i] + c.char_end)
                 for i, page in enumerate(pages) for c in split(page, cfg.size, cfg.overlap)]
    else:
        raise ValueError(f"unknown scope {cfg.scope!r}")
    h = cfg.params_hash()
    return [DocChunk(doc_id, f"{doc_id}:{h}:{seq:05d}", seq, full[a:b], a, b,
                     page_of(a, starts), page_of(b - 1, starts), cfg.name, h)
            for seq, (a, b) in enumerate(spans)]
