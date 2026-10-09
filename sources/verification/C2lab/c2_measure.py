"""C2 lab measurements: every expected value used by the CHECK cells of labs/C2_chunking_lab.ipynb, computed from
the reference solution (c2_solution_ref.py) and cross-checked against 07 H.1 / H.3 executed from the lesson text,
the 07 lab-verified numbers (LAB_FACTS.md) and the 06 §2.3 / §5.3 contracts.

Run from rag_learning/ (no API calls, no network, .env never read):
    uv run python sources/verification/C2lab/c2_measure.py > sources/verification/C2lab/out_c2_measure.txt
Exit code 0 iff every [PASS/FAIL] line passes.
"""
import ast
import hashlib
import json
import math
import os
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
from c2_common import run_reference  # noqa: E402
import contracts_check as CC  # noqa: E402  (helpers only; its main() is not run)

FAILS = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


def sec(t):
    print(f"\n== {t} ==")


R = run_reference(str(HERE / "c2_solution_ref.py"))
pages, doc_text, page_starts = R["pages"], R["doc_text"], R["page_starts"]
fwc, rc, cc = R["fixed_window_chunks"], R["recursive_chunks"], R["check_chunks"]
spans = R["_spans"]

md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
core, chunking, _tests = CC.load_07_modules(md07)       # 07 H.1 as ragkit._core, 07 H.3 as ragkit.chunking

import pymupdf  # noqa: E402

sec("M1 environment and Corpus D snapshot")
print(f"python {sys.version.split()[0]} | pymupdf {pymupdf.VersionBind}")
print(f"pages={len(pages)} len(doc_text)={len(doc_text)} SNAPSHOT_ID={R['SNAPSHOT_ID']}")
check("33 pages, 72,593 characters (06 §5.3)", len(pages) == 33 and len(doc_text) == 72593)
check("snapshot_id = ea07572562ac (06 §5.3 recipe)", R["SNAPSHOT_ID"] == "ea07572562ac")
check("page starts p1..p3 = 0, 2425, 4836; p8 16074, p10 20555, p23 49209, p29 62565 (06 §5.3)",
      [page_starts[i] for i in (0, 1, 2, 7, 9, 22, 28)] == [0, 2425, 4836, 16074, 20555, 49209, 62565])
check("07 H.1 join_pages gives the same doc_text and starts", core.join_pages(pages) == (doc_text, page_starts))
empty_pages = [i + 1 for i, p in enumerate(pages) if not p]
print(f"empty pages: {empty_pages}; page lengths min/median/max = "
      f"{min(map(len, pages))}/{statistics.median(map(len, pages))}/{max(map(len, pages))}")

sec("M2 fixed windows (Task 1, Task 2; 07 D.2, C2-A-01, C2-A-02)")
a01 = {k: [(c.char_start, c.char_end, c.text) for c in fwc(R["T"], *k)] for k in ((10, 3), (8, 4), (10, 0))}
for k, v in a01.items():
    print(f"fixed_window_chunks(T, {k[0]}, {k[1]}) = {v}")
check("C2-A-01 (10,3) matches 07 L.2", a01[(10, 3)] == [(0, 10, 'abcdefghij'), (7, 17, 'hijklmnopq'), (14, 23, 'opqrstuvw')])
check("C2-A-01 (8,4) matches 07 L.2", a01[(8, 4)] == [(0, 8, 'abcdefgh'), (4, 12, 'efghijkl'), (8, 16, 'ijklmnop'),
                                                      (12, 20, 'mnopqrst'), (16, 23, 'qrstuvw')])
check("C2-A-02 (10,0) matches 07 L.2", a01[(10, 0)] == [(0, 10, 'abcdefghij'), (10, 20, 'klmnopqrst'), (20, 23, 'uvw')])
SWEEP = [(10, 3), (8, 4), (300, 60), (1000, 200), (7, 6), (5, 0)]
mism = 0
for S, O in SWEEP:
    for L in range(1, 5 * S + 1):
        want = 1 if L <= S else math.ceil((L - O) / (S - O))
        got = len(fwc("x" * L, S, O))
        mism += got != want
        mism += [(c.char_start, c.char_end) for c in fwc("x" * L, S, O)] != \
                [(c.char_start, c.char_end) for c in core.fixed_window_chunks("x" * L, S, O)]
check("count = ceil((L-O)/(S-O)) (L>S), 1 (L<=S), and spans == 07 H.1, for L = 1..5S at 6 settings", mism == 0,
      f"{mism} mismatches")
fd = fwc(doc_text, 1000, 200)
lens = [len(c.text) for c in fd]
print(f"doc_text 1000/200 fixed windows: {len(fd)} chunks; lengths min/median/max {min(lens)}/{statistics.median(lens)}/{max(lens)}; "
      f"last span {(fd[-1].char_start, fd[-1].char_end)}")
check("doc_text fixed 1000/200 = 91 chunks = ceil(72,393/800) (07 D.2 also 91 on PyPDFLoader's 72,523)",
      len(fd) == 91 == math.ceil((72593 - 200) / 800))
for args in (("abc", 10, 10), ("abc", 10, 11), ("abc", 10, -1), ("abc", 0, 0)):
    try:
        fwc(*args)
        print(f"fixed_window_chunks{args}: no error")
    except ValueError as e:
        print(f"fixed_window_chunks{args}: ValueError: {e}")
check("empty text -> []", fwc("", 5, 2) == [] and rc("", 5, 2) == [])
try:
    cc(doc_text, fd, 1000)
    check("check_chunks passes on the fixed windows of doc_text", True)
except AssertionError as e:
    check("check_chunks passes on the fixed windows of doc_text", False, str(e))

sec("M3 boundary math (Task 4; 07 D.3 and Part F)")
pf, pb, cont = R["p_formula"], R["p_brute"], R["chunks_containing"]
fs, fe = R["FACT_SPAN"]
f0 = fwc(R["PARA"], 300, 0)
f60 = fwc(R["PARA"], 300, 60)
print(f"PARA fixed 300/0 spans {spans(f0)} contain FACT: {cont(f0, fs, fe)}")
print(f"PARA fixed 300/60 spans {spans(f60)} contain FACT: {cont(f60, fs, fe)}")
check("Part F: FACT [558,629); O=0 -> []; O=60 -> [2]; spans as 07 Part F",
      (fs, fe) == (558, 629) and cont(f0, fs, fe) == [] and cont(f60, fs, fe) == [2]
      and spans(f0) == [(0, 300), (300, 600), (600, 785)] and spans(f60) == [(0, 300), (240, 540), (480, 780), (720, 785)])
PF = {f"{S},{O},{F}": round(pf(S, O, F), 3) for S, O, F in
      ((1000, 0, 500), (1000, 200, 500), (1000, 400, 500), (1000, 200, 200), (1000, 200, 201), (1000, 200, 202),
       (1000, 200, 250), (300, 60, 71), (300, 0, 71))}
print("p_formula:", PF)
check("p_formula (3 decimals) = 07 D.3 table (0.501, 0.626, 0.835; 1, 1, 0.999, 0.939) and Part F 0.958",
      [PF[k] for k in ("1000,0,500", "1000,200,500", "1000,400,500", "1000,200,200", "1000,200,201",
                       "1000,200,202", "1000,200,250", "300,60,71")] == [0.501, 0.626, 0.835, 1.0, 1.0, 0.999, 0.939, 0.958])
PB = {O: round(pb(20000, 1000, O, 500), 4) for O in (0, 200, 400)}
print("p_brute(L=20000, S=1000, F=500):", PB)
check("p_brute whole doc L=20,000 = 0.5138 / 0.6320 / 0.8375 (07 D.3 last column)", PB == {0: 0.5138, 200: 0.632, 400: 0.8375})
PG = {F: pb(20000, 1000, 200, F) for F in (200, 201, 202)}
print("p_brute(20000, 1000, 200, F) for F = 200, 201, 202:", PG)
check("guarantee threshold at S=1000, O=200 is F = 201 = O + 1 (brute force: 1, 1, < 1)",
      PG[200] == 1.0 and PG[201] == 1.0 and PG[202] < 1.0)
# boundary guard: formula values are fingerprinted at 3 decimals, brute-force values at 4 decimals
for S, O, F in ((1000, 0, 500), (1000, 200, 500), (1000, 400, 500), (1000, 200, 202), (1000, 200, 250), (300, 60, 71), (300, 0, 71)):
    v = pf(S, O, F)
    assert abs((v * 1e3) % 1 - 0.5) > 1e-6, f"{S},{O},{F} too close to a 3-decimal rounding boundary"
for O in (0, 200, 400):
    v = pb(20000, 1000, O, 500)
    assert abs((v * 1e4) % 1 - 0.5) > 1e-6, f"p_brute O={O} too close to a rounding boundary"
print("rounding guard: no fingerprinted value is within 1e-6 of its rounding boundary (formula 3 dp, brute force 4 dp)")

sec("M4 recursive splitter (Task 5; 07 D.4, H.1, C2-A-03, Part F step 3)")
W = R["W"]
pieces = R["split_spans"](W, 0, len(W), R["SEPARATORS"], 10)
print(f"split_spans(W, 0, 22, SEPARATORS, 10) = {pieces}")
check("C2-A-03 pieces", pieces == [(0, 4), (4, 8), (8, 12), (12, 15), (15, 19), (19, 22)])
rw = rc(W, 10, 4)
print(f"recursive_chunks(W, 10, 4) = {[(c.char_start, c.char_end, c.text) for c in rw]}")
check("C2-A-03 result [(0,8),(4,12),(8,15),(12,22)]", spans(rw) == [(0, 8), (4, 12), (8, 15), (12, 22)])
rp = rc(R["PARA"], 300, 60)
print(f"recursive_chunks(PARA, 300, 60) spans {spans(rp)}; FACT in {cont(rp, fs, fe)}")
check("Part F step 3: [0,294) [238,534) [478,773) [714,785); FACT in chunk 2",
      spans(rp) == [(0, 294), (238, 534), (478, 773), (714, 785)] and cont(rp, fs, fe) == [2])
LW = "short " + "x" * 25 + " tail"
rl = rc(LW, 10, 0)
print(f"recursive_chunks('short ' + 'x'*25 + ' tail', 10, 0) = {[(c.char_start, c.char_end, c.text) for c in rl]}")
check("long word falls back to single characters ('' separator) and matches 07 H.1",
      spans(rl) == spans(core.recursive_chunks(LW, 10, 0)))
print(f"STATIC+run: ''.find on a real text returns the start: 'abc'.find('', 1, 3) = {'abc'.find('', 1, 3)} "
      "-> a split loop on '' never advances (why '' must mean 'single characters')")
rd = rc(doc_text, 1000, 200)
n_cross = sum(core.page_of(c.char_start, page_starts) != core.page_of(c.char_end - 1, page_starts) for c in rd)
print(f"recursive_chunks(doc_text, 1000, 200): {len(rd)} chunks; {n_cross} span a page break")
check("whole-document recursive 1000/200 = 92 chunks (07 H.1: 92 on PyPDFLoader text) and == 07 H.1 spans",
      len(rd) == 92 and spans(rd) == spans(core.recursive_chunks(doc_text, 1000, 200)))
cc(doc_text, rd, 1000)
# random equivalence sweep: 06 separators (with "") vs 07 H.1 default separators (without "")
rng = random.Random(0)
words = "alpha beta gamma delta\n\nepsilon zeta\neta theta iota supercalifragilistic".split(" ")
bad = 0
for _ in range(300):
    txt = " ".join(rng.choice(words) for _ in range(rng.randint(0, 120)))
    size = rng.randint(2, 150)
    ov = rng.randint(0, size - 1)
    a = spans(rc(txt, size, ov))
    bad += a != spans(core.recursive_chunks(txt, size, ov))
    if txt:
        cc(txt, rc(txt, size, ov), size)
check("300 random (text, size, overlap): separators ['\\n\\n','\\n',' ',''] give exactly 07 H.1's spans; check_chunks passes",
      bad == 0, f"{bad} differ")

sec("M5 per-page scope (Task 6; 07 D.8)")
cp = R["chunk_pages"](pages, 1000, 200)
lens = [b - a for a, b, _ in cp]
per_page = {}
for a, b, p in cp:
    per_page[p] = per_page.get(p, 0) + 1
print(f"chunk_pages(pages, 1000, 200): {len(cp)} chunks; lengths min/median/max {min(lens)}/{statistics.median(lens)}/{max(lens)}")
print(f"chunks per page: {per_page}")
check("per-page 1000/200 = 97 chunks (07 D.8: 97 with PyPDFLoader; now verified for PyMuPDF)", len(cp) == 97)
check("no per-page chunk crosses a page and every span round-trips to its page text",
      all(page_starts[p - 1] <= a < b <= page_starts[p - 1] + len(pages[p - 1])
          and doc_text[a:b] == pages[p - 1][a - page_starts[p - 1]:b - page_starts[p - 1]] for a, b, p in cp))
h3 = chunking.chunk_document("climate", R["SNAPSHOT_ID"], pages,
                             chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))
check("per-page spans == 07 H.3 chunk_document(scope=per_page) spans", [(a, b) for a, b, _ in cp] == [(c.char_start, c.char_end) for c in h3])
print(f"07 H.3 params_hash (its ChunkerConfig recipe) = {h3[0].params_hash}; first id {h3[0].chunk_id}")
print(f"07 D.8 PyPDFLoader per-page lengths were 391 / 933 / 999; PyMuPDF gives {min(lens)} / {statistics.median(lens)} / {max(lens)}")
pagerel_bug = sum(doc_text[a - page_starts[p - 1]:b - page_starts[p - 1]] == doc_text[a:b] for a, b, p in cp)
print(f"C2-A-05 trap: page-relative offsets read against doc_text match on {pagerel_bug} of {len(cp)} chunks "
      f"(page-1 chunks: {per_page[1]})")

sec("M6 chunk records (Task 7; 06 §2.3, §3.1, §5.3)")
recs = R["records"]
PH = R["params_hash"](R["PARAMS"])
pjson = json.dumps(R["PARAMS"], sort_keys=True)
print(f"PARAMS canonical JSON: {pjson}")
print(f"params_hash = sha256(that, utf-8)[:12] = {PH}")
t06 = ast.parse(CC.code_blocks(CC.section(md06, "2.3 Provider-agnostic"), "python")[0])
f06 = next([s.target.id for s in n.body if isinstance(s, ast.AnnAssign)] for n in t06.body
           if isinstance(n, ast.ClassDef) and n.name == "Chunk")
seg06 = next([s.target.id for s in n.body if isinstance(s, ast.AnnAssign)] for n in t06.body
             if isinstance(n, ast.ClassDef) and n.name == "PageSegment")
print(f"06 §2.3 Chunk fields: {f06}; PageSegment fields: {seg06}")
check("record keys == 06 §2.3 Chunk fields, in order", all(list(r) == f06 for r in recs))
check("page_segments dict keys == 06 §2.3 PageSegment fields", all(list(s) == seg06 for r in recs for s in r["page_segments"]))
check("chunker == 06 §2.4 chunking.name 'recursive_char'", all(r["chunker"] == "recursive_char" for r in recs))
check("text == doc_text[char_start:char_end] for all 97", all(doc_text[r["char_start"]:r["char_end"]] == r["text"] for r in recs))
check("text_sha256 = sha256(text utf-8)", all(r["text_sha256"] == hashlib.sha256(r["text"].encode()).hexdigest() for r in recs))
check("exactly one page segment per record; it converts back to the doc range (07 H.3 to_page_segments agrees)",
      all(len(r["page_segments"]) == 1 and [(s.page, s.char_start, s.char_end) for s in
          chunking.to_page_segments(r["char_start"], r["char_end"], page_starts, len(doc_text))] ==
          [(s["page"], s["char_start"], s["char_end"]) for s in r["page_segments"]] for r in recs))
check("chunk_id = doc_id:snapshot_id:params_hash:seq05d, seq 0..96", all(
    r["chunk_id"] == f"climate:ea07572562ac:{PH}:{i:05d}" and r["seq"] == i for i, r in enumerate(recs)))
again = R["make_records"]("climate", R["SNAPSHOT_ID"], pages, R["PARAMS"])
check("two calls give identical records (deterministic)", again == recs)
p2 = dict(R["PARAMS"], chunk_overlap=199)
check("changing chunk_overlap changes params_hash and every chunk_id",
      R["params_hash"](p2) != PH and not ({r["chunk_id"] for r in R["make_records"]("climate", R["SNAPSHOT_ID"], pages, p2)}
                                          & {r["chunk_id"] for r in recs}))
check("records' (seq, spans, text) == 07 H.3 per_page DocChunks (only params_hash/chunker differ)",
      [(r["seq"], r["char_start"], r["char_end"], r["text"], r["text_sha256"]) for r in recs] ==
      [(c.seq, c.char_start, c.char_end, c.text, c.text_sha256) for c in h3])
import dataclasses  # noqa: E402
alt = {
    "07 H.3 ChunkerConfig(name='recursive', 1000, 200) [3 separators, contracts_check]":
        chunking.ChunkerConfig(name="recursive", size=1000, overlap=200).params_hash(),
    "07 H.3 ChunkerConfig(name='recursive', 1000, 200, separators + '')":
        chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, separators=("\n\n", "\n", " ", "")).params_hash(),
    "07 H.3 ChunkerConfig(name='recursive_char', 1000, 200, separators + '')":
        chunking.ChunkerConfig(name="recursive_char", size=1000, overlap=200, separators=("\n\n", "\n", " ", "")).params_hash(),
    "07 H.3 ChunkerConfig(name='fixed', 1000, 200)": chunking.ChunkerConfig(name="fixed", size=1000, overlap=200).params_hash(),
    "this lab: 06 §2.4 chunking block (chunk_size/chunk_overlap keys)": PH,
}
print("params_hash under the candidate recipes (same sha256(json.dumps(..., sort_keys=True))[:12], different inputs):")
for k, v in alt.items():
    print(f"  {v}  {k}")
check("same recipe as 07 H.3 when fed 07's own config dict", R["params_hash"](dataclasses.asdict(
    chunking.ChunkerConfig(name="recursive", size=1000, overlap=200))) == alt[next(iter(alt))])
KEYS = f06
jsonl = "".join(json.dumps({k: r[k] for k in KEYS}, ensure_ascii=False) + "\n" for r in recs).encode("utf-8")
print(f"first record (text shortened): {json.dumps({**recs[0], 'text': recs[0]['text'][:40] + '...'}, ensure_ascii=False)}")
print(f"last chunk_id {recs[-1]['chunk_id']}; last span [{recs[-1]['char_start']},{recs[-1]['char_end']}) page {recs[-1]['page_segments'][0]['page']}")
print(f"chunks.jsonl: {len(recs)} lines, {len(jsonl)} bytes, sha256 {hashlib.sha256(jsonl).hexdigest()}")
print(f"_fp(records) = {R['_fp'](recs)}")

sec("M7 achieved overlap (Task 8; 07 D.4, H.2, L.6 Intermediate)")
ao = R["achieved_overlaps"](recs)
print(f"{len(ao)} same-page consecutive pairs; achieved overlap min/median/max = {min(ao)}/{statistics.median(ao)}/{max(ao)}; "
      f"exactly 200: {sum(x == 200 for x in ao)}; mean {statistics.mean(ao):.1f}")
check("all achieved overlaps in [0, 200]; pairs = 97 - 33 pages", all(0 <= x <= 200 for x in ao) and len(ao) == 97 - 33)
print(f"07 H.2 (LangChain, PyPDFLoader) first overlaps were 180, 140, 197, 177 (whitespace stripped); ours start {ao[:4]}")

print(f"\n== SUMMARY: {'ALL PASS' if not FAILS else 'FAILURES: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
