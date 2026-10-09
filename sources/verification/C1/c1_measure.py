"""C1: produce every measured number in concepts/C1_document_parsing.md (sections S1-S10).

Run from rag_learning/ (Git Bash), with the project env (pymupdf pinned at 1.26.7):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_measure.py "$B" <scratch dir> \
        > sources/verification/C1/out_c1_measure.txt 2> sources/verification/C1/out_c1_measure.stderr.txt
<scratch dir> receives the synthetic zoo PDF and the newline test files; it must be OUTSIDE the workspace.
Read-only on the book, the repo and the PDFs. No API calls; .env is never read.
"""
import hashlib
import json
import math
import os
import re
import sys
import unicodedata

import pymupdf as fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_ref as R  # noqa: E402
from c1_zoo import ZOO_LEFT, ZOO_RIGHT, build_zoo  # noqa: E402

BASE, SCRATCH = sys.argv[1], sys.argv[2]
CLIMATE = os.path.join(BASE, "upstream", "RAG_Techniques", "data", "Understanding_Climate_Change.pdf")
BOOK = os.path.join(BASE, "RAG_Made_Simple_The_Complete_Visual_Guide")


def sec(t):
    print(f"\n=== {t}")


def fsha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------------ S1
sec("S1 Environment and inputs")
print("python", sys.version.split()[0], "| pymupdf", fitz.VersionBind, "| fitz.VersionBind == '1.26.7':", fitz.VersionBind == "1.26.7")
print("climate sha256", fsha(CLIMATE), "bytes", os.path.getsize(CLIMATE), "pages", len(fitz.open(CLIMATE)))
ch1 = os.path.join(BOOK, "chapter 1.pdf")
print("book chapter 1.pdf sha256", fsha(ch1)[:16], "pages", len(fitz.open(ch1)))

# ------------------------------------------------------------------------------------------------ S2
sec("S2 Corpus D: pages, doc_text, page_table, snapshot_id (06 §5.3)")
pages = R.load_pages(CLIMATE, "climate")
texts = [p.text for p in pages]
print("Page[0]:", pages[0].doc_id, pages[0].page, repr(pages[0].text[:28]), pages[0].parser)
print("n pages", len(pages), "| first/last page number", pages[0].page, pages[-1].page)
print("page lengths", [len(t) for t in texts])
print("sum of page lengths", sum(map(len, texts)), "| min", min(map(len, texts)), "(page", 1 + texts.index(min(texts, key=len)), ") | max", max(map(len, texts)))
doc_text, table = R.build_page_table(texts)
dsha = R.sha256_hex(doc_text)
print("len(doc_text)", len(doc_text), "= sum + 32 joins:", len(doc_text) == sum(map(len, texts)) + 32)
print("doc_text_sha256", dsha)
for r in table[:3]:
    print("row", r)
for p in (8, 10, 23, 29, 33):
    print(f"page {p} doc_char_start", table[p - 1]["doc_char_start"], "end", table[p - 1]["doc_char_end"])
print("round trip doc_text[s:e] == page text on all pages:", all(doc_text[r["doc_char_start"]:r["doc_char_end"]] == t for r, t in zip(table, texts)))
print("every page ends with '\\n':", all(t.endswith("\n") for t in texts))
print("'\\n\\n' in doc_text:", doc_text.count("\n\n"), "| of them at page joins:",
      sum(doc_text[r["doc_char_end"] - 1:r["doc_char_end"] + 1] == "\n\n" for r in table[:-1]))
pinfo = R.parser_info()
sid = R.snapshot_id("pymupdf", pinfo["version"], {}, "none", {"climate": dsha})
print("parser block", pinfo)
print("snapshot_id", sid, "| equals 06 §5.3 published ea07572562ac:", sid == "ea07572562ac")

# ------------------------------------------------------------------------------------------------ S3
sec("S3 What changes the snapshot_id (same recipe, one input changed at a time)")
print("version 1.28.2, same text  ->", R.snapshot_id("pymupdf", "1.28.2", {}, "none", {"climate": dsha}))
print("cleaning 'tabs_v1', same text (no tabs, so text unchanged) ->", R.snapshot_id("pymupdf", "1.26.7", {}, "tabs_v1", {"climate": dsha}))
print("options {'sort': True}, same text ->", R.snapshot_id("pymupdf", "1.26.7", {"sort": True}, "none", {"climate": dsha}))
one = texts[:]
one[0] = one[0] + " "
d1, _ = R.build_page_table(one)
print("one extra space at the end of page 1 ->", R.snapshot_id("pymupdf", "1.26.7", {}, "none", {"climate": R.sha256_hex(d1)}))
parts_nl = ["snapshot-v1", "parser=pymupdf@1.26.7", "options={}", "cleaning=none", "page_join=\n", f"climate:{dsha}"]
print("page_join read as a REAL newline ->", hashlib.sha256("|".join(parts_nl).encode()).hexdigest()[:12])
tabs_replaced = [t.replace("\t", " ") for t in texts]
print("replace_t_with_space changes the text:", tabs_replaced != texts, "| tabs in Corpus D:", sum(t.count("\t") for t in texts))

# ------------------------------------------------------------------------------------------------ S4
sec("S4 Same PDF, other extraction calls (Corpus D)")
with fitz.open(CLIMATE) as d:
    same_text = sum(p.get_text("text") == t for p, t in zip(d, texts))
    sort_diff = sum(p.get_text(sort=True) != t for p, t in zip(d, texts))
    sort_ws = sum(re.sub(r"\s+", " ", p.get_text(sort=True)).strip() == re.sub(r"\s+", " ", t).strip() for p, t in zip(d, texts))
    x0s = sorted({round(b[0]) for p in d for b in p.get_text("blocks") if b[6] == 0})
    imgs = sum(len(p.get_images()) for p in d)
    tables = sum(len(p.find_tables().tables) for p in d)
print("get_text('text') identical to get_text() on", same_text, "of 33 pages")
print("get_text(sort=True) differs on", sort_diff, "pages; equal after whitespace collapse on", sort_ws, "of 33")
print("distinct text-block x0 values", x0s, "| images", imgs, "| find_tables", tables)
concat = "".join(texts)                                # helper_functions.read_pdf_to_string (L223-L245)
print("read_pdf_to_string length", len(concat), "| our doc_text", len(doc_text))
print("page 2 starts at", len(texts[0]), "(read_pdf_to_string) vs", table[1]["doc_char_start"], "(doc_text); page 33:", sum(map(len, texts[:32])), "vs", table[32]["doc_char_start"])
stripped = [t.strip() for t in texts]                  # multi_model_rag_with_captioning.ipynb cell 9
print("sum of page.get_text().strip() lengths", sum(map(len, stripped)), "| chars removed by strip", sum(map(len, texts)) - sum(map(len, stripped)))

# ------------------------------------------------------------------------------------------------ S5
sec("S5 Corpus D artifact inventory (raw text)")
a = R.artifact_counts(texts)
for k, v in a.items():
    print(k, v if k != "hyphen_breaks" else len(v))
for pno, s in a["hyphen_breaks"]:
    print("  hyphen break p.%d %r" % (pno, s))
thr, rep = R.repeated_lines(texts)
print("repeated-line threshold", thr, "| lines over it", rep)
c3 = {}
for t in texts:
    for k in {R.line_key(x) for x in t.split("\n") if x.strip()}:
        c3[k] = c3.get(k, 0) + 1
print("line keys on >= 3 pages:", {k: v for k, v in c3.items() if v >= 3})
ends = [t.rstrip() for t in texts]
nonterm = [i for i, t in enumerate(ends[:-1], 1) if t and t[-1] not in '.!?:")\'']
lower_next = [i for i in nonterm if texts[i].lstrip()[:1].islower()]
print("page breaks (32) where page N does not end in . ! ? : \" ) ':", len(nonterm), nonterm)
print("  ...and page N+1 starts lowercase (mid-sentence cut):", len(lower_next), [f"{i}->{i + 1}" for i in lower_next])
vocab = {w.lower() for t in texts for w in re.findall(r"[A-Za-z]+", t)}
for pno, s in a["hyphen_breaks"]:
    l, r = s.split("-\n")
    print(f"  naive join p.{pno}: {l + r!r}; joined word attested elsewhere: {(l + r).lower() in vocab}; hyphenated form elsewhere: {(l + '-' + r).lower() in doc_text.lower()}")

# ------------------------------------------------------------------------------------------------ S6
sec("S6 Paris Agreement offsets and page lookup (doc offsets -> page)")
first = doc_text.find("Paris Agreement")
print("first 'Paris Agreement' doc offset", first, "-> (page, page offset)", R.page_of(first, table))
pages_with = sorted({R.page_of(m.start(), table)[0] for m in re.finditer("Paris Agreement", doc_text)})
print("pages containing 'Paris Agreement'", pages_with, "| occurrences", doc_text.count("Paris Agreement"))
join1 = table[0]["doc_char_end"]
print("offset", join1, "(the join after page 1) ->", R.page_of(join1, table), "| offset", join1 + 1, "->", R.page_of(join1 + 1, table))
print("offset 0 ->", R.page_of(0, table), "| last offset", len(doc_text) - 1, "->", R.page_of(len(doc_text) - 1, table))

# ------------------------------------------------------------------------------------------------ S7
sec("S7 Writing the snapshot text on Windows: newline translation")
p_default = os.path.join(SCRATCH, "climate_default.txt")
p_lf = os.path.join(SCRATCH, "climate_lf.txt")
with open(p_default, "w", encoding="utf-8") as f:
    f.write(doc_text)
with open(p_lf, "w", encoding="utf-8", newline="\n") as f:
    f.write(doc_text)
print("os.linesep", repr(os.linesep), "| newlines in doc_text", doc_text.count("\n"), "| utf-8 bytes of doc_text", len(doc_text.encode("utf-8")))
print("default open(): bytes", os.path.getsize(p_default), "| file sha256 == doc_text_sha256:", fsha(p_default) == dsha)
print("newline='\\n':   bytes", os.path.getsize(p_lf), "| file sha256 == doc_text_sha256:", fsha(p_lf) == dsha)
print("reading the default file back in text mode gives doc_text:", open(p_default, encoding="utf-8").read() == doc_text)
print("reading it with newline='' gives doc_text:", open(p_default, encoding="utf-8", newline="").read() == doc_text)
man = R.build_manifest("D", "1.0", [{"doc_id": "climate", "pdf_sha256": fsha(CLIMATE), "bytes": os.path.getsize(CLIMATE),
                                     "pages": 33, "doc_text_sha256": dsha, "page_table": table}],
                       pinfo, R.CLEANING_NONE, "2026-10-08T00:00:00Z")
R.validate_snapshot(man, {"climate": doc_text})
print("manifest validates:", True, "| manifest snapshot_id", man["snapshot_id"])
bad = json.loads(json.dumps(man))
bad["docs"][0]["page_table"][1]["doc_char_start"] += 1
bad["docs"][0]["page_table"][1]["doc_char_end"] += 1
try:
    R.validate_snapshot(bad, {"climate": doc_text})
    print("shifted page 2 accepted (BAD)")
except ValueError as e:
    print("shifted page 2 rejected:", e)

# ------------------------------------------------------------------------------------------------ S8
sec("S8 Book chapter 1 as a parsing specimen (not a corpus): figures, a table, list bullets")
with fitz.open(ch1) as d:
    print("chars per page", [len(p.get_text()) for p in d])
    print("images per page", [len(p.get_images()) for p in d])
    t_all = "".join(p.get_text() for p in d)
    print("bullet characters '•' in chapter 1 text", t_all.count("\u2022"), "| non-breaking spaces", t_all.count("\xa0"))
    p2 = d[1]
    irect = p2.get_image_rects(p2.get_images()[0][0])[0]
    inside = [b for b in p2.get_text("blocks") if fitz.Rect(b[:4]).intersects(irect)]
    print("p.2: image rect", [round(x) for x in irect], "| text blocks intersecting the image", len(inside))
    p13 = d[12]
    t13 = p13.get_text()
    print("p.13: find_tables() default (ruling lines)", len(p13.find_tables().tables), "| strategy='text'", len(p13.find_tables(strategy="text").tables))
    tt = p13.find_tables(strategy="text").tables[0].extract()
    print("p.13 strategy='text' table shape", len(tt), "x", len(tt[0]), "| first non-empty cells", [c for c in tt[0] if c][:3])
    print("p.13 first 6 lines of get_text()", t13.split("\n")[:6])
for name in ("intro.pdf", "index.pdf"):
    with fitz.open(os.path.join(BOOK, name)) as d:
        tx = [p.get_text() for p in d]
    thr, rep = R.repeated_lines(tx)
    print(f"{name}: {len(tx)} pages; repeated-line threshold {thr}; flagged {rep}")

# ------------------------------------------------------------------------------------------------ S9
sec("S9 Synthetic artifact zoo (TOY ILLUSTRATION; c1_zoo.py)")
zp = build_zoo(os.path.join(SCRATCH, "zoo.pdf"))
with fitz.open(zp) as d:
    zt = [p.get_text() for p in d]
    print("pages", len(zt), "| chars per page", [len(t) for t in zt], "| images per page", [len(p.get_images()) for p in d])
    print("p.1 default get_text() lines", zt[0].split("\n"))
    truth = ZOO_LEFT + ZOO_RIGHT
    got = [x for x in zt[0].split("\n") if x in truth]
    print("p.1 body lines in true reading order:", got == truth, "| order got", [("L" if x in ZOO_LEFT else "R") + str((ZOO_LEFT + ZOO_RIGHT).index(x) % 4 + 1) for x in got])
    srt = d[0].get_text(sort=True)
    print("p.1 sort=True first body line", [x for x in srt.split("\n") if "Parsing" in x])
    col = R.extract_columns(d[0])
    gotc = [x for x in col.split("\n") if x in truth]
    print("p.1 extract_columns body lines in true order:", gotc == truth)
    print("p.1 TEXT_DEHYPHENATE on the default order:", [x for x in d[0].get_text(flags=fitz.TEXTFLAGS_TEXT | fitz.TEXT_DEHYPHENATE).split("\n") if "extrac" in x])
    print("p.1 TEXT_DEHYPHENATE with column clips:", [x for x in (d[0].get_text(clip=fitz.Rect(0, 0, 297.5, 842), flags=fitz.TEXTFLAGS_TEXT | fitz.TEXT_DEHYPHENATE)).split("\n") if "extrac" in x])
    lig_line = [x for x in zt[0].split("\n") if "flag" in unicodedata.normalize("NFKC", x)][0]
    print("p.1 ligature line", repr(lig_line), "| ligature chars", sum(lig_line.count(c) for c in R.LIGATURES), "| 'file' in it:", "file" in lig_line, "| after NFKC:", "file" in unicodedata.normalize("NFKC", lig_line))
    nolig = d[0].get_text(flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_PRESERVE_LIGATURES)
    print("p.1 without TEXT_PRESERVE_LIGATURES: ligature chars", sum(nolig.count(c) for c in R.LIGATURES))
    print("p.2 get_text() lines", zt[1].split("\n"))
    print("p.2 find_tables()", len(d[1].find_tables().tables), d[1].find_tables().tables[0].extract())
    print("p.3 text", repr(zt[2]), "images", len(d[2].get_images()), "| p.4 text", repr(zt[3]), "images", len(d[3].get_images()))
    print("TEXTFLAGS_TEXT default includes PRESERVE_LIGATURES:", bool(fitz.TEXTFLAGS_TEXT & fitz.TEXT_PRESERVE_LIGATURES), "| DEHYPHENATE:", bool(fitz.TEXTFLAGS_TEXT & fitz.TEXT_DEHYPHENATE))
    za = R.artifact_counts(zt)
    print("zoo artifact counts:", {k: (len(v) if k == "hyphen_breaks" else v) for k, v in za.items()})
    thr, rep = R.repeated_lines(zt)
    print("zoo repeated-line threshold", thr, "| flagged", rep)
    zpages = [col] + zt[1:]                            # page 1 extracted by columns (a parser option)

# ------------------------------------------------------------------------------------------------ S10
sec("S10 Logged cleaning rules R1-R3 (none applied in v0)")
edits = R.plan_edits("zoo", zpages)
for e in edits:
    print("  ", {k: e[k] for k in ("page", "rule", "start", "end", "before", "after", "context")})
by_rule = {}
for e in edits:
    by_rule[e["rule"]] = by_rule.get(e["rule"], 0) + 1
print("zoo edits by rule", by_rule, "| raw chars removed", sum(e["end"] - e["start"] for e in edits), "| chars inserted", sum(len(e["after"]) for e in edits))
ok = True
for i, t in enumerate(zpages, 1):
    pe = [e for e in edits if e["page"] == i]
    cleaned, src = R.apply_edits(t, pe)
    ok &= R.undo_edits(cleaned, src, pe, len(t)) == t
    ok &= len(src) == len(cleaned)
    if i == 1:
        print("zoo p.1 cleaned lines", cleaned.split("\n"))
        k = cleaned.find("extraction")
        print("zoo p.1 cleaned 'extraction' at", k, "-> raw page offsets", src[k], "..", src[k + len("extraction") - 1], "| raw text there", repr(t[src[k]:src[k + len("extraction") - 1] + 1]))
print("provenance round trip (undo(apply(edits)) == raw) on every zoo page:", ok)
de = R.plan_edits("climate", texts)
print("Corpus D: edits the same rules would make", len(de), {e["rule"] for e in de} or "{}")
naive = sum(len(R.HYPHEN_BREAK.findall(t)) for t in texts)
print("Corpus D: a naive '-\\n' join rule would change", naive, "places")

# ------------------------------------------------------------------------------------------------ S12
sec("S12 Part F worked example (TOY ILLUSTRATION)")
toy = ["Ice melts.\n", "Seas rise.\n", "Act now.\n"]
tdoc, trows = R.build_page_table(toy)
print("toy doc_text", repr(tdoc), "len", len(tdoc))
print("toy rows", [(r["page"], r["doc_char_start"], r["doc_char_end"]) for r in trows])
for o in (10, 11, 12, tdoc.find("rise"), 30):
    print("toy page_of", o, "->", R.page_of(o, trows))
big = ["Ice melts.\n" * 2, "Seas rise.\n", "Act now.\n"]
bdoc, brows = R.build_page_table(big)
print("toy page 1 doubled: page 2 start", brows[1]["doc_char_start"], "| len", len(bdoc),
      "| ids differ:", R.snapshot_id("pymupdf", "1.26.7", {}, "none", {"toy": R.sha256_hex(tdoc)}) != R.snapshot_id("pymupdf", "1.26.7", {}, "none", {"toy": R.sha256_hex(bdoc)}))
hp = ["later extrac-\ntion\n", "extraction\n"]
he = R.plan_edits("toy", hp)
print("toy R2 edits", [(e["page"], e["rule"], e["start"], e["end"], e["before"]) for e in he])
hc, hs = R.apply_edits(hp[0], [e for e in he if e["page"] == 1])
print("toy cleaned", repr(hc), "| src", hs)
