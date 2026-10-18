"""I4 study-kit measurements (K1-K12): the numbers the I4 HTML lesson (proposition chunking) relies on.

I4 has no earlier lesson, lab or measure script, so this is its first facts script. It measures the mechanism only:
no LLM writes a proposition here. The proposition sets are hand-written (i4_tutor_props.jsonl, written by the tutor
on 2026-10-18 from the PyMuPDF page text; i4_planted_props.jsonl, six deliberate mistakes). They stand in for the
recorded LLM run that the research plans (phase_04_indexing.md, Concept I4, section 7) and that does not exist yet.

What it measures:
  K1  environment, corpus, the 97 v0 chunks (the parents), the draft seeds
  K2  the upstream notebook proposition_chunking.ipynb @ 009adba, read as data (cells 0-based)
  K3  the sentence splitter: units (headings, sentences) with offsets, per page and in total; its known errors
  K4  the tutor set: every source id exists, every span lies inside the document, alignment, parents, pronouns
  K5  the planted mistakes: which check catches which mistake (and which no code check catches)
  K6  coverage ceilings: sentence_coverage per scope; gold_reachability per draft seed
  K7  the three scorings on made-up ranked lists (D-002, D-007, D-005): arm (a) parents, arm (b) spans, text check
  K8  dilution toy: cosine of a one-fact query with an n-fact chunk vector = 1 / sqrt(n)
  K9  cost and size forecast for Corpus D (measured sentence counts; token and output sizes ASSUMED, labelled)
  K10 the frozen prompt prop_gen_v1: rendered size for p.10; 8-gram leakage test, clean and with an injected leak
  K11 Wilson intervals for hand-checked faithfulness samples (formula outputs, no labels exist yet)
  K12 the upstream k=4 ceiling and parent dedup (cells 20, 22, 32)

Local only: no Groq, Cohere or Claude call, no .env read, no network, no embedding model.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I4/i4_kit_measure.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        "<Book RAG>/upstream/RAG_Techniques/all_rag_techniques/proposition_chunking.ipynb" \
        > sources/verification/I4/out_i4_kit_measure.txt
"""
import hashlib
import importlib.metadata as md
import json
import math
import re
import sys
from pathlib import Path

import pymupdf                                        # pinned 1.26.7

PDF = Path(sys.argv[1])
NB = Path(sys.argv[2])
HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]

sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402


def head(t):
    print(f"\n=== {t}")


def f3(x):
    return "nan" if x is None else f"{x:.3f}"


# ---------------------------------------------------------------- corpus, 97 chunks, seeds (as P4 kit measure)
pdf_bytes = PDF.read_bytes()
pages = [p.get_text() for p in pymupdf.open(PDF)]
DOC = "\n".join(pages)
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
manifest06 = cc.build_manifest("climate", pages, pdf_bytes, {**cc.PARSER, "version": pymupdf.VersionBind}, cc.CLEANING_NONE)
SNAP = manifest06["snapshot_id"]
STARTS = [r["doc_char_start"] for r in manifest06["docs"][0]["page_table"]]
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
N = len(chunks)
TEXTS = {"climate": DOC}
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", STARTS[seg["page"] - 1] + seg["char_start"], STARTS[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]), s["G"], TEXTS)]
       for s in ANS}

head("K1 environment, corpus, parents, seeds")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "numpy")})
print("pdf sha256", hashlib.sha256(pdf_bytes).hexdigest(), "| pages", len(pages), "| doc chars", len(DOC), "| snapshot_id", SNAP)
print(f"parents = v0's 97 chunks (recursive 1000/200 per page, 07 H.1): count={N} params_hash={PH} chunks.jsonl sha256={SHA_JL}")
print(f"draft seeds: {len(SEEDS)} ({len(ANS)} answerable, all llm-draft); relevant chunk seqs per answerable seed: {REL}")


# ---------------------------------------------------------------- K2 the upstream notebook, read as data
head("K2 upstream proposition_chunking.ipynb @ 009adba (cells 0-based; read as JSON, never run)")
nb_bytes = NB.read_bytes()
nb = json.loads(nb_bytes)
cells = nb["cells"]


def src(i):
    return "".join(cells[i]["source"])


def outs(i):
    return "".join("".join(o.get("text", [])) or "".join(o.get("data", {}).get("text/plain", [])) for o in cells[i].get("outputs", []))


print("file sha256", hashlib.sha256(nb_bytes).hexdigest(), "| cells", len(cells))
m = re.search(r"from_tiktoken_encoder\(\s*chunk_size=(\d+), chunk_overlap=(\d+)", src(9))
print(f"cell 9: RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size={m.group(1)}, chunk_overlap={m.group(2)}); "
      f"encoding_name given: {'encoding_name' in src(9)} (library default 'gpt2'); embedder {re.search(r'model=.([^\"]+?).,', src(9)).group(1)}")
models = sorted(set(re.findall(r'ChatGroq\(model="([^"]+)"', src(12) + src(15))))
print(f"cells 12 and 15: ChatGroq models {models}; temperature=0 in both: {src(12).count('temperature=0') == 1 and src(15).count('temperature=0') == 1}")
rules = re.findall(r"^\s*(\d)\. ([^:]+):", src(12), re.M)
print(f"cell 12 system prompt rules: {[f'{a}. {b}' for a, b in rules]}")
ex_doc = re.search(r'"document":\s*\n\s*"([^"]+)"', src(12)).group(1)
ex_props = re.findall(r"'([^']+?\.)'", re.search(r'"propositions":\s*\n\s*"(\[.+?\])"', src(12)).group(1))
print(f"cell 12 few-shot document: {ex_doc!r}")
print(f"cell 12 few-shot propositions ({len(ex_props)}): {ex_props}")
grades = re.findall(r'"accuracy": (\d+), "clarity": (\d+), "completeness": (\d+), "conciseness": (\d+)', src(15))
print(f"cell 15 grader examples: {len(grades)}, all 10/10/10/10: {all(g == ('10', '10', '10', '10') for g in grades)}; "
      f"label typos: 'Propositons' x{src(15).count('Propositons_')}, 'Evaluation_3' x{src(15).count('Evaluation_3')}")
human_turn = re.search(r'\("human", "([^"]+)"\)', src(15))
print(f"cell 15 human turn: {human_turn.group(1) if human_turn else None!r}")
print(f"cell 16 thresholds: {re.search(r'thresholds = (\{[^}]+\})', src(16)).group(1)}; keep rule: every grade >= 7")
fails = re.findall(r"(\d+)\) Propostion: (.+?) \n Scores: (\{[^}]+\})\nFail", outs(16))
print(f"cell 16 saved output: {len(fails)} rejected: " + "; ".join(f"#{a} {c}" for a, _, c in fails))
code_prints = "print(f\"{idx+1}) Propostion: {proposition.page_content} \\n Scores: {scores}\")" in src(16) and 'print("Fail")' in src(16)
print(f"cell 16 code prints exactly this '<n>) Propostion: ... Scores: ...' + 'Fail' format: {code_prints} (so the saved output is consistent with the code)")
emb = re.search(r"(\d+)/(\d+) \[", outs(18))
print(f"cell 18 embedding progress: {emb.group(1)}/{emb.group(2)} propositions embedded -> generated = {int(emb.group(1)) + len(fails)} "
      f"(kept + rejected), rejected share {len(fails)}/{int(emb.group(1)) + len(fails)} = {len(fails) / (int(emb.group(1)) + len(fails)):.3f}")
print(f"cell 18 retriever k: {re.search(chr(39) + 'k' + chr(39) + r': (\d+)', src(18)).group(1)}; cell 18 sets no model (the model is set in cell 9)")


def ranked(i):
    return re.findall(r"\d+\) Content: (.+?) --- Chunk_id: (\d+)", outs(i), re.S)


for i in (20, 28, 32, 36):
    hits = ranked(i)
    print(f"cell {i} top-{len(hits)} propositions: " + " | ".join(f"{t} [chunk {c}]" for t, c in hits))
    print(f"   distinct chunk ids {sorted(set(c for _, c in hits))}; hits containing 'Founder Mode is': "
          f"{sum('Founder Mode is' in t for t, _ in hits)}")
lg = re.search(r"(\d+)/(\d+) \[", outs(22))
print(f"cell 22 chunk index: {lg.group(1)} chunks embedded, retriever k = 4 -> k >= chunks: {4 >= int(lg.group(1))}")


# ---------------------------------------------------------------- K3 the sentence splitter
SENT_END = re.compile(r'[.!?]["”)\]]?(?=\s|$)')
LINE_END = re.compile(r'[.!?:]["”)\]]?\s*$')


def split_page(t):
    """Units of one page as (kind, a, b), page-relative offsets, whitespace trimmed. kind 'h' = heading line,
    's' = sentence. A heading is a short line (< 80 chars) that starts with a capital letter, has no end
    punctuation, and is not inside an unfinished sentence. A sentence ends at . ! ? followed by whitespace."""
    units, buf, pos = [], None, 0
    for ln in t.split("\n"):
        a, s = pos, ln.strip()
        pos += len(ln) + 1
        if not s:
            continue
        a2 = a + len(ln) - len(ln.lstrip())
        b2 = a + len(ln.rstrip())
        if buf is None and not LINE_END.search(s) and s[0].isupper() and len(s) < 80:
            units.append(("h", a2, b2))
            continue
        if buf is None:
            buf = a2
        for mt in SENT_END.finditer(ln):
            e = a + mt.end()
            if e <= buf:
                continue
            units.append(("s", buf, e))
            buf = None
            rest = ln[mt.end():]
            if rest.strip():
                buf = a + mt.end() + len(rest) - len(rest.lstrip())
    if buf is not None:
        units.append(("s", buf, len(t.rstrip())))
    return units


UNITS = {}                                            # "page:i" -> dict
for pn, t in enumerate(pages, 1):
    for i, (k, a, b) in enumerate(split_page(t)):
        UNITS[f"{pn}:{i}"] = {"id": f"{pn}:{i}", "page": pn, "kind": k, "a": a, "b": b,
                              "da": STARTS[pn - 1] + a, "db": STARTS[pn - 1] + b, "text": t[a:b]}
assert all(DOC[u["da"]:u["db"]] == u["text"] for u in UNITS.values())

head("K3 sentence splitter (regex, offsets kept; headings are their own units)")
per_page = []
for pn in range(1, len(pages) + 1):
    us = [u for u in UNITS.values() if u["page"] == pn]
    per_page.append((pn, sum(u["kind"] == "s" for u in us), sum(u["kind"] == "h" for u in us)))
ns = [s for _, s, _ in per_page]
nh = [h for _, _, h in per_page]
srt = sorted(ns)
print(f"sentences per page: {dict((p, s) for p, s, _ in per_page)}")
print(f"total sentences {sum(ns)}, headings {sum(nh)}, units {len(UNITS)}; sentences per page min {min(ns)} / median {srt[len(srt) // 2]} / max {max(ns)}")
words4 = sum(len(re.findall(r"\S+", u["text"])) >= 4 for u in UNITS.values() if u["kind"] == "s")
print(f"sentences of >= 4 words: {words4} (research rough pdftotext count: about 620)")
print("all units satisfy DOC[da:db] == text: True")
print("p.10 units:")
for u in (u for u in UNITS.values() if u["page"] == 10):
    print(f"  [{u['id']}] {u['kind']} page [{u['a']}, {u['b']}) doc [{u['da']}, {u['db']}) {u['text']!r}")
tests = {
    "'1.5 degrees' stays inside one sentence (10:7)": "1.5 degrees Celsius." in UNITS["10:7"]["text"],
    "'pre-industrial' and the line break stay inside 10:7": "pre-industrial" in UNITS["10:7"]["text"],
    "heading 'Paris Agreement' is its own unit (10:6)": UNITS["10:6"]["kind"] == "h" and UNITS["10:6"]["text"] == "Paris Agreement",
    "lower-case page start is not a heading (29:0)": UNITS["29:0"]["kind"] == "s",
    "'market-\\nbased' kept inside 29:2": "market-\nbased" in UNITS["29:2"]["text"],
}
for k, v in tests.items():
    print(f"  test: {k}: {v}")
frag = sorted((u for u, x in UNITS.items() if u.endswith(":0") and x["kind"] == "s" and x["text"][0].islower()), key=lambda u: int(u.split(":")[0]))
lastu = {}
for u, x in UNITS.items():
    lastu[x["page"]] = max(lastu.get(x["page"], -1), int(u.split(":")[1]))
cut = [f"{pg}:{i}" for pg, i in sorted(lastu.items()) if UNITS[f"{pg}:{i}"]["kind"] == "s" and not re.search(r'[.!?]["\u201d)\]]?$', UNITS[f"{pg}:{i}"]["text"])]
print(f"pages that start with the end of the previous page's sentence ({len(frag)}): {frag}")
print(f"pages whose last sentence is cut at the page end ({len(cut)}): {cut}")
print(f"known splitter limits (shown, not fixed): page-start fragment 23:0 = {UNITS['23:0']['text']!r} (the end of a p.22 sentence); "
      f"a sentence that continues onto the next page is cut at the page end; 'e.g.' would split a sentence "
      f"(occurrences of 'e.g.' in the document: {DOC.count('e.g.')})")


# ---------------------------------------------------------------- shared: words, alignment, parents
STOP = set("""a an the is are was were be been being of in on at to for and or but with by as from that this these those
it its their them they such which who whom whose than then there here into over under about also can may might will would
should could has have had do does did not no nor so very via per each every all both other another some any many much more
most less least only just up down out off our your his her he she we you i if while when where what how why""".split())


def stem(w):
    for suf in ("ing", "ed", "es", "s", "e"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def words(t):
    t = re.sub(r"-\s*\n\s*", "-", t.lower())
    return {stem(w) for w in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", t) if (len(w) > 1 or w.isdigit()) and w not in STOP}


PRONOUN_START = re.compile(r"^(it|its|they|their|them|this|these|those|that|he|she|his|her|such)\b", re.I)


def load(name):
    return [json.loads(l) for l in (HERE / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def check_prop(p):
    """C3 ids and span, alignment with verified resolved names, parents, pronoun start."""
    ids_ok = all(i in UNITS for i in p["source_ids"]) and len(p["source_ids"]) > 0
    r = {"prop_id": p["prop_id"], "ids_ok": ids_ok}
    if not ids_ok:
        r.update(span=None, align=None, parents=[], pronoun=bool(PRONOUN_START.match(p["text"])), resolved_ok=None)
        return r
    us = [UNITS[i] for i in p["source_ids"]]
    a, b = min(u["da"] for u in us), max(u["db"] for u in us)
    first = min(u["da"] for u in us)
    pg = us[0]["page"]
    before = DOC[STARTS[pg - 1]:first]
    resolved_ok = all(words(nm) <= words(before) for nm in p["resolved"])
    allowed = set().union(*(words(u["text"]) for u in us))
    if resolved_ok:
        allowed |= set().union(set(), *(words(nm) for nm in p["resolved"]))
    W = words(p["text"])
    contain = [c["seq"] for c in chunks if c["char_start"] <= a and b <= c["char_end"]]
    overlap = [c["seq"] for c in chunks if c["char_start"] < b and a < c["char_end"]]
    r.update(span=(a, b), inside=0 <= a < b <= len(DOC), align=len(W & allowed) / len(W), unsupported=sorted(W - allowed),
             parents=contain or overlap, contained=bool(contain), pronoun=bool(PRONOUN_START.match(p["text"])),
             resolved_ok=resolved_ok, one_page=len({u["page"] for u in us}) == 1)
    return r


TUTOR = load("i4_tutor_props.jsonl")
PLANT = load("i4_planted_props.jsonl")
RT = {p["prop_id"]: check_prop(p) for p in TUTOR}
RP = {p["prop_id"]: check_prop(p) for p in PLANT}
PT = {p["prop_id"]: p for p in TUTOR + PLANT}

head("K4 the tutor-written proposition set (hand-written by the tutor 2026-10-18; NOT an LLM output)")
print(f"file i4_tutor_props.jsonl sha256 {hashlib.sha256((HERE / 'i4_tutor_props.jsonl').read_bytes()).hexdigest()}; "
      f"propositions {len(TUTOR)}; by page {dict((pg, sum(p['page'] == pg for p in TUTOR)) for pg in sorted({p['page'] for p in TUTOR}))}")
for p in TUTOR:
    r = RT[p["prop_id"]]
    print(f"  {p['prop_id']} ids={p['source_ids']} span={list(r['span'])} align={r['align']:.3f} parents={r['parents']} "
          f"resolved={p['resolved']} ok={r['resolved_ok']} | {p['text']}")
print(f"C3 every source id exists: {all(r['ids_ok'] for r in RT.values())}; every span inside the document: {all(r['inside'] for r in RT.values())}; "
      f"every proposition's sources on one page: {all(r['one_page'] for r in RT.values())}")
print(f"every resolved name occurs earlier on the same page: {all(r['resolved_ok'] for r in RT.values())}; "
      f"propositions using a resolved name: {sum(bool(p['resolved']) for p in TUTOR)}")
print(f"align: min {min(r['align'] for r in RT.values()):.3f}; propositions with align < 1: {[k for k, r in RT.items() if r['align'] < 1]}")
print(f"C7 pronoun-initial propositions: {[k for k, r in RT.items() if r['pronoun']]}")
npar = [len(r["parents"]) for r in RT.values()]
print(f"parents: span fully inside a chunk for {sum(r['contained'] for r in RT.values())}/{len(TUTOR)}; "
      f"1 parent {npar.count(1)}, 2 parents (the 200-char overlap) {npar.count(2)}; primary parent = lowest seq")
print(f"index units: {len(TUTOR)} propositions from {len({u for p in TUTOR for u in p['source_ids'] if UNITS[u]['kind'] == 's'})} source sentences "
      f"-> {len(TUTOR) / len({u for p in TUTOR for u in p['source_ids'] if UNITS[u]['kind'] == 's'}):.2f} per sentence (Dense X README: 257M / 114M = {257 / 114:.2f})")
from collections import Counter as _C
_norm = _C(" ".join(re.findall(r"[a-z0-9.]+", p["text"].lower())) for p in TUTOR)
_dups = [[q["prop_id"] for q in TUTOR if " ".join(re.findall(r"[a-z0-9.]+", q["text"].lower())) == t] for t, c in _norm.items() if c > 1]
print(f"near-duplicate groups (same normalised text): {_dups}; distinct texts {len(_norm)}/{len(TUTOR)}")
for pid in ("p10-07", "p10-08", "p23-02"):
    print(f"  normalised text {pid}: {' '.join(re.findall(r'[a-z0-9.]+', PT[pid]['text'].lower()))!r}")


# ---------------------------------------------------------------- K5 planted mistakes
head("K5 planted mistakes: which check catches which (i4_planted_props.jsonl)")
UP_SRC = ex_doc
ast = "Neil Armstrong was an astronaut."
Wa = words(ast)
print(f"upstream few-shot 'astronaut' proposition: words {sorted(Wa)}; unsupported {sorted(Wa - words(UP_SRC))}; "
      f"align = {len(Wa & words(UP_SRC))}/{len(Wa)} = {len(Wa & words(UP_SRC)) / len(Wa):.3f}")
for p in PLANT:
    r = RP[p["prop_id"]]
    al = r["align"]
    print(f"  {p['prop_id']} [{p['error']}] ids_ok={r['ids_ok']} align={f3(al)} unsupported={r.get('unsupported')} pronoun={r['pronoun']} "
          f"| flagged by align<0.5: {al is not None and al < 0.5} | by align<1: {al is not None and al < 1} | {p['text']}")
print("not caught by any code check: x-03 (qualifier 'well' dropped: align only sees ADDED words) and x-04 (wrong referent: "
      "'Paris Agreement' is in the source sentence, so every word is supported). Only a person reading against the source catches them.")


# ---------------------------------------------------------------- K6 coverage ceilings
head("K6 coverage ceilings")
SCOPES = {"p.10 (whole page)": [u for u in UNITS if UNITS[u]["page"] == 10],
          "p.23 Paris section (23:25-23:27)": ["23:25", "23:26", "23:27"],
          "p.29 COP section (29:12-29:14)": ["29:12", "29:13", "29:14"],
          "p.2 coal and gas paragraphs (2:0-2:2, 2:8-2:10)": ["2:0", "2:1", "2:2", "2:8", "2:9", "2:10"]}
covered = {u for p in TUTOR for u in p["source_ids"]}
for nm, ids in SCOPES.items():
    sent = [u for u in ids if UNITS[u]["kind"] == "s"]
    hit = [u for u in sent if u in covered]
    miss = [u for u in sent if u not in covered]
    print(f"sentence_coverage {nm}: {len(hit)}/{len(sent)} = {len(hit) / len(sent):.3f}; sentences with no proposition: "
          + ("; ".join(f"[{u}] {UNITS[u]['text']!r}" for u in miss) if miss else "none"))
SP = [("climate", *RT[p["prop_id"]]["span"]) for p in TUTOR]
alts = reach = 0
for s in ANS:
    per_g = []
    for g in s["G"]:
        per_alt = [any(cc.rel(sp, [[alt]], TEXTS) for sp in SP) for alt in g]
        alts += len(per_alt)
        reach += sum(per_alt)
        per_g.append(any(per_alt))
    print(f"gold_reachability {s['qid']}: groups reachable {per_g} -> all groups {all(per_g)}")
print(f"gold_reachability (alternatives overlapped by some span(p)): {reach}/{alts} = {reach / alts:.3f} "
      "(the tutor set covers only parts of pages 2, 10, 23 and 29, so this is a property of the sample, not of the method)")


# ---------------------------------------------------------------- K7 the three scorings on made-up ranked lists
head("K7 the three scorings on made-up ranked lists (orders are illustrative, NOT model output)")
GOLD_TEXT = {"D-002": ["2015"], "D-007": ["Conference of the Parties", "COP"], "D-005": ["coal", "natural gas"]}


def score_lists(qid, order, k=4):
    s = BYQ[qid]
    rows = []
    for rank, pid in enumerate(order, 1):
        r = RT[pid]
        relb = cc.rel(("climate", *r["span"]), s["G"], TEXTS)
        rows.append((rank, pid, r["parents"][0], relb))
        print(f"  {qid} rank {rank}: {pid} parent {r['parents'][0]} (page {chunks[r['parents'][0]]['page_segments'][0]['page']}) "
              f"span-overlaps-gold={relb} parent-relevant={int(r['parents'][0] in REL[qid])} | {PT[pid]['text']}")
    parents = []
    for _, _, par, _ in rows:
        if par not in parents:
            parents.append(par)
    top_k_parents = []
    for _, _, par, _ in rows[:k]:
        if par not in top_k_parents:
            top_k_parents.append(par)
    rr_a = next((1 / i for i, par in enumerate(parents, 1) if par in REL[qid] and i <= 10), 0.0)
    rr_b = next((1 / rk for rk, _, _, rb in rows if rb and rk <= 10), 0.0)
    ce_a = cc.ce(s["G"], [("climate", chunks[p]["char_start"], chunks[p]["char_end"]) for p in top_k_parents], TEXTS)
    ce_b = cc.ce(s["G"], [("climate", *RT[pid]["span"]) for _, pid, _, _ in rows[:k]], TEXTS)
    norm = [" ".join(re.findall(r"[a-z0-9.]+", PT[pid]["text"].lower())) for _, pid, _, _ in rows[:k]]
    print(f"  {qid} arm (a) parents after dedup {parents}; relevant parents {REL[qid]}; RR = {rr_a:.3f}; "
          f"top {k} propositions -> {len(top_k_parents)} distinct parents {top_k_parents}; CE@{k} on those parents = {ce_a}")
    print(f"  {qid} arm (b) RR = {rr_b:.3f}; CE@{k} on the union of the top-{k} spans = {ce_b}; distinct-facts@{k} = {len(set(norm))}")
    return rows


rows = score_lists("D-002", ["p10-08", "p23-02", "p10-07", "p10-10", "p23-01", "p10-09"])
rr_t = next((1 / rk for rk, pid, _, rb in rows if rb and "2015" in PT[pid]["text"]), 0.0)
print(f"  D-002 text check: the first proposition whose span overlaps gold AND whose text states '2015' is at rank "
      f"{next(rk for rk, pid, _, rb in rows if rb and '2015' in PT[pid]['text'])}: RR = {rr_t:.3f}")
score_lists("D-007", ["p29-01", "p10-01", "p10-06", "p10-05", "p29-04", "p10-03"])
score_lists("D-007", ["p29-01", "p10-01", "p10-06", "p29-04", "p10-05", "p10-03"])
score_lists("D-005", ["p02-01", "p02-02", "p02-04", "p02-03", "p02-05", "p02-06"])


# ---------------------------------------------------------------- K8 dilution toy
head("K8 dilution toy (made-up orthonormal fact vectors; the chunk vector is the normalised mean of n facts)")
print("cos(one-fact query, n-fact chunk) = 1/sqrt(n): " + ", ".join(f"n={n}: {1 / math.sqrt(n):.3f}" for n in range(1, 9)))
print(f"a one-fact distractor with cos 0.60 to the query beats the right chunk once n >= {next(n for n in range(1, 20) if 1 / math.sqrt(n) < 0.60)}")


# ---------------------------------------------------------------- K9 cost and size forecast
head("K9 cost and size forecast for Corpus D (sentence counts measured; per-call tokens ASSUMED from the research, section 9)")
S_TOT = sum(ns)
RATIO = 257 / 114
P_EST = round(S_TOT * RATIO)
P_TUT = round(S_TOT * len(TUTOR) / len({u for p in TUTOR for u in p['source_ids'] if UNITS[u]['kind'] == 's'}))
TOK_PER_CHAR = 12840 / 72593                          # P1_FACTS M S3: o200k_harmony tokens / chars, whole document
print(f"sentences {S_TOT}; propositions at the Dense X ratio {RATIO:.3f}: about {P_EST}; at the tutor set's ratio: about {P_TUT}")
print(f"page input tokens (DERIVED: chars x {TOK_PER_CHAR:.4f}, P1 o200k_harmony ratio): mean {sum(len(p) for p in pages) / len(pages) * TOK_PER_CHAR:.0f}; "
      f"p.10 {len(pages[9]) * TOK_PER_CHAR:.0f}")
PRICE_IN, PRICE_OUT, TPD, TPM = 0.075, 0.30, 200_000, 8_000    # LLMOPS 6.2 / prices_2026-10-17.json (plan UNVERIFIED)
ASSUME = {"gen": (1050, 1600), "batched": (1800, 1600), "per_prop": (870, 300)}
print(f"assumed tokens per call (research I4 section 9, not measured): generation {ASSUME['gen']}, batched grade {ASSUME['batched']}, per-proposition grade {ASSUME['per_prop']} (in, out incl. reasoning)")


def plan(npages, nprops, grading):
    calls = {"gen": npages, "batched": npages if grading == "batched" else 0, "per_prop": nprops if grading == "per_prop" else 0}
    tin = sum(calls[k] * ASSUME[k][0] for k in calls)
    tout = sum(calls[k] * ASSUME[k][1] for k in calls)
    usd = (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
    return sum(calls.values()), tin + tout, usd


for nm, npg, npr in (("subset 5 pages", 5, round(P_EST * 5 / 33)), ("Corpus D 33 pages", 33, P_EST)):
    for gr in ("off", "batched", "per_prop"):
        c, t, u = plan(npg, npr, gr)
        print(f"  {nm} (about {npr} propositions), grading {gr}: {c} calls, {t:,} tokens, ${u:.3f}, "
              f"{t / TPD:.2f} days of 200K TPD, at least {t / TPM:.0f} min at 8K TPM")
for dim, nm in ((384, "MiniLM"), (1536, "Cohere embed-v4.0 default")):
    print(f"index size float32 {nm} dim {dim}: 97 chunks {97 * dim * 4 / 1024:.0f} KiB vs about {P_EST} propositions "
          f"{P_EST * dim * 4 / 1024:.0f} KiB (x{P_EST / 97:.1f} vectors)")
for gr in ("off", "batched", "per_prop"):
    c, t, u = plan(33, P_EST, gr)
    print(f"cost per 1k chunks (DERIVED: Corpus D cost x 1000 / 97 chunks), grading {gr}: {c * 1000 / 97:,.0f} calls, "
          f"{t * 1000 / 97:,.0f} tokens, ${u * 1000 / 97:.2f}")


# ---------------------------------------------------------------- K10 the frozen prompt and the leakage test
head("K10 prompt prop_gen_v1: rendered size; 8-gram leakage test")
PROMPT = (HERE / "prop_gen_v1.txt").read_text(encoding="utf-8")
SCHEMA = json.loads((HERE / "proposition_set_v1.json").read_text(encoding="utf-8"))
print(f"prop_gen_v1.txt sha256 {hashlib.sha256(PROMPT.encode('utf-8')).hexdigest()}; proposition_set_v1.json sha256 "
      f"{hashlib.sha256((HERE / 'proposition_set_v1.json').read_bytes()).hexdigest()}; schema required {SCHEMA['properties']['propositions']['items']['required']}")


def render(pn):
    lines = []
    for u in (u for u in UNITS.values() if u["page"] == pn):
        txt = re.sub(r"\s+", " ", u["text"])
        lines.append(f"[{u['id']}] " + ("(heading) " if u["kind"] == "h" else "") + txt)
    return PROMPT.replace("{units}", "\n".join(lines))


r10 = render(10)
print(f"rendered prompt for p.10: {len(r10)} chars, about {len(r10) * TOK_PER_CHAR:.0f} tokens (DERIVED ratio); template alone {len(PROMPT)} chars")
print("rendered p.10 units block, first 3 lines: " + " || ".join(r10.split("Page:\n")[1].splitlines()[:3]))


def toks(t):
    return re.findall(r"[a-z0-9]+", t.lower())


def ngrams(t, n=8):
    w = toks(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


EVAL_TEXT = [s["question"] for s in SEEDS] + [alt["quote"] for s in SEEDS for g in s["evidence_groups"] for alt in g["alternatives"]]
EV = set().union(*(ngrams(t) for t in EVAL_TEXT))
example_part = PROMPT.split("Page:\n")[0]
print(f"eval texts checked: {len(EVAL_TEXT)} (10 questions + {len(EVAL_TEXT) - 10} gold quotes), {len(EV)} distinct 8-grams")
print(f"clean: template + few-shot example share {len(ngrams(example_part) & EV)} 8-grams with the eval texts")
leaky = example_part.replace("The town library opened in 1998.", "The Paris Agreement, adopted in 2015, aims to limit global warming to well below 2 degrees Celsius.")
print(f"injected leak (example sentence replaced by the D-002 quote): {len(ngrams(leaky) & EV)} shared 8-grams -> the test fails as it should")


# ---------------------------------------------------------------- K11 Wilson intervals
head("K11 Wilson 95% intervals for a hand-checked faithfulness sample (formula outputs; no labels exist yet)")
for x, n in ((27, 30), (54, 60), (51, 60), (57, 60)):
    lo, hi = cc.wilson(x, n)
    print(f"  {x}/{n} supported = {x / n:.3f}: Wilson [{lo:.3f}, {hi:.3f}]; lower bound >= 0.85: {lo >= 0.85}")
need = next(n for n in range(20, 2000, 20) if cc.wilson(n * 19 // 20, n)[0] >= 0.85)
print(f"smallest n (a multiple of 20) where 95% supported gives a Wilson lower bound >= 0.85: {need} ({need * 19 // 20}/{need})")


# ---------------------------------------------------------------- K12 upstream ceiling and parent dedup
head("K12 the upstream k = 4 ceiling and parent dedup")
for i in (20, 32):
    hits = ranked(i)
    print(f"cell {i}: {len(hits)} proposition hits -> {len(set(c for _, c in hits))} distinct parent chunk(s) {sorted(set(c for _, c in hits))} "
          "(a MultiVectorRetriever-style return would give 1 parent, not 4)")
print(f"cell 22: chunk retriever k = 4 over {lg.group(1)} chunks: every query returns the whole chunk index, so its 'comparison' cannot rank")
print("DONE")
