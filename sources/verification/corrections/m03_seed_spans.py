"""M-03 correction: recompute D-004 / D-007 evidence spans on the climate PDF (PyMuPDF page text).
Usage: python -I m03_seed_spans.py <path-to-Understanding_Climate_Change.pdf>
Prints old and corrected spans (page-relative offsets), verifies quotes, and prints snapshot facts."""
import sys, json, hashlib, fitz
pdf = sys.argv[1]
doc = fitz.open(pdf)
pages = [p.get_text() for p in doc]
def find_once(page, needle):
    t = pages[page - 1]
    i = t.find(needle)
    assert i >= 0 and t.find(needle, i + 1) < 0, (page, needle)
    return i
def span(page, start_needle, end_needle):
    a = find_once(page, start_needle)
    b = pages[page - 1].index(end_needle, a) + len(end_needle)
    return a, b
fixes = {
    "D-004 p.23 alt (was [1463,1566))": (23, "Direct Air Capture (DAC)", "negative emissions."),
    "D-007 p.10 (was [211,339))": (10, "The UNFCCC is an international treaty", "the Paris Agreement."),
    "D-007 p.29 (was [963,1078))": (29, "The Conference of the Parties (COP) is the supreme", "on Climate Change (UNFCCC)."),
}
out = {}
for name, (pg, s, e) in fixes.items():
    a, b = span(pg, s, e)
    txt = pages[pg - 1][a:b]
    norm = " ".join(txt.split())
    out[name] = {"page": pg, "char_start": a, "char_end": b, "words": len(norm.split()), "text": norm}
    print(f"{name}: page {pg} [{a},{b}) words={len(norm.split())}\n   {norm!r}")
# snapshot facts: document text = pages joined with "\n"
starts, pos = [], 0
for t in pages:
    starts.append(pos); pos += len(t) + 1
full = "\n".join(pages)
print("pymupdf", fitz.VersionBind, "pages", len(pages), "doc_chars", len(full),
      "doc_text_sha256", hashlib.sha256(full.encode("utf-8")).hexdigest())
for i in range(3):
    print(f" page {i+1}: doc_start={starts[i]} len={len(pages[i])} text_sha256={hashlib.sha256(pages[i].encode('utf-8')).hexdigest()}")
print(" page 23 doc_start", starts[22], "| page 10 doc_start", starts[9], "| page 29 doc_start", starts[28], "| page 8 doc_start", starts[7])
