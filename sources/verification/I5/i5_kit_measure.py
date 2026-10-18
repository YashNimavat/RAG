"""I5 study-kit measurements (K1-K16): the numbers the I5 HTML lesson, reading file, questions, verify notebook and
apply-it tool rely on. Sections K1..K16 of out_i5_kit_measure.txt (I5_FACTS.md section 1).

Corpus D, v0's 97 chunks (07 recursive chunker, per page, 1000/200), rebuilt exactly as P4's kit script does, and
the draft seeds of 06 section 6.7 (LLM-drafted, not human-verified: every rank below is an observation on draft
seeds, never an evaluation result).

Local only: no Groq, Cohere or Claude call, no .env read, no network.
- K1-K15 need only pymupdf, numpy and rank_bm25. They run anywhere.
- K16 (MiniLM) runs only when sentence-transformers/all-MiniLM-L6-v2 is in the local Hugging Face cache. Otherwise
  it prints "SKIPPED" and the rest of the output is unchanged.
Token counts are not measured here (no tokenizer files are loaded): every token figure is DERIVED from the
measured characters-per-token ratios in C2_FACTS K2 (WordPiece 6.21) and P1_FACTS K5 (o200k_harmony 5.65), and is
labelled so. The verify notebook counts them exactly.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I5/i5_kit_measure.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        "<Book RAG>/upstream/RAG_Techniques/all_rag_techniques/contextual_chunk_headers.ipynb" \
        > sources/verification/I5/out_i5_kit_measure.txt
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import collections
import hashlib
import importlib.metadata as md
import json
import math
import re
import statistics
import sys
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
from rank_bm25 import BM25Okapi

PDF = Path(sys.argv[1])
NB = Path(sys.argv[2]) if len(sys.argv) > 2 else None
HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
L6 = "sentence-transformers/all-MiniLM-L6-v2"
WP_CPT = 6.21          # WordPiece characters per token on Corpus D (C2_FACTS K2, measured)
O200_CPT = 5.65        # o200k_harmony characters per token on Corpus D (P1_FACTS K5, measured)
O200_DOC = 12840       # o200k_harmony tokens in the whole PDF text (P1_FACTS K5, measured)
SEP = "\n\n"           # header / chunk separator in embed_text


def head(t):
    print(f"\n=== {t}")


def f4(x):
    return f"{x:.4f}"


def wp(chars):
    """DERIVED WordPiece token estimate from characters (C2 K2 ratio)."""
    return round(chars / WP_CPT)


# ---------------------------------------------------------------- the 97 chunks and the draft seeds (as P4 kit)
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402

pdf_bytes = PDF.read_bytes()
doc = pymupdf.open(PDF)
pages = [p.get_text() for p in doc]
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
manifest06 = cc.build_manifest("climate", pages, pdf_bytes, {**cc.PARSER, "version": pymupdf.VersionBind}, cc.CLEANING_NONE)
SNAP = manifest06["snapshot_id"]
starts = [r["doc_char_start"] for r in manifest06["docs"][0]["page_table"]]
_core, chunking, _ = cc.load_07_modules(md07)
dch = chunking.chunk_document("climate", SNAP, pages,
                              chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
chunks = [{"doc_id": "climate", "snapshot_id": SNAP, "chunk_id": f"climate:{SNAP}:{PH}:{c.seq:05d}", "seq": c.seq,
           "char_start": c.char_start, "char_end": c.char_end,
           "page_segments": [{"page": g.page, "char_start": g.char_start, "char_end": g.char_end} for g in c.page_segments],
           "text": c.text, "text_sha256": c.text_sha256, "chunker": CHUNKING["name"], "params_hash": PH, "meta": {}}
          for c in dch]
SHA_JL = hashlib.sha256("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")).hexdigest()
DOC = "\n".join(pages)
TEXTS = {"climate": DOC}
N = len(chunks)
PAGE = [c["page_segments"][0]["page"] for c in chunks]
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]), s["G"], TEXTS)]
       for s in ANS}


def order(scores):
    """chunk seqs best first; ties broken by the smaller seq (the course rule)."""
    s = np.asarray(scores, float)
    return sorted(range(len(s)), key=lambda i: (-s[i], i))


def first_rel(ranking, qid):
    return next((r for r, i in enumerate(ranking, 1) if i in REL[qid]), None)


def ce_at(ranking, qid, k=4):
    top = [("climate", chunks[i]["char_start"], chunks[i]["char_end"]) for i in ranking[:k]]
    return cc.ce(BYQ[qid]["G"], top, TEXTS)


def summary(ranks, ces, k=4):
    hitk = sum(r is not None and r <= k for r in ranks)
    mrr = sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks)
    return hitk, sum(ces), round(mrr, 3)


# ---------------------------------------------------------------- the heading tree (font size + bold)
LEVEL_BY_SIZE = {24.0: 0, 18.0: 1, 13.56: 2}          # title, chapter, section; 12 pt bold = subsection (3)
LEVEL_NAME = ["title", "chapter", "section", "subsection"]


def heading_level(span):
    size = round(span["size"], 2)
    bold = bool(span["flags"] & 16)
    if size in LEVEL_BY_SIZE and bold:
        return LEVEL_BY_SIZE[size]
    if size == 12.0 and bold:
        return 3
    return None


def extract_headings():
    """[(level, text, page, doc_start, doc_end)] in reading order. A heading that wraps over two lines of one block
    (Chapter 5) is merged. Offsets are located in the same page.get_text() string the chunks are cut from."""
    out = []
    for pno, page in enumerate(doc, 1):
        found = []
        for b in page.get_text("dict")["blocks"]:
            prev = None
            for ln in b.get("lines", []):
                sp = [s for s in ln["spans"] if s["text"].strip()]
                if not sp:
                    continue
                lv = {heading_level(s) for s in sp}
                if len(lv) != 1 or None in lv:
                    prev = None
                    continue
                lv = lv.pop()
                txt = "".join(s["text"] for s in sp).strip()
                if prev is not None and prev[0] == lv and lv == 1:
                    found[-1] = (lv, found[-1][1] + [txt])
                else:
                    found.append((lv, [txt]))
                prev = (lv,)
        cur = 0
        ptxt = pages[pno - 1]
        for lv, parts in found:
            a = ptxt.find(parts[0], cur)
            assert a >= 0, (pno, parts)
            e = a
            for p in parts:
                e = ptxt.find(p, e)
                assert e >= 0, (pno, p)
                e += len(p)
            cur = e
            out.append((lv, " ".join(parts), pno, starts[pno - 1] + a, starts[pno - 1] + e))
    return out


H = extract_headings()
TITLE = next(h[1] for h in H if h[0] == 0)


def path_at(pos):
    """the heading path in effect at document offset pos: the last heading of each level that starts at or before
    pos, deeper levels reset when a shallower heading starts."""
    path = [None, None, None, None]
    for lv, txt, _p, a, _e in H:
        if a > pos:
            break
        path[lv] = txt
        for d in range(lv + 1, 4):
            path[d] = None
    return tuple(path)


def first_nonspace(c):
    t = c["text"]
    k = len(t) - len(t.lstrip())
    return c["char_start"] + k


def inside(c):
    return [h for h in H if c["char_start"] <= h[3] < c["char_end"]]


def path_majority(c):
    votes = collections.Counter()
    for i in range(c["char_start"], c["char_end"]):
        if not DOC[i].isspace():
            votes[path_at(i)] += 1
    return max(votes.items(), key=lambda kv: (kv[1], kv[0] is not None))[0] if votes else path_at(c["char_start"])


def fmt_path(p, with_title=True):
    parts = [x for x in (p if with_title else p[1:]) if x]
    return " › ".join(parts)


def fmt_path_with_extra(p, extra):
    parts = [x for x in p if x]
    for lv, txt in extra:
        parts.append(txt)
    return " › ".join(parts)


START = [path_at(first_nonspace(c)) for c in chunks]
MAJ = [path_majority(c) for c in chunks]
HDR = {
    "none": ["" for _ in chunks],
    "title": [TITLE for _ in chunks],
    "path": [fmt_path(p) for p in START],
    "major": [fmt_path(p) for p in MAJ],
}
EMBED = {arm: [(h + SEP + c["text"]) if h else c["text"] for h, c in zip(HDR[arm], chunks)] for arm in HDR}

# ---------------------------------------------------------------- K1
head("K1 environment, corpus, chunks")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "numpy", "rank-bm25")})
print("pdf sha256", hashlib.sha256(pdf_bytes).hexdigest())
print(f"pages={len(pages)} doc_chars={len(DOC)} snapshot_id={SNAP}")
print(f"chunks={N} params_hash={PH} chunks.jsonl sha256={SHA_JL[:16]}")
assert all(DOC[c["char_start"]:c["char_end"]] == c["text"] for c in chunks)
print("span invariant DOC[char_start:char_end] == text: OK for all", N)
lens = [len(c["text"]) for c in chunks]
print(f"chunk chars min/median/max {min(lens)}/{int(statistics.median(lens))}/{max(lens)}")
print("relevant chunks (any_overlap) per answerable seed:", {q: r for q, r in REL.items()})

# ---------------------------------------------------------------- K2
head("K2 heading tree from font size + bold (PyMuPDF get_text('dict'))")
print("PDF metadata title:", repr(doc.metadata.get("title")))
cls = collections.Counter()
for page in doc:
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if sp:
                cls[tuple(sorted({(round(s["size"], 2), bool(s["flags"] & 16)) for s in sp}))] += 1
for k, v in sorted(cls.items(), key=lambda kv: -kv[1]):
    print(f"  lines {v:4d}  (size, bold) {k}")
cnt = collections.Counter(h[0] for h in H)
print("headings by level:", {LEVEL_NAME[k]: cnt[k] for k in sorted(cnt)}, "total", len(H))
print("title:", repr(TITLE), len(TITLE), "chars")
ch = [h for h in H if h[0] == 1]
print("chapters:", len(ch), "| merged two-line chapter:", [h[1] for h in ch if h[2] == next(x[2] for x in ch if x[1].startswith("Chapter 5"))][:1])
per_page = collections.Counter(h[2] for h in H if h[0] >= 1)
pp = [per_page.get(p, 0) for p in range(1, len(pages) + 1)]
print(f"headings (levels 1-3) per page min/median/max {min(pp)}/{statistics.median(pp)}/{max(pp)}; "
      f"pages with >= 1: {sum(x > 0 for x in pp)} of {len(pages)}")
print(f"one heading every {len(DOC) / len(H):.0f} characters on average ({len(H)} headings, {len(DOC)} chars)")
sub_bold_share = cnt[3] / (len(H) - cnt[0])
print(f"12 pt bold subsections as a share of chapter+section+subsection headings: {cnt[3]}/{len(H) - cnt[0]} = {sub_bold_share:.2f}"
      " (a size-only detector that needs size > body misses these)")

# ---------------------------------------------------------------- K3
head("K3 reused heading names under different chapters, and the two Paris paths")
by_name = collections.defaultdict(list)
cur = [None] * 4
for lv, txt, p, a, e in H:
    cur[lv] = txt
    for d in range(lv + 1, 4):
        cur[d] = None
    if lv >= 2:
        by_name[txt].append((p, cur[1]))
reused = {n: v for n, v in by_name.items() if len({c for _p, c in v}) > 1}
print("names reused under different chapters:", len(reused))
for n, v in sorted(reused.items(), key=lambda kv: kv[1][0][0]):
    print(f"  {n!r}: " + "; ".join(f"p.{p} {c.split(':')[0]}" for p, c in v))
paris = [h for h in H if h[1] == "Paris Agreement"]
for h in paris:
    print(f"  Paris Agreement heading p.{h[2]} path: {fmt_path(path_at(h[3]))}")
leaves = [fmt_path(path_at(h[3])) for h in H if h[0] >= 2]
lp = [len(x) for x in leaves]
print(f"path header length over {len(lp)} section/subsection headings, chars min/median/max {min(lp)}/{int(statistics.median(lp))}/{max(lp)}"
      f" = about {wp(min(lp))}/{wp(statistics.median(lp))}/{wp(max(lp))} WordPiece tokens (DERIVED, {WP_CPT} chars/token)")

# ---------------------------------------------------------------- K4
head("K4 which heading a chunk gets: path at the chunk start vs majority vs all headings inside")
no_head = [i for i, c in enumerate(chunks) if not inside(c)]
starts_with_head = [i for i, c in enumerate(chunks) if any(h[3] == first_nonspace(c) for h in H)]
diff = [i for i in range(N) if START[i] != MAJ[i]]
print(f"chunks with no heading line inside: {len(no_head)} of {N}: {no_head}")
print(f"chunks whose first non-space character starts a heading: {len(starts_with_head)} of {N}")
print(f"chunks where start-rule path != majority-rule path: {len(diff)} of {N}: {diff}")
multi = [i for i, c in enumerate(chunks) if len(inside(c)) >= 2]
print(f"chunks containing >= 2 headings: {len(multi)} of {N}")
orphan = []
for i, c in enumerate(chunks):
    if any(h[4] <= c["char_end"] and not DOC[h[4]:c["char_end"]].strip() for h in inside(c)):
        orphan.append(i)
print(f"chunks whose last non-empty line is a heading (orphaned heading, its body is in the next chunk): {len(orphan)} of {N}: {orphan}")
page_end = [i for i in orphan if i == N - 1 or PAGE[i + 1] != PAGE[i]]
print(f"  of which at a page end (07 D.8 counts 16 page-end orphans): {len(page_end)}: {page_end}")
for i in [j for j in range(N) if PAGE[j] == 10] + [34, 68]:
    c = chunks[i]
    print(f"  chunk {i} p.{PAGE[i]} [{c['char_start']},{c['char_end']}) start: {fmt_path(START[i], False)}")
    print(f"           majority: {fmt_path(MAJ[i], False)}")
    print(f"           inside: {[h[1] for h in inside(c)]}")
ALL_IN = [fmt_path(START[i]) + "".join(f" | {h[1]}" for h in inside(c) if h[3] > first_nonspace(c))
          for i, c in enumerate(chunks)]
MAJ_H = [fmt_path(p) for p in MAJ]
for name, hs in (("start", HDR_START := [fmt_path(p) for p in START]), ("majority", MAJ_H), ("all-inside", ALL_IN)):
    L = [len(h) for h in hs]
    est = [wp(len(h) + 2 + len(c["text"])) + 2 for h, c in zip(hs, chunks)]
    print(f"  rule {name:10s}: header chars min/median/max {min(L)}/{int(statistics.median(L))}/{max(L)};"
          f" distinct {len(set(hs))}; header+chunk over 256 (DERIVED) {sum(x > 256 for x in est)}")
for q, i in (("D-002", 27), ("D-003", 68)):
    print(f"  {q} gold chunk {i}: start -> {START[i][1]} | majority -> {MAJ[i][1]} › {MAJ[i][2]} › {MAJ[i][3]}")

# ---------------------------------------------------------------- K5
head("K5 header arms: distinct headers, the header magnet, lengths")
for arm in ("none", "title", "path", "major"):
    hs = HDR[arm]
    distinct = len(set(hs))
    top = collections.Counter(hs).most_common(1)[0]
    L = [len(h) for h in hs]
    print(f"  {arm:6s} distinct headers {distinct:3d} / {N} | largest group sharing one header {top[1]:3d} "
          f"({top[1] / N:.2f}) | header chars min/median/max {min(L)}/{int(statistics.median(L))}/{max(L)}")
grp = collections.Counter(HDR["path"])
print("  path arm, the 3 largest groups:", [(g.split(' › ')[-1], n) for g, n in grp.most_common(3)])
print("  path arm, header used by exactly 1 chunk:", sum(1 for n in grp.values() if n == 1))
leaf_only = [p[3] or p[2] or p[1] or "" for p in START]
print("  leaf-only arm distinct:", len(set(leaf_only)), "/", N)
ex = 34 if N > 34 else 0
print(f"  example embed_text (path arm, chunk {ex}):")
print("   ", repr(EMBED["path"][ex][:200]))

# ---------------------------------------------------------------- K6
head("K6 dilution s = h/(h+c) and truncation at 256 (DERIVED token estimates)")
hc = [len(h) for h in HDR["path"]]
s_chars = [h / (h + len(c["text"])) for h, c in zip(hc, chunks)]
print(f"  path arm, header share by characters: min/median/max {min(s_chars):.3f}/{statistics.median(s_chars):.3f}/{max(s_chars):.3f}")
for hchars, cchars in ((120, 1000), (120, 935), (120, 400)):
    h_t, c_t = wp(hchars), wp(cchars)
    print(f"  header {hchars} chars (~{h_t} tok) + chunk {cchars} chars (~{c_t} tok): s = {h_t / (h_t + c_t):.3f}")
print("  truncation examples (MiniLM max_seq_length 256 incl. [CLS]/[SEP]; chunk max 182 tokens incl. specials, C2 K2):")
for extra in (wp(max(hc)), 27, 100):
    tot = 182 + extra
    print(f"    182 + {extra:3d} = {tot} -> {'fits' if tot <= 256 else f'over by {tot - 256}: the chunk TAIL is cut'}")
est = [wp(len(e)) + 2 for e in EMBED["path"]]
print(f"  path arm embed_text estimate over 256: {sum(x > 256 for x in est)} of {N} (DERIVED; max est {max(est)})")
est100 = [wp(len(c['text'])) + 2 + 100 for c in chunks]
print(f"  a 100-token LLM context + chunk over 256: about {sum(x > 256 for x in est100)} of {N} (DERIVED)")

# ---------------------------------------------------------------- K7
head("K7 the near-duplicate pages: chunks on p.6, 10, 23, 24 and the seeds D-002 / D-003")
for p in (6, 10, 23, 24):
    for i in [j for j in range(N) if PAGE[j] == p]:
        has = "Paris" in chunks[i]["text"]
        print(f"  chunk {i:2d} p.{p:2d} paris={'Y' if has else '-'} path: {fmt_path(START[i], False)}")
for q in ("D-002", "D-003", "D-004", "D-006"):
    print(f"  {q} relevant chunks {REL[q]} -> paths {[fmt_path(START[i], False) for i in REL[q]]}")

# ---------------------------------------------------------------- K8
head("K8 header-query leakage on the draft seeds (question content words in the gold chunk's header, not in its text)")
STOP = set("a an and are as at be by does did do for from how in is it of on or the this that to was what which who why with "
           "according document regarding countries".split())
WRE = re.compile(r"[a-z0-9]+")
for s in ANS:
    q = {w for w in WRE.findall(s["question"].lower()) if w not in STOP and len(w) > 2}
    for i in REL[s["qid"]][:1]:
        htoks = set(WRE.findall(HDR["path"][i].lower()))
        ttoks = set(WRE.findall(chunks[i]["text"].lower()))
        only_h = sorted(q & htoks - ttoks)
        both = sorted(q & htoks & ttoks)
        print(f"  {s['qid']} chunk {i:2d}: header-only {only_h} | in header and text {both}")

# ---------------------------------------------------------------- K9
head("K9 'anonymous' chunks: no heading inside and the first word is a pronoun or determiner")
PRON = {"it", "its", "this", "these", "they", "their", "such", "those", "that", "he", "she", "the"}
anon = []
for i in no_head:
    w = WRE.findall(chunks[i]["text"].lower()[:40])
    if w and w[0] in PRON:
        anon.append((i, chunks[i]["text"].strip()[:60]))
print(f"  {len(anon)} of {N}:")
for i, t in anon:
    print(f"   chunk {i} p.{PAGE[i]}: {t!r}")
cut_start = [i for i, c in enumerate(chunks) if c["text"].lstrip()[:1].islower()]
print(f"  chunks that start mid-sentence (first character lower-case): {len(cut_start)} of {N}")

# ---------------------------------------------------------------- K10
head("K10 BM25 preview (v2.0 field, not v1.2): the same three header arms in an inverted index")
NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")


def tok(t):
    return NORM_RE.findall(t.lower())


for arm in ("none", "title", "path", "major"):
    C = [tok(e) for e in EMBED[arm]]
    bm = BM25Okapi(C)
    ranks, ces = [], []
    for s in ANS:
        r = order(bm.get_scores(tok(s["question"])))
        ranks.append(first_rel(r, s["qid"]))
        ces.append(ce_at(r, s["qid"]))
    hk, c4, mrr = summary(ranks, ces)
    print(f"  {arm:6s} first relevant rank {dict(zip([s['qid'] for s in ANS], ranks))} | Hit@4 {hk}/8 CE@4 {c4}/8 MRR@10 {mrr}")
    if arm == "title":
        for w in tok(TITLE):
            print(f"     idf[{w}] = {bm.idf[w]:.4f} (floor = 0.25 x average_idf = {0.25 * bm.average_idf:.4f})"
                  f" | df = {sum(w in set(c) for c in C)} of {N}")

# ---------------------------------------------------------------- K11
head("K11 cost ladder (DERIVED arithmetic; prices from study/tools/examples/prices_2026-10-17.json)")
prices = json.loads((WS / "study" / "tools" / "examples" / "prices_2026-10-17.json").read_text(encoding="utf-8"))
g = prices["models"]["groq:openai/gpt-oss-20b"]
hk5 = prices["models"]["anthropic:claude-haiku-5-5"]
tpm = prices["rate_limits"]["groq:openai/gpt-oss-20b"]["tpm"]
tpd = prices["rate_limits"]["groq:openai/gpt-oss-20b"]["tpd"]
P_TOK, O_TOK = 250, 200        # chunk + instruction tokens per call; output incl. reasoning (research assumptions)
chap_bounds = [h[3] for h in H if h[0] == 1] + [len(DOC)]
chap_len = [b - a for a, b in zip(chap_bounds, chap_bounds[1:])]
print(f"  doc tokens (o200k_harmony, P1 K5 measured) {O200_DOC}; chapters {len(chap_len)}, chars min/median/max "
      f"{min(chap_len)}/{int(statistics.median(chap_len))}/{max(chap_len)}")


def chapter_of(i):
    pos = first_nonspace(chunks[i])
    k = max(j for j, a in enumerate(chap_bounds[:-1]) if a <= pos) if pos >= chap_bounds[0] else 0
    return k


win_tok = [round(chap_len[chapter_of(i)] / O200_CPT) for i in range(N)]
in2 = [w + P_TOK for w in win_tok]
cost2 = sum(x * g["input"] + O_TOK * g["output"] for x in in2) / 1e6
tok2 = sum(in2) + N * O_TOK
print(f"  rung 2 (chapter window, Groq): input tokens per call median {int(statistics.median(in2))}, max {max(in2)};"
      f" total tokens {tok2} (incl. output); USD {cost2:.4f}; fits TPD {tpd}: {tok2 <= tpd};"
      f" minutes at {tpm} TPM >= {tok2 / tpm:.1f}")
in3 = O200_DOC + P_TOK
print(f"  rung 3 (whole document) input tokens per call {in3}; Groq free tier TPM {tpm}: per-request too large = {in3 > tpm};"
      f" 97 calls = {N * in3} input tokens vs TPD {tpd}")
w_mult, r_mult = 1.25, 0.10
c_unc = (N * in3 * hk5["input"] + N * O_TOK * hk5["output"]) / 1e6
c_cache = (O200_DOC * hk5["input"] * w_mult + (N - 1) * O200_DOC * hk5["input"] * r_mult
           + N * P_TOK * hk5["input"] + N * O_TOK * hk5["output"]) / 1e6
print(f"  rung 3 Haiku 5.5: uncached USD {c_unc:.4f}; cached (write 1.25x once, read 0.1x) USD {c_cache:.4f};"
      f" ratio {c_unc / c_cache:.1f}x")
c_groq_cached = (O200_DOC * g["input"] + (N - 1) * O200_DOC * g["cached_input"] + N * P_TOK * g["input"]
                 + N * O_TOK * g["output"]) / 1e6
print(f"  rung 3 on a paid Groq tier with 50% cached input: USD {c_groq_cached:.4f} (rate limits aside)")
print(f"  rung 0 (path header): 0 LLM calls; rung 1 (title/summary per document): 1-2 calls, not needed on D"
      f" (the title is the 24 pt line)")
print("  general formula: cost_d = D*p_in*w + (n-1)*D*p_in*rho + n*(c+P)*p_in + n*o*p_out")

# ---------------------------------------------------------------- K12
head("K12 cache keys after an edit on page 12 (whole-document prompt)")
edited_pages = list(pages)
edited_pages[11] = pages[11].replace("\n", " (revised)\n", 1)
EDOC = "\n".join(edited_pages)
edch = chunking.chunk_document("climate", "edited", edited_pages,
                               chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))
assert len(edch) == N
sha = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
k_chunk = [sha(c["text"]) for c in chunks]
k_chunk_e = [sha(c.text) for c in edch]
k_full = [sha("i5_context_wholedoc_v1|" + DOC + "|" + c["text"]) for c in chunks]
k_full_e = [sha("i5_context_wholedoc_v1|" + EDOC + "|" + c.text) for c in edch]
same_chunk = sum(a == b for a, b in zip(k_chunk, k_chunk_e))
same_full = sum(a == b for a, b in zip(k_full, k_full_e))
p12 = [i for i in range(N) if PAGE[i] == 12]
print(f"  edit: ' (revised)' appended to the first line of page 12; changed chunks: "
      f"{[i for i in range(N) if k_chunk[i] != k_chunk_e[i]]} (page-12 chunks: {p12})")
print(f"  chunk-text-hash key: {same_chunk} of {N} served from cache (stale: their prompt held the old document)")
print(f"  key over prompt version + document text + chunk: {same_full} of {N} served from cache (all rebuilt)")
print(f"  doc_text_sha256 before {sha(DOC)[:12]} after {sha(EDOC)[:12]}")

# ---------------------------------------------------------------- K13
head("K13 toy: mean pooling with a shared header (d=64, seed 0; token = unit(topic + noise), cos(token, topic) ~ 0.5)")
rng = np.random.default_rng(0)
d = 64


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def tokens(topic, n):
    return unit(topic[None] + 1.7 * rng.normal(size=(n, d)) / math.sqrt(d))


tA, tB, tH = (unit(rng.normal(size=d)) for _ in range(3))
A, B, Hd = tokens(tA, 150), tokens(tB, 150), tokens(tH, 100)
print(f"  mean cos(token, its topic) {f4(float((A @ tA).mean()))}")
pa0, pb0 = unit(A.mean(0)), unit(B.mean(0))
for h in (0, 19, 27, 50, 100):
    pa = unit(np.vstack([A, Hd[:h]]).mean(0))
    pb = unit(np.vstack([B, Hd[:h]]).mean(0))
    print(f"  h={h:3d} share s={h / (h + 150):.3f}: cos(A with header, A bare) {f4(float(pa @ pa0))} |"
          f" cos(A, B), different topics, same header {f4(float(pa @ pb))} | cos(A with header, header topic) {f4(float(pa @ tH))}")

# ---------------------------------------------------------------- K14
head("K14 upstream contextual_chunk_headers.ipynb @ 009adba (cells 0-based)")
if NB and NB.exists():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    print("  notebook sha256", hashlib.sha256(NB.read_bytes()).hexdigest()[:16], "| cells", len(nb["cells"]))
    src = lambda i: "".join(nb["cells"][i]["source"])
    outs = lambda i: "".join("".join(o.get("text", "")) for o in nb["cells"][i].get("outputs", []))
    for i in (8, 9, 11, 13):
        s = src(i)
        keys = [k for k in ("nike", "Nike", "Understanding_Climate_Change", "chunk_size=800", "chunk_overlap=0",
                            "MAX_CONTENT_TOKENS = 4000", "gpt-3.5-turbo", "gpt-4o-mini", "temperature=0.2",
                            "rerank-english-v3.0", "cohere.Client", "Document Title", "[86]") if k in s]
        print(f"  cell {i} {nb['cells'][i]['cell_type']}: contains {keys}")
    o13 = outs(13)
    print("  cell 13 saved output:", " | ".join(x.strip() for x in o13.strip().splitlines()))
    print("  cell 11 saved output:", outs(11).strip()[:80])
    print("  execution counts:", [c.get("execution_count") for c in nb["cells"] if c["cell_type"] == "code"])
else:
    print("  SKIPPED: notebook path not given")

# ---------------------------------------------------------------- K15
head("K15 vendor numbers turned into absolute and relative change (formula)")
for a, b, what in ((5.7, 3.7, "contextual embeddings"), (5.7, 2.9, "+ contextual BM25"), (5.7, 1.9, "+ rerank")):
    print(f"  1 - recall@20 {a}% -> {b}% ({what}): absolute {b - a:+.1f} points, relative {(b - a) / a * 100:+.1f}%")
se = math.sqrt(10) / 50
print(f"  06 section 9.4: n=50 paired, b+c=10 -> SE {se:.3f}, 95% half-width {1.96 * se:.3f}, 80%-power effect ~{2.8 * se:.2f}")
print("  0.10576342 -> 0.92206234 (upstream cell 13): one chunk, one query, a cross-encoder relevance score; not a retrieval metric")

# ---------------------------------------------------------------- K16
head("K16 MiniLM (all-MiniLM-L6-v2) per arm: margins and dev-seed retrieval")
snap = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{L6.replace('/', '--')}"
if not snap.exists():
    print(f"  SKIPPED: {L6} is not in the local Hugging Face cache on this machine. Run this script (or the verify"
          " notebook) where the model is cached.")
else:
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(L6, device="cpu")
    tk = m.tokenizer
    for arm in ("none", "title", "path", "major"):
        n_tok = [len(tk(e)["input_ids"]) for e in EMBED[arm]]
        print(f"  {arm:6s} tokens incl. specials min/median/max {min(n_tok)}/{int(statistics.median(n_tok))}/{max(n_tok)};"
              f" over 256: {sum(x > 256 for x in n_tok)}")
    Q = m.encode([s["question"] for s in ANS], normalize_embeddings=True)
    E = {arm: m.encode(EMBED[arm], normalize_embeddings=True, batch_size=32) for arm in ("none", "title", "path", "major")}
    for arm in ("none", "title", "path", "major"):
        ranks, ces = [], []
        for qi, s in enumerate(ANS):
            r = order(E[arm] @ Q[qi])
            ranks.append(first_rel(r, s["qid"]))
            ces.append(ce_at(r, s["qid"]))
        hk, c4, mrr = summary(ranks, ces)
        print(f"  {arm:6s} first relevant rank {dict(zip([s['qid'] for s in ANS], ranks))} | Hit@4 {hk}/8 CE@4 {c4}/8 MRR@10 {mrr}")
    for q in ("D-002", "D-003"):
        qi = [s["qid"] for s in ANS].index(q)
        gold = REL[q]
        dpages = BYQ[q]["distractor_pages"]
        dist = [i for i in range(N) if PAGE[i] in dpages and "Paris" in chunks[i]["text"] and i not in gold]
        for arm in ("none", "title", "path", "major"):
            sc = E[arm] @ Q[qi]
            print(f"  {q} {arm:6s} best gold {max(sc[gold]):.4f} best distractor {max(sc[dist]):.4f}"
                  f" margin {max(sc[gold]) - max(sc[dist]):+.4f} (distractor chunks {dist})")
    from scipy.stats import kendalltau
    for qi, s in enumerate(ANS[:3]):
        tau = kendalltau(E["none"] @ Q[qi], E["title"] @ Q[qi]).statistic
        print(f"  Kendall tau none vs title, {s['qid']}: {tau:.4f}")
