"""C1 kit measurements K1-K12 for the HTML lesson (study/lessons/C1_parsing.html), added 2026-10-18.

Run from rag_learning/ (Git Bash), project env (pymupdf pinned at 1.26.7):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_kit_measure.py "$B" <scratch dir> \
        > sources/verification/C1/out_c1_kit_measure.txt 2> sources/verification/C1/out_c1_kit_measure.stderr.txt
<scratch dir> receives the two synthetic PDFs (the zoo of c1_zoo.py and the "paper" page built here); it must be
OUTSIDE the workspace. Read-only on the repo PDF. No book PDF is opened. No API call; .env is never read.
c1_measure.py and its output are unchanged; S1-S12 stay the facts they were.
"""
import hashlib
import math
import os
import re
import sys
import unicodedata

import pymupdf as fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_ref as R  # noqa: E402
from c1_zoo import build_zoo  # noqa: E402

BASE, SCRATCH = sys.argv[1], sys.argv[2]
CLIMATE = os.path.join(BASE, "upstream", "RAG_Techniques", "data", "Understanding_Climate_Change.pdf")
LIG = R.LIGATURES


def sec(t):
    print(f"\n=== {t}")


def sh(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def line_starts(page):
    """(x0, y0, text) of every text line, in the order PyMuPDF's default extraction walks them."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            t = "".join(s["text"] for s in ln["spans"]).strip()
            if t:
                out.append((ln["bbox"][0], ln["bbox"][1], t))
    return out


def rl_jumps(page):
    """Right-to-left jumps: a line starting in the right half followed by one starting in the left half,
    counted only on lines below the top 10% and above the bottom 10% (running headers and footers excluded)."""
    mid, h = page.rect.width / 2, page.rect.height
    ls = [l for l in line_starts(page) if 0.1 * h < l[1] < 0.9 * h]
    return sum(1 for a, b in zip(ls, ls[1:]) if a[0] >= mid and b[0] < mid)


def nfkc_changes(text):
    """Characters that NFKC would change, and the total length delta."""
    ch = [c for c in text if unicodedata.normalize("NFKC", c) != c]
    return len(ch), len(unicodedata.normalize("NFKC", text)) - len(text)


# --------------------------------------------------------------------------------------------- K1
sec("K1 Environment")
print("python", sys.version.split()[0], "| pymupdf", fitz.VersionBind, "| unicodedata", unicodedata.unidata_version)

# --------------------------------------------------------------------------------------------- K2
sec("K2 The 37-character PyPDFLoader gap, by arithmetic on PyMuPDF text (S4, S11, LAB_FACTS §7)")
pages = R.load_pages(CLIMATE, "climate")
texts = [p.text for p in pages]
raw_sum = sum(len(t) for t in texts)
no_final_nl = sum(len(t[:-1]) for t in texts)              # S11: pymupdf page == pypdf page + "\n" on 33/33
stripped = sum(len(t.strip()) for t in texts)
print("pages", len(texts), "| every page ends with \\n:", all(t.endswith("\n") for t in texts))
print("sum of PyMuPDF page lengths", raw_sum, "| joined with \\n", raw_sum + 32)
print("pypdf pages (= PyMuPDF page minus final \\n, S11): sum", no_final_nl, "| joined", no_final_nl + 32)
print(".strip() per page: sum", stripped, "| joined", stripped + 32, "| removed vs pypdf", no_final_nl - stripped,
      "| removed vs PyMuPDF", raw_sum - stripped)
print("joined stripped == LAB_FACTS §7 PyPDFLoader full_len 72523:", stripped + 32 == 72523)
lead = sum(len(t) - len(t.lstrip()) for t in texts)
trail_extra = sum(len(t[:-1]) - len(t[:-1].rstrip()) for t in texts)
print("leading whitespace removed", lead, "| trailing whitespace before the final \\n", trail_extra)

# --------------------------------------------------------------------------------------------- K3
sec("K3 Characters, bytes, normalisation (literal strings)")
SAMPLES = [("ligature fi", "\ufb01"), ("ligature fl", "\ufb02"), ("ellipsis", "\u2026"), ("one half", "\u00bd"),
           ("x squared", "x\u00b2"), ("e acute, one code point", "\u00e9"), ("e + combining acute", "e\u0301"),
           ("em dash", "\u2014"), ("soft hyphen", "\u00ad"), ("non-breaking space", "\u00a0"), ("plain a", "a")]
print("name | code points | UTF-8 bytes | NFC | NFKC | NFKC length | delta")
for name, s in SAMPLES:
    nfc, nfkc = unicodedata.normalize("NFC", s), unicodedata.normalize("NFKC", s)
    print(f"{name} | {' '.join(f'U+{ord(c):04X}' for c in s)} | {len(s.encode('utf-8'))} | {nfc!r} len {len(nfc)} | "
          f"{nfkc!r} | {len(nfkc)} | {len(nfkc) - len(s):+d}")
print("'file' in 'The \\ufb01le':", "file" in "The \ufb01le", "| after NFKC:", "file" in unicodedata.normalize("NFKC", "The \ufb01le"))
doc_text = "\n".join(texts)
n_ch, delta = nfkc_changes(doc_text)
print("Corpus D: characters NFKC would change", n_ch, "| length delta", delta,
      "| chars", len(doc_text), "| UTF-8 bytes", len(doc_text.encode("utf-8")),
      "| non-ASCII", sorted({c for c in doc_text if ord(c) > 127}))

# --------------------------------------------------------------------------------------------- K4
sec("K4 Offset shift after ligature decomposition (TOY)")
body = ("Parsing is the first step. " * 30)[:520]
toy = body[:100] + "\ufb01" + body[101:300] + "\ufb02" + body[301:]
assert len(toy) == 520 and toy[100] == "\ufb01" and toy[300] == "\ufb02"
mark = toy[500]
dec = unicodedata.normalize("NFKC", toy)
src = []                                                    # cleaned index -> raw index
for i, c in enumerate(toy):
    src.extend([i] * len(unicodedata.normalize("NFKC", c)))
new_pos = src.index(500)
print("toy length", len(toy), "| ligatures at raw 100 and 300 | raw[500] =", repr(mark))
print("after NFKC: length", len(dec), "| raw offset 500 is now at", new_pos, "| same character:", dec[new_pos] == mark)
print("a ligature at 120 shifts every later offset by", len(unicodedata.normalize("NFKC", "\ufb01")) - 1)
print("cleaned->raw map: cleaned 101 <- raw", src[101], "| cleaned 102 <- raw", src[102], "| cleaned 502 <- raw", src[502])

# --------------------------------------------------------------------------------------------- K5
sec("K5 A hash names exact bytes (toy strings)")
for s in ["Seas rise.\n", "Seas rise. \n", "Seas rise.\r\n", "seas rise.\n"]:
    print(repr(s), "len", len(s), "| sha256[:12]", sh(s))
print("page 2 of Part F with one extra space: id changes as the text hash changes (S3 row 'one extra space')")

# --------------------------------------------------------------------------------------------- K6
sec("K6 PyMuPDF text flags (as installed)")
print("TEXTFLAGS_TEXT", fitz.TEXTFLAGS_TEXT, "| bits:",
      {n: bool(fitz.TEXTFLAGS_TEXT & getattr(fitz, n)) for n in
       ("TEXT_PRESERVE_LIGATURES", "TEXT_PRESERVE_WHITESPACE", "TEXT_PRESERVE_IMAGES", "TEXT_DEHYPHENATE",
        "TEXT_MEDIABOX_CLIP", "TEXT_CID_FOR_UNKNOWN_UNICODE")})
print("TEXT_DEHYPHENATE", fitz.TEXT_DEHYPHENATE, "| TEXT_PRESERVE_LIGATURES", fitz.TEXT_PRESERVE_LIGATURES)

# --------------------------------------------------------------------------------------------- K7
sec("K7 Zoo (c1_zoo.py, TOY): per-page signals as a parse check sees them")
zoo_path = build_zoo(os.path.join(SCRATCH, "c1_zoo.pdf"))
zoo = fitz.open(zoo_path)
zt = [p.get_text() for p in zoo]
thr, rep = R.repeated_lines(zt)
print("repeated-line threshold", thr, "| repeated", rep)
print("page | chars | images | ligatures | hyphen breaks | R->L jumps | tables (lines) | NFKC delta")
for i, p in enumerate(zoo, 1):
    t = zt[i - 1]
    print(i, "|", len(t), "|", len(p.get_images()), "|", sum(t.count(c) for c in LIG), "|",
          len(R.HYPHEN_BREAK.findall(t)), "|", rl_jumps(p), "|", len(p.find_tables().tables), "|", nfkc_changes(t)[1])
print("zoo p.1 line order:", " / ".join(l[2][:18] for l in line_starts(zoo[0])))

# --------------------------------------------------------------------------------------------- K8
sec("K8 A two-column 'paper' page drawn column by column (TOY, built here)")
PAPER_L = ["Dense retrieval maps each passage", "to a vector and finds the nearest", "ones to the question vector. We",
           "train the encoder on question and", "passage pairs from five data sets,", "and report top-k retrieval accu-",
           "racy on each test set below."]
PAPER_R = ["Table 1 shows the accuracy. The", "dense model beats BM25 on four", "of the five sets, by a wide mar-",
           "gin on the open-domain ones.", "The score is s(q, p) = q\u00b7p, the", "dot product of the two vectors,",
           "with \u2016q\u2016 \u2264 1 for every question."]
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
    tw.append((60, 330), "The \ufb01nal \ufb01gure is a \ufb02at line.", font=lig_font, fontsize=10)
    tw.write_text(p)
    doc.save(path)
    return path


paper = fitz.open(build_paper(os.path.join(SCRATCH, "c1_paper.pdf")))
pg = paper[0]
dflt, srt = pg.get_text(), pg.get_text(sort=True)
truth_l = " ".join(PAPER_L)
print("default text, first 5 lines:", dflt.split("\n")[:5])
print("default: left column comes out before the right column:", dflt.index(PAPER_L[-1]) < dflt.index(PAPER_R[0]))
print("default R->L jumps (body lines):", rl_jumps(pg))
mixed = [ln for ln in srt.split("\n") if any(w in ln for w in ("Dense retrieval", "to a vector", "ones to the"))
         and any(w in ln for w in ("Table 1", "dense model", "of the five"))]
print("sort=True: lines holding words of both columns:", len(mixed), "| first:", repr(mixed[0][:70]) if mixed else None)
print("line-end hyphen breaks (default):", R.HYPHEN_BREAK.findall(dflt))
vocab = {w.lower() for w in re.findall(r"[A-Za-z]+", dflt)}
for a, b in R.HYPHEN_BREAK.findall(dflt):
    print(f"  {a}-|{b}: joined '{(a + b).lower()}' attested elsewhere on the page:", (a + b).lower() in vocab)
tab_lines = pg.find_tables()
tab_text = pg.find_tables(strategy="text")
print("find_tables() default (ruling lines):", len(tab_lines.tables), "| strategy='text':", len(tab_text.tables),
      "| first text-table shape:", (tab_text.tables[0].row_count, tab_text.tables[0].col_count) if tab_text.tables else None)
tl = dflt.split("\n")
i0 = tl.index("Method")
print("table as extracted, one cell per line:", tl[i0:i0 + 12])
n_ch, d = nfkc_changes(dflt)
print("ligatures", sum(dflt.count(c) for c in LIG), "| characters NFKC would change", n_ch, "| length delta", d,
      "| NFKC turns 'q\u00b7p' and '\u2016q\u2016 \u2264 1' into:",
      repr(unicodedata.normalize("NFKC", "q\u00b7p")), repr(unicodedata.normalize("NFKC", "\u2016q\u2016 \u2264 1")))
print("'x\u00b2' NFKC:", repr(unicodedata.normalize("NFKC", "x\u00b2")), "| '10\u2075' NFKC:", repr(unicodedata.normalize("NFKC", "10\u2075")))
print("chars", len(dflt), "| images", len(pg.get_images()))

# --------------------------------------------------------------------------------------------- K9
sec("K9 Corpus D per-page signals (the bars of the lesson's chart)")
print("chars per page", [len(t) for t in texts])
print("hyphen breaks per page", {i: len(R.HYPHEN_BREAK.findall(t)) for i, t in enumerate(texts, 1) if R.HYPHEN_BREAK.findall(t)})
with fitz.open(CLIMATE) as d:
    print("images per page (all)", sorted({len(p.get_images()) for p in d}), "| R->L jumps per page (all)",
          sorted({rl_jumps(p) for p in d}), "| tables found (lines) total", sum(len(p.find_tables().tables) for p in d))
print("ligatures", sum(t.count(c) for t in texts for c in LIG), "| U+FFFD", doc_text.count("\ufffd"),
      "| '(cid:' strings", doc_text.count("(cid:"))

# --------------------------------------------------------------------------------------------- K10
sec("K10 Page-table arithmetic (TOY, C1-A-01 and C1-A-02)")
for lens in ([100, 50, 80], [100, 50, 80, 40]):
    dt, rows = R.build_page_table(["x" * (n - 1) + "\n" for n in lens])
    print(lens, "->", [(r["page"], r["doc_char_start"], r["doc_char_end"]) for r in rows], "| len", len(dt))
toy3 = ["Ice melts.\n", "Seas rise.\n", "Act now.\n"]
dt, rows = R.build_page_table(toy3)
print("Part F rows", [(r["page"], r["doc_char_start"], r["doc_char_end"]) for r in rows],
      "| page_of 11, 12, 17:", [R.page_of(o, rows) for o in (11, 12, 17)])

# --------------------------------------------------------------------------------------------- K11
sec("K11 Edits with a map on the paper page (TOY): R2 + R3 only on body text")
ptxt = dflt
vocab_c = {w.lower() for w in re.findall(r"[A-Za-z]+", ptxt)}
edits = []
for m in R.HYPHEN_BREAK.finditer(ptxt):
    if (m.group(1) + m.group(2)).lower() in vocab_c:
        edits.append({"start": m.end(1), "end": m.end(1) + 2, "before": "-\n", "after": ""})
for i, c in enumerate(ptxt):
    if c in LIG:
        edits.append({"start": i, "end": i + 1, "before": c, "after": unicodedata.normalize("NFKC", c)})
cleaned, srcmap = R.apply_edits(ptxt, edits)
print("edits", len(edits), "| R2", sum(e["before"] == "-\n" for e in edits), "| R3", sum(e["before"] in LIG for e in edits),
      "| raw", len(ptxt), "-> cleaned", len(cleaned),
      "| round trip:", R.undo_edits(cleaned, srcmap, edits, len(ptxt)) == ptxt)

# --------------------------------------------------------------------------------------------- K12
sec("K12 Snapshot ids of the paper page under three cleaning versions (TOY recipe of 06 §5.3)")
for cl, txt in (("none", ptxt), ("r3_ligatures_v1", R.apply_edits(ptxt, [e for e in edits if e["before"] in LIG])[0]),
                ("r2r3_v1", cleaned)):
    print(cl, "| text sha256[:12]", sh(txt), "| snapshot_id",
          R.snapshot_id("pymupdf", fitz.VersionBind, {}, cl, {"paper": hashlib.sha256(txt.encode()).hexdigest()}))
print("\nDONE")
