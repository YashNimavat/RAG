"""Build the two tiny synthetic PDFs (TOY ILLUSTRATION) that the C1 apply-it tool's example report reads.

    study/tools/examples/toy_pdfs/c1_zoo.pdf    the 5-page artifact zoo, from c1_zoo.build_zoo (S9, K7)
    study/tools/examples/toy_pdfs/c1_paper.pdf  the two-column "paper" page of K8: build_paper and its constants are
                                                copied verbatim from c1_kit_measure.py (which runs at import, so it
                                                cannot be imported here)

Run from rag_learning/ (Git Bash), project env (pymupdf pinned at 1.26.7):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_make_toy_pdfs.py
The script asserts that the paper page's extracted text has sha256[:12] 4033785d96eb (K12, cleaning "none") and that the
zoo's chars per page are 273, 74, 0, 0, 101 (S9). Fonts are subset, so each file stays a few KB (text unchanged,
asserted). No API call; .env is never read; no book PDF is opened.
"""
import hashlib
import os
import sys
from pathlib import Path

import pymupdf as fitz

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from c1_zoo import build_zoo  # noqa: E402

OUT = HERE.parents[2] / "study" / "tools" / "examples" / "toy_pdfs"

# ---------------------------------------------------------------- verbatim from c1_kit_measure.py, K8
PAPER_L = ["Dense retrieval maps each passage", "to a vector and finds the nearest", "ones to the question vector. We",
           "train the encoder on question and", "passage pairs from five data sets,", "and report top-k retrieval accu-",
           "racy on each test set below."]
PAPER_R = ["Table 1 shows the accuracy. The", "dense model beats BM25 on four", "of the five sets, by a wide mar-",
           "gin on the open-domain ones.", "The score is s(q, p) = q·p, the", "dot product of the two vectors,",
           "with ‖q‖ ≤ 1 for every question."]
TABLE = [["Method", "NQ", "TQA", "SQuAD"], ["BM25", "59.1", "66.9", "68.8"], ["Dense", "78.4", "79.4", "63.2"]]
lig_font = fitz.Font("cjk")


def build_paper(path):
    doc = fitz.open()
    p = doc.new_page(width=595, height=842)
    p.insert_text((150, 60), "A Toy Paper on Dense Retrieval", fontname="helv", fontsize=14)
    y = 110
    for line in PAPER_L:                                        # left column, top to bottom ...
        p.insert_text((60, y), line, fontname="helv", fontsize=10)
        y += 14
    y = 110
    for line in PAPER_R:                                        # ... then the right column (as LaTeX writes it)
        tw = fitz.TextWriter(p.rect)
        tw.append((310, y), line, font=lig_font, fontsize=10)
        tw.write_text(p)
        y += 14
    y = 260                                                     # an unruled results table (text alignment only)
    for row in TABLE:
        for j, cell in enumerate(row):
            p.insert_text((60 + 55 * j, y), cell, fontname="helv", fontsize=10)
        y += 14
    tw = fitz.TextWriter(p.rect)                                # one line with a ligature, below the table
    tw.append((60, 330), "The ﬁnal ﬁgure is a ﬂat line.", font=lig_font, fontsize=10)
    tw.write_text(p)
    doc.save(path)
    return path
# ---------------------------------------------------------------- end of the verbatim copy


def shrink(path):
    """Keep only the glyphs used (the built-in CJK font is about 3.5 MB in full) and rewrite the file compactly.
    The extracted text is asserted unchanged."""
    with fitz.open(path) as d:
        before = [p.get_text() for p in d]
        d.subset_fonts()
        data = d.tobytes(garbage=4, deflate=True)
    with fitz.open("pdf", data) as e:
        assert [p.get_text() for p in e] == before, path
    Path(path).write_bytes(data)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    zoo = shrink(build_zoo(str(OUT / "c1_zoo.pdf")))
    paper = shrink(build_paper(str(OUT / "c1_paper.pdf")))
    with fitz.open(zoo) as d:
        zc = [len(p.get_text()) for p in d]
    with fitz.open(paper) as d:
        pt = [p.get_text() for p in d]
    sha = hashlib.sha256(pt[0].encode("utf-8")).hexdigest()[:12]
    assert zc == [273, 74, 0, 0, 101], zc
    assert len(pt) == 1 and sha == "4033785d96eb", sha
    for f in (zoo, paper):
        print(f"{Path(f).name}: {os.path.getsize(f):,} bytes")
    print("zoo chars per page", zc, "| paper text sha256[:12]", sha, "(K12: 4033785d96eb)")


if __name__ == "__main__":
    main()
