import random

import pytest

from ragkit._core import join_pages
from ragkit.chunking import ChunkerConfig, chunk_document

PAGES = ["Heading\n\nFirst page text that ends mid-sentence because the page",
         "break came here. Second page continues.\n\nNew paragraph on page two."]
CUT = "because the page\nbreak came here."


@pytest.mark.parametrize("scope", ["per_page", "cross_page"])
@pytest.mark.parametrize("name", ["fixed", "recursive"])
def test_offsets_size_and_pages(name, scope):
    cfg = ChunkerConfig(name=name, size=40, overlap=10, scope=scope)
    full, starts = join_pages(PAGES)
    chunks = chunk_document("doc1", PAGES, cfg)
    for c in chunks:
        assert full[c.char_start:c.char_end] == c.text          # offsets reproduce the text
        assert 0 < len(c.text) <= cfg.size                       # size limit in the chosen unit
        assert 1 <= c.page_start <= c.page_end <= len(PAGES)
        if scope == "per_page":
            assert c.page_start == c.page_end                    # per-page never crosses


def test_cross_page_rebuilds_document_and_keeps_cut_sentence():
    # fixed windows guarantee containment when len(CUT) <= overlap + 1 (Part D.3): 33 <= 41
    cfg = ChunkerConfig(name="fixed", size=80, overlap=40, scope="cross_page")
    full, _ = join_pages(PAGES)
    chunks = chunk_document("doc1", PAGES, cfg)
    rebuilt = chunks[0].text + "".join(b.text[a.char_end - b.char_start:] for a, b in zip(chunks, chunks[1:]))
    assert rebuilt == full                                       # every char covered, no gaps
    assert any(CUT in c.text for c in chunks)
    per_page = chunk_document("doc1", PAGES, ChunkerConfig(name="fixed", size=80, overlap=40))
    assert not any(CUT in c.text for c in per_page)


def test_deterministic_ids_and_params_hash():
    cfg = ChunkerConfig(name="recursive", size=40, overlap=10)
    a = chunk_document("doc1", PAGES, cfg)
    b = chunk_document("doc1", PAGES, cfg)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
    assert cfg.params_hash() != ChunkerConfig(name="recursive", size=40, overlap=0).params_hash()


@pytest.mark.parametrize("overlap", [40, 41, -1])
def test_invalid_overlap_rejected(overlap):
    with pytest.raises(ValueError):
        chunk_document("doc1", PAGES, ChunkerConfig(name="fixed", size=40, overlap=overlap))


def test_random_property_sweep():
    rng = random.Random(0)
    words = "alpha beta gamma delta\n\nepsilon zeta\neta theta iota".split(" ")
    pages = [" ".join(rng.choice(words) for _ in range(rng.randint(5, 80))) for _ in range(4)]
    full, _ = join_pages(pages)
    for _ in range(50):
        size = rng.randint(5, 120)
        cfg = ChunkerConfig(name=rng.choice(["fixed", "recursive"]), size=size,
                            overlap=rng.randint(0, size - 1), scope="cross_page")
        chunks = chunk_document("d", pages, cfg)
        assert chunks[0].char_start == 0 and chunks[-1].char_end == len(full)
        assert all(len(c.text) <= size for c in chunks)
