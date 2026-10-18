"""Test study/tools/qrels_check.py against P2_FACTS (S3-S5, S8, S9, K2-K6) and small made-up cases.

1. The inverted index equals a brute-force scan (toy and climate PDF); its counts equal S3 (88 / 114 / 71) and S9
   (91 windows; 1,868 / 8,107 / 11,807 / 745); AND / OR / postings read equal S4 and S9; the keyword run equals S5.
2. Set metrics equal the S8 hand values (runs A, B, C; edge cases); recall@k from the tool equals K3 (k = 3 and 6).
3. Span conversion: the 06 §6.7 seeds give exactly the K5 windows, per question and per alternative; the example
   spans file is a byte copy of the 06 block; a broken offset is caught (Q11 fails).
4. The toy pool (--pool-from keyword:3, --dense, k = 4) equals K4: Judged@4, P@4 full vs pooled, recall full vs pooled.
5. TREC: export -> re-import gives the same labels (climate spans and toy JSONL); --unlisted zero exports 50 pairs.
6. Ties at the cut-off: toy q4 at k = 1 (d06 and d09 both score 1, K2) is reported and fails Q8; at k = 4 it is not.
7. Each recommendation branch end to end (labels not ready / pool biased / do not report a winner / rewrite the
   guideline / fit for metrics), the rule order on synthetic checklists, Q1, Q2, Q4 and Q10 (κ on IIR Table 8.2 = K6).
8. The CLI writes the saved example reports byte for byte, a second run is byte-identical, and the tool's source makes
   no network or API call.

No API calls; MiniLM loads from the local Hugging Face cache (offline). Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P2/p2_tool_test.py ["<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"]
Saved output: sources/verification/P2/out_p2_tool_test.txt
"""
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]                                           # rag_learning/
TOOL = WS / "study" / "tools" / "qrels_check.py"
EX = WS / "study" / "tools" / "examples"
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
SPANS = EX / "climate_seed_spans.jsonl"
TOY_C, TOY_Q, TOY_R = EX / "toy_chunks.jsonl", EX / "toy_questions.jsonl", EX / "toy_qrels.jsonl"
sys.path.insert(0, str(TOOL.parent))
import qrels_check as qc                                       # noqa: E402

RESULTS = []


def same(got, exp, tol):
    if isinstance(exp, (list, tuple)):
        return isinstance(got, (list, tuple)) and len(got) == len(exp) and all(same(g, e, tol) for g, e in zip(got, exp))
    if exp is None or isinstance(exp, (str, bool, dict)) or got is None:
        return got == exp
    return abs(float(got) - float(exp)) <= tol


def check(name, got, exp, tol=0.0):
    ok = same(got, exp, tol)
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got!r} | expected {exp!r}")
    return ok


V = lambda res, cid: next(i for i in res["checklist"] if i["id"] == cid)
verdicts = lambda res: " ".join(f"{i['id']}{i['verdict']}" for i in res["checklist"])
r3 = lambda x: None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, 3)
toy = json.loads((HERE / "p2_toy_corpus.json").read_text(encoding="utf-8"))
TMP = Path(tempfile.mkdtemp(prefix="p2_tool_"))


def write_jsonl(name, rows):
    p = TMP / name
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def toy_run(**kw):
    return qc.run_check(chunks=TOY_C, questions=kw.pop("questions", TOY_Q), qrels=kw.pop("qrels", TOY_R), **kw)


def climate_run(**kw):
    return qc.run_check(docs=[PDF], doc_ids=["climate"], spans=kw.pop("spans", SPANS), **kw)


# ================================================================ 0 example inputs are faithful copies
print("=== 0 example inputs")
plan = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
block = plan.split("Machine-readable form (offsets: PyMuPDF 1.26.7")[1].split("```jsonl")[1].split("```")[0]
check("0 climate_seed_spans.jsonl is the 06 §6.7 JSONL block, byte for byte", SPANS.read_text(encoding="utf-8") == block.strip("\n") + "\n", True)
tc = [json.loads(x) for x in TOY_C.read_text(encoding="utf-8").splitlines()]
tq = [json.loads(x) for x in TOY_Q.read_text(encoding="utf-8").splitlines()]
tr = [json.loads(x) for x in TOY_R.read_text(encoding="utf-8").splitlines()]
check("0 toy chunks = p2_toy_corpus.json docs", {c["id"]: c["text"] for c in tc} == toy["docs"], True)
check("0 toy questions = p2_toy_corpus.json queries", {q["id"]: q["q"] for q in tq} == toy["queries"], True)
check("0 toy qrels = p2_toy_corpus.json qrels (+ guideline_version v1)",
      [(r["qid"], r["doc"], r["grade"], r["why"], r["guideline_version"]) for r in tr]
      == [(r["qid"], r["did"], r["grade"], r["why"], "v1") for r in toy["qrels"]], True)

# ================================================================ 1 index
print("\n=== 1 inverted index (S3, S4, S5, S9)")
for label, chunks in (("toy", qc.load_chunks(TOY_C)), ("climate", qc.make_windows(qc.load_documents([PDF], ["climate"])))):
    ix = qc.InvertedIndex(chunks)
    scan = {}
    for i, c in enumerate(chunks):                              # an independent scan: every token of every chunk
        for t in re.findall(r"[a-z0-9]+", c["text"].lower()):
            scan.setdefault(t, set()).add(i)
    check(f"1 {label}: postings equal an independent scan", {t: set(p) for t, p in ix.postings.items()} == scan, True)
    check(f"1 {label}: equals_scan()", ix.equals_scan(), True)
ix = qc.InvertedIndex(qc.load_chunks(TOY_C))
st = ix.stats()
check("1 toy vocabulary / postings / df = 1 (S3: 88 / 114 / 71)", [st["vocab"], st["postings"], st["df1"]], [88, 114, 71])
check("1 toy commonest terms (S3: and 6, the 5, in 4)", st["top"][:3], [("and", 6), ("the", 5), ("in", 4)])
check("1 tokenize('Sea-level RISE, 2019!') (S2)", qc.tokenize("Sea-level RISE, 2019!"), ["sea", "level", "rise", "2019"])
S4 = {"q1": (1, 3, 10), "q2": (0, 1, 2), "q3": (0, 0, 0), "q4": (0, 2, 2), "q5": (0, 3, 5)}
for q, exp in S4.items():
    r = ix.query(toy["queries"][q])
    check(f"1 toy {q} AND / OR / postings read (S4)", [r["and"], r["or"], r["postings_read"]], list(exp))
ids = [c["id"] for c in qc.load_chunks(TOY_C)]
S5 = {"q1": [("d02", 5), ("d01", 3), ("d08", 2)], "q4": [("d06", 1), ("d09", 1)], "q5": [("d10", 3), ("d02", 1), ("d03", 1)]}
for q, exp in S5.items():
    check(f"1 toy {q} keyword ranking (S5)", [(ids[i], s) for i, s in ix.query(toy["queries"][q])["ranking"]], exp)
cl = climate_run()
ci = cl["index"]
check("1 climate windows / vocabulary / postings / tokens / df = 1 (S9: 91 / 1,868 / 8,107 / 11,807 / 745)",
      [ci["N"], ci["vocab"], ci["postings"], ci["tokens"], ci["df1"]], [91, 1868, 8107, 11807, 745])
check("1 climate last window 593 characters (S9)", cl["chunks"][-1]["end"] - cl["chunks"][-1]["start"], 593)
cix = qc.InvertedIndex(cl["chunks"])
for text, exp in (("main cause of climate change", (90, 0, 213)), ("methane emissions", (34, 5, 39)), ("renewable energy", (42, 30, 72))):
    r = cix.query(text)
    check(f"1 climate '{text}' OR / AND / postings read (S9)", [r["or"], r["and"], r["postings_read"]], list(exp))
check("1 climate df: and 91, climate 77, methane 5 (S9)", [cix.df("and"), cix.df("climate"), cix.df("methane")], [91, 77, 5])

# ================================================================ 2 set metrics
print("\n=== 2 set metrics (S8, K3)")
REL1 = {"d01", "d03", "d09"}
for name, run, exp in (("A", ["d02", "d01", "d08"], [0.3333, 0.3333, 2]), ("B", ["d01", "d08", "d02"], [0.3333, 0.3333, 1]),
                       ("C", ["d01", "d03", "d09"], [1.0, 1.0, 1])):
    check(f"2 run {name} precision / recall / first relevant rank (S8)",
          [round(qc.precision(run, REL1), 4), round(qc.recall(run, REL1), 4), qc.first_relevant_rank(run, REL1)], exp)
check("2 precision([]) = 0.0; first_relevant_rank(['d02']) = None (S8)", [qc.precision([], REL1), qc.first_relevant_rank(["d02"], REL1)], [0.0, None])
check("2 recall with no relevant chunk is undefined", math.isnan(qc.recall(["d01"], set())), True)
for k, exp in ((3, (0.567, 0.867)), (6, (0.567, 0.933))):
    r = toy_run(dense=True, unlisted="zero", k=k)
    check(f"2 mean recall@{k} keyword / MiniLM (S8, K3: {exp[0]} / {exp[1]})", [r3(r["runs"]["keyword"]["r"]), r3(r["runs"]["dense"]["r"])], list(exp))
r = toy_run(dense=True, unlisted="zero", k=6)
check("2 MiniLM q1 precision / recall at k = 6 (S8: 0.333 / 0.667)", [r3(r["runs"]["dense"]["rows"]["q1"]["p"]), r3(r["runs"]["dense"]["rows"]["q1"]["r"])], [0.333, 0.667])
check("2 MiniLM q1 ranking starts d02, d01, d04, d03 (S6, K4)", r["runs"]["dense"]["rows"]["q1"]["top"][:4], ["d02", "d01", "d04", "d03"])

# ================================================================ 3 spans -> windows
print("\n=== 3 span conversion (K5)")
K5 = {"D-001": [7], "D-002": [25, 26], "D-003": [63, 64], "D-004": [22, 63], "D-005": [2, 3, 4], "D-006": [20],
      "D-007": [25, 26, 79], "D-008": [64], "D-009": [], "D-010": []}
check("3 91 windows of 1,000 / step 800", [len(cl["chunks"]), cl["chunks"][1]["start"], cl["chunks"][0]["end"]], [91, 800, 1000])
for q, exp in K5.items():
    got = sorted(int(c.split("#")[1]) for c in cl["REL_FULL"][q])
    check(f"3 {q} relevant windows (K5)", got, exp)
alts = {(d["qid"], d["alt"]): [int(c.split("#")[1]) for c in d["chunks"]] for d in cl["span_details"]}
check("3 D-004 alternatives: p.8 -> 22, p.23 -> 63 (K5)", [alts[("D-004", "g1a")], alts[("D-004", "g1b")]], [[22], [63]])
check("3 D-005 groups: g1 -> 2, 3; g2 -> 3, 4 (K5)", [alts[("D-005", "g1a")], alts[("D-005", "g2a")]], [[2, 3], [3, 4]])
check("3 no span problems; Q11 passes", [cl["span_problems"], V(cl, "Q11")["verdict"]], [[], qc.OK])
check("3 every pair judged: 10 questions x 91 windows, 15 relevant", [len(cl["trec"].splitlines()), sum(len(v) for v in cl["REL_FULL"].values())], [910, 15])
items = [json.loads(x) for x in SPANS.read_text(encoding="utf-8").splitlines()]
bad = json.loads(json.dumps(items))
bad[1]["evidence_groups"][0]["alternatives"][0]["segments"][0]["char_start"] += 40      # shifted: the quote no longer matches
bad[0]["evidence_groups"][0]["alternatives"][0]["segments"][0]["char_end"] = 10 ** 6   # past the end of the page
rb = climate_run(spans=write_jsonl("bad_spans.jsonl", bad))
check("3 broken spans: 2 problems, Q11 fails -> labels not ready",
      [len(rb["span_problems"]), V(rb, "Q11")["verdict"], rb["recommendation"]["verdict"]],
      [2, qc.BAD, "labels not ready: fix the format and guideline first"])

# ================================================================ 4 the toy pool = K4
print("\n=== 4 one-retriever pool (K4)")
pool = toy_run(dense=True, pool_from="keyword:3", k=4)
kw, dn = pool["runs"]["keyword"], pool["runs"]["dense"]
check("4 keyword: mean Judged@4 0.450; P@4 full 0.433 = pooled 0.433; recall 0.567 full -> 1.000 pooled",
      [r3(kw["judged_k"]), r3(kw["p_full"]), r3(kw["p"]), r3(kw["r_full"]), r3(kw["r"])], [0.45, 0.433, 0.433, 0.567, 1.0])
check("4 MiniLM: mean Judged@4 0.350; P@4 0.350 full -> 0.200 pooled; recall 0.933 full -> 1.000 pooled",
      [r3(dn["judged_k"]), r3(dn["p_full"]), r3(dn["p"]), r3(dn["r_full"]), r3(dn["r"])], [0.35, 0.35, 0.2, 0.933, 1.0])
check("4 pooled recall averaged over 4 questions (q3 has no pooled relevant doc)", [kw["n_r"], dn["n_r"], dn["n_r_full"]], [4, 4, 5])
q1 = dn["rows"]["q1"]
check("4 MiniLM q1: top 4 d02, d01, d04, d03; 2 of 4 judged; P@4 0.500 -> 0.250",
      [q1["top"], q1["judged"], r3(q1["p_full"]), r3(q1["p"])], [["d02", "d01", "d04", "d03"], 2, 0.5, 0.25])
check("4 pooled relevant (K4): q1 d01, q2 d04, q3 none, q4 d09, q5 d10", {q: sorted(v) for q, v in pool["REL"].items()},
      {"q1": ["d01"], "q2": ["d04"], "q3": [], "q4": ["d09"], "q5": ["d10"]})
check("4 Hole@4: keyword 0, MiniLM 0.650; 13 holes; pool depth keyword 4, MiniLM 0",
      [r3(kw["hole_k"]), r3(dn["hole_k"]), len(pool["holes"]), kw["depth"], dn["depth"]], [0.0, 0.65, 13, 4, 0])
check("4 checklist", verdicts(pool), "Q1✓ Q2✓ Q3✓ Q4? Q5✗ Q6✗ Q7✗ Q8✓ Q9✗ Q10? Q11? Q12?")
check("4 Q7 bounds: MiniLM 0.200 -> 0.850 swaps with keyword 0.433", [r3(dn["p_upper"]), "`keyword` vs `dense`" in V(pool, "Q7")["evidence"]], [0.85, True])
check("4 Q9 lists q3 (vocabulary mismatch, S4)", "q3" in V(pool, "Q9")["evidence"], True)
check("4 recommendation: pool is biased",
      pool["recommendation"]["verdict"], "pool is biased: judge the listed holes (top-k chunks from every run that no one judged), then rerun")
both = toy_run(dense=True, pool_from="keyword:3,dense:3", k=4)
check("4 pooling both retrievers (top 3 each): Q5 passes; MiniLM Hole@4 = 0.250 (each question's rank 4 is outside both top 3s)",
      [V(both, "Q5")["verdict"], r3(both["runs"]["dense"]["hole_k"]), [len(both["runs"]["dense"]["rows"][q]["holes"]) for q in sorted(toy["queries"])]], [qc.OK, 0.25, [1, 1, 1, 1, 1]])

# ================================================================ 5 TREC round trip
print("\n=== 5 TREC export and re-import")
ct = TMP / "climate.trec"
ct.write_text(cl["trec"], encoding="utf-8")
rt = qc.run_check(docs=[PDF], doc_ids=["climate"], questions=SPANS, qrels=ct, guideline_version="g-test")
check("5 climate: TREC re-import gives the same relevant windows", rt["REL_FULL"] == cl["REL_FULL"], True)
check("5 climate: re-export is identical", rt["trec"] == cl["trec"], True)
check("5 climate: TREC on window ids fails Q2 (no reasons) and Q11 (chunk ids)", [V(rt, "Q2")["verdict"], V(rt, "Q11")["verdict"], V(rt, "Q3")["verdict"]], [qc.BAD, qc.BAD, qc.OK])
t0 = toy_run()
check("5 toy JSONL export: 13 listed pairs, first line 'q1 0 d01 2'", [len(t0["trec"].splitlines()), t0["trec"].splitlines()[0]], [13, "q1 0 d01 2"])
tt = TMP / "toy.trec"
tt.write_text(t0["trec"], encoding="utf-8")
t1 = toy_run(qrels=tt)
check("5 toy: TREC round trip keeps every grade", {(q, d): l["grade"] for q, v in t1["given"].items() for d, l in v.items()}
      == {(r["qid"], r["did"]): r["grade"] for r in toy["qrels"]}, True)
check("5 toy --unlisted zero exports all 50 pairs, 8 relevant (S7)", [len(toy_run(unlisted="zero")["trec"].splitlines()),
                                                                    sum(len(v) for v in toy_run(unlisted="zero")["REL_FULL"].values())], [50, 8])

# ================================================================ 6 ties at the cut-off
print("\n=== 6 ties at the cut-off (K2)")
k1 = toy_run(unlisted="zero", k=1)
tie = k1["runs"]["keyword"]["rows"]["q4"]["tie"]
check("6 k = 1: q4 tie reported (d06 and d09 both score 1; d06 kept by the rule, d09 relevant)",
      [tie["score"], tie["inside"], tie["outside"], tie["changes"]], [1, ["d06"], ["d09"], True])
check("6 k = 1: q4 first relevant rank within the top 1 = none (K2: rank 2 under the ascending rule)", k1["runs"]["keyword"]["rows"]["q4"]["first"], None)
check("6 k = 1: Q8 fails and names q4", [V(k1, "Q8")["verdict"], "`keyword` q4" in V(k1, "Q8")["evidence"]], [qc.BAD, True])
k2 = toy_run(unlisted="zero", k=2)
check("6 k = 2: q4 rank of d09 = 2, RR 0.50 (K2)", [k2["runs"]["keyword"]["rows"]["q4"]["first"]], [2])
k4 = toy_run(unlisted="zero", k=4)
check("6 k = 4: no tie straddles the cut; Q8 passes", [k4["runs"]["keyword"]["rows"]["q4"]["tie"], V(k4, "Q8")["verdict"]], [None, qc.OK])
ties = qc.tie_at_cut([("a", 2.0), ("b", 1.0), ("c", 1.0)], 2, {"c"})
check("6 tie_at_cut: a tie of two non-relevant chunks does not change P@k", qc.tie_at_cut([("a", 2.0), ("b", 1.0), ("c", 1.0)], 2, {"a"})["changes"], False)
check("6 tie_at_cut: a relevant chunk just outside the cut does", ties["changes"], True)

# ================================================================ 7 recommendation branches
print("\n=== 7 recommendation branches")
NOT_READY = "labels not ready: fix the format and guideline first"
POOL = "pool is biased: judge the listed holes (top-k chunks from every run that no one judged), then rerun"
WINNER = "your comparison is decided by unjudged chunks: do not report a winner"
GUIDE = "rewrite the guideline sentence for the disagreeing category; relabel; bump the guideline version"
FIT = "labels are fit for retrieval metrics (P6/M2); report Judged@k next to every number"
check("7 climate example: Q3 fails -> labels not ready (llm-draft note added)",
      [cl["recommendation"]["verdict"], any("llm-draft" in x for x in cl["recommendation"]["reasons"])], [NOT_READY, True])
check("7 climate with --guideline-version and --dense: fit for metrics",
      climate_run(dense=True, guideline_version="v1").get("recommendation")["verdict"], FIT)
check("7 TREC qrels (no reasons): labels not ready", toy_run(qrels=tt, guideline_version="v1")["recommendation"]["verdict"], NOT_READY)
# Q1 and Q2 failures
noreason = write_jsonl("noreason.jsonl", [dict(r, why="relevant") if r["qid"] == "q1" and r["doc"] == "d01" else r for r in tr])
r = toy_run(qrels=noreason, unlisted="zero")
check("7 a one-word reason fails Q2 -> labels not ready", [V(r, "Q2")["verdict"], r["recommendation"]["verdict"]], [qc.BAD, NOT_READY])
noq3 = write_jsonl("noq3.jsonl", [r_ for r_ in tr if r_["qid"] != "q3"])
r = toy_run(qrels=noq3)
check("7 q3 with no label and no 'answerable: false' fails Q1", [V(r, "Q1")["verdict"], "q3" in V(r, "Q1")["evidence"]], [qc.BAD, True])
qs_un = write_jsonl("q_unans.jsonl", [dict(q, answerable=(q["id"] != "q3")) for q in tq])
r = toy_run(qrels=noq3, questions=qs_un, unlisted="zero")
check("7 ... marked answerable: false and judged (unlisted = 0): Q1 passes", V(r, "Q1")["verdict"], qc.OK)
ghost = write_jsonl("ghost.jsonl", tr + [{"qid": "q1", "doc": "d99", "grade": 1, "why": "a chunk id that does not exist", "guideline_version": "v1"}])
check("7 a label on a chunk id that does not exist fails Q1", V(toy_run(qrels=ghost), "Q1")["verdict"], qc.BAD)
# fit for metrics: full toy labels, both runs, nothing unjudged
fit = toy_run(dense=True, unlisted="zero")
check("7 full toy labels + dense: Q5 Q6 Q7 pass -> fit for metrics", [V(fit, "Q5")["verdict"], V(fit, "Q6")["verdict"], V(fit, "Q7")["verdict"],
                                                                   fit["recommendation"]["verdict"]], [qc.OK, qc.OK, qc.OK, FIT])
check("7 one run only: Q5 and Q7 are '?'", [V(toy_run(unlisted="zero"), "Q5")["verdict"], V(toy_run(unlisted="zero"), "Q7")["verdict"]], [qc.ASK, qc.ASK])
# Q10: kappa and the relabel branch
po, kap = qc.cohen_kappa([1] * 300 + [1] * 20 + [0] * 10 + [0] * 70, [1] * 300 + [0] * 20 + [1] * 10 + [0] * 70)
check("7 κ on IIR Table 8.2 (K6: P(A) 0.9250, κ 0.7761 with separate marginals)", [round(po, 4), round(kap, 4)], [0.925, 0.7761])
full = {(q, d): next((r_["grade"] for r_ in toy["qrels"] if r_["qid"] == q and r_["did"] == d), 0) for q in sorted(toy["queries"]) for d in sorted(toy["docs"])}
flip = {("q1", "d03"), ("q1", "d09"), ("q2", "d05"), ("q1", "d06"), ("q5", "d03"), ("q4", "d06")}
relab = TMP / "relabel.trec"
relab.write_text("".join(f"{q} 0 {d} {(1 if g == 0 else 0) if (q, d) in flip else g}\n" for (q, d), g in full.items()), encoding="utf-8")
r = toy_run(dense=True, unlisted="zero", relabel=relab)
check("7 relabel with 6 of 50 flipped: agreement 0.880 < 0.90, Q10 fails -> rewrite the guideline",
      [round(r["agree"]["agreement"], 3), r["agree"]["n"], V(r, "Q10")["verdict"], r["recommendation"]["verdict"]], [0.88, 50, qc.BAD, GUIDE])
same_lab = TMP / "same.trec"
same_lab.write_text("".join(f"{q} 0 {d} {g}\n" for (q, d), g in full.items()), encoding="utf-8")
r = toy_run(dense=True, unlisted="zero", relabel=same_lab)
check("7 identical relabel: agreement 1.000, κ 1.000, Q10 passes -> fit", [r["agree"]["agreement"], round(r["agree"]["kappa"], 3), V(r, "Q10")["verdict"], r["recommendation"]["verdict"]],
      [1.0, 1.0, qc.OK, FIT])
small = TMP / "small.trec"
small.write_text("q1 0 d01 2\nq1 0 d02 0\n", encoding="utf-8")
check("7 relabel of 2 pairs: Q10 '?' (needs 10)", V(toy_run(unlisted="zero", relabel=small), "Q10")["verdict"], qc.ASK)
# Q7 alone: two runs of your own, holes under a looser limit, the order swaps
q1only = write_jsonl("q1.jsonl", [tq[0]])
lab7 = write_jsonl("lab7.jsonl", [{"qid": "q1", "doc": d, "grade": g, "why": "made-up label for the bounds test", "guideline_version": "v1"}
                                  for d, g in (("d01", 2), ("d09", 1), ("d02", 0), ("d08", 0), ("d06", 0))])
runA = write_jsonl("runA.jsonl", [{"qid": "q1", "docs": ["d01", "d09", "d02", "d08"]}])
runB = write_jsonl("runB.jsonl", [{"qid": "q1", "docs": ["d01", "d04", "d05", "d02"]}])
r = toy_run(questions=q1only, qrels=lab7, runs=[runA, runB], hole_limit=0.6)
check("7 run B: 2 holes in its top 4 (Hole@4 0.500), pool depth 1; P@4 0.250 -> 0.750 vs run A 0.500",
      [r3(r["runs"]["runB"]["hole_k"]), r["runs"]["runB"]["depth"], r3(r["runs"]["runB"]["p"]), r3(r["runs"]["runB"]["p_upper"]), r3(r["runs"]["runA"]["p"])],
      [0.5, 1, 0.25, 0.75, 0.5])
check("7 Q5 and Q6 pass, Q7 fails -> do not report a winner", [V(r, "Q5")["verdict"], V(r, "Q6")["verdict"], V(r, "Q7")["verdict"], r["recommendation"]["verdict"]],
      [qc.OK, qc.OK, qc.BAD, WINNER])
# Q4 timestamps
lab_ts = write_jsonl("lab_ts.jsonl", [dict(x, ts="2026-10-10T09:00:00Z") for x in json.loads("[" + ",".join(lab7.read_text().splitlines()) + "]")])
runA_late = write_jsonl("runA_late.jsonl", [{"qid": "q1", "docs": ["d01", "d09", "d02", "d08"], "ts": "2026-10-11T09:00:00Z"}])
runA_early = write_jsonl("runA_early.jsonl", [{"qid": "q1", "docs": ["d01", "d09", "d02", "d08"], "ts": "2026-10-09T09:00:00Z"}])
check("7 Q4: labels dated before the run file pass", V(toy_run(questions=q1only, qrels=lab_ts, runs=[runA_late]), "Q4")["verdict"], qc.OK)
check("7 Q4: labels dated after the run file fail", V(toy_run(questions=q1only, qrels=lab_ts, runs=[runA_early]), "Q4")["verdict"], qc.BAD)
check("7 Q4: no timestamps -> '?'", V(toy_run(questions=q1only, qrels=lab7, runs=[runA]), "Q4")["verdict"], qc.ASK)
# rule order on synthetic checklists (first match wins)
base = {"questions": [], "runs": {"keyword": {"judged_k": 1.0}}, "holes": [], "settings": {"k": 4}}
for failing, exp in ((["Q3", "Q5", "Q7", "Q10"], NOT_READY), (["Q11"], NOT_READY), (["Q6", "Q7", "Q10"], POOL), (["Q5"], POOL),
                     (["Q7", "Q10"], WINNER), (["Q10", "Q8", "Q9"], GUIDE), (["Q4", "Q8", "Q9", "Q12"], FIT), ([], FIT)):
    cl_items = [{"id": f"Q{i}", "verdict": qc.BAD if f"Q{i}" in failing else qc.OK, "evidence": "e"} for i in range(1, 13)]
    check(f"7 failing {failing}", qc.recommend(dict(base, checklist=cl_items))["verdict"], exp)

# ================================================================ 8 CLI, saved examples, determinism, no network
print("\n=== 8 CLI and saved examples")
out1, out2, trec1 = TMP / "c1.md", TMP / "c2.md", TMP / "c1.trec"
cmd = [sys.executable, str(TOOL), "--docs", str(PDF), "--doc-ids", "climate", "--spans", str(SPANS), "--dense", "--k", "4"]
cp1 = subprocess.run(cmd + ["--report", str(out1), "--trec-out", str(trec1)], capture_output=True, text=True, encoding="utf-8")
cp2 = subprocess.run(cmd + ["--report", str(out2)], capture_output=True, text=True, encoding="utf-8")
check("8 CLI exit 0 (twice)", [cp1.returncode, cp2.returncode], [0, 0])
check("8 CLI summary line", cp1.stdout.splitlines()[0], "chunks 91, vocabulary 1,868, postings 8,107")
check("8 a second run is byte-identical", out1.read_bytes() == out2.read_bytes(), True)
check("8 the saved climate example equals the CLI report", (EX / "climate_qrels_report.md").read_bytes() == out1.read_bytes(), True)
check("8 the saved climate_qrels.trec equals the CLI export", (EX / "climate_qrels.trec").read_bytes() == trec1.read_bytes(), True)
check("8 the climate report equals render_report(run_check(...))", out1.read_text(encoding="utf-8") == qc.render_report(climate_run(dense=True)), True)
rep = out1.read_text(encoding="utf-8")
check("8 report has the 7 parts", [f"## {n} " in rep for n in range(1, 8)], [True] * 7)
check("8 report marks the seeds as llm-draft", "> **Draft labels:** 10 of 10 questions are `created_by: llm-draft`" in rep, True)
check("8 climate checklist without --dense (one run: Q5, Q7 '?')", verdicts(cl), "Q1✓ Q2✓ Q3✗ Q4? Q5? Q6✓ Q7? Q8✗ Q9? Q10? Q11✓ Q12?")
check("8 climate checklist with --dense", verdicts(climate_run(dense=True)), "Q1✓ Q2✓ Q3✗ Q4? Q5✓ Q6✓ Q7✓ Q8✗ Q9? Q10? Q11✓ Q12?")
out3 = TMP / "toy.md"
cp3 = subprocess.run([sys.executable, str(TOOL), "--chunks", str(TOY_C), "--questions", str(TOY_Q), "--qrels", str(TOY_R), "--dense",
                      "--pool-from", "keyword:3", "--k", "4", "--report", str(out3)], capture_output=True, text=True, encoding="utf-8")
check("8 the saved toy example equals the CLI report", [cp3.returncode, (EX / "toy_qrels_report.md").read_bytes() == out3.read_bytes()], [0, True])
src = TOOL.read_text(encoding="utf-8")
check("8 the tool imports no network or API client", [w for w in ("requests", "urllib", "http.client", "groq", "cohere", "anthropic", "langsmith", "dotenv")
                                                      if re.search(rf"^\s*(import|from)\s+{re.escape(w)}", src, re.M)], [])
check("8 the tool forces the offline Hugging Face mode", 'os.environ.setdefault("HF_HUB_OFFLINE", "1")' in src, True)
banned = ["share of queries", "fraction of queries", "a guide says", "sixth", "add a pdf", "adding a document", "new document",
          "another pdf", "tenant", "300 pdf", "without reading", "half noise", "0.729", "three stages"]
texts = {p.name: p.read_text(encoding="utf-8").lower() for p in (TOOL, EX / "climate_qrels_report.md", EX / "toy_qrels_report.md")}
check("8 no coach-banned phrase in the tool or the example reports", [f"{n}: {b}" for n, t in texts.items() for b in banned if b in t], [])

shutil.rmtree(TMP, ignore_errors=True)
n_ok = sum(ok for _, ok in RESULTS)
print(f"\n{n_ok}/{len(RESULTS)} tool checks passed")
sys.exit(0 if n_ok == len(RESULTS) else 1)
