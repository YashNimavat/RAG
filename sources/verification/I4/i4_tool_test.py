"""Test study/tools/proposition_fit_check.py against I4_FACTS (K1, K3-K7, K9-K11) and small made-up cases.

1. Parents: the tool's v0 chunker gives exactly v0's 97 chunks (offsets and texts, as i4_kit_measure.py builds them
   from 06 + 07); the relevant chunks of the 8 answerable draft seeds equal K1; bad sizes raise.
2. Units (K3): 621 sentences, 286 headings, 907 units, 6 / 19 / 22 per page, 614 of >= 4 words; every unit equals the
   kit's (id, kind, offsets, text); the splitter tests; the known limits (23:0 "resources.", 0 "e.g.").
3. The tutor set (K4): ids, spans, one page, resolved names, align, pronouns, parents (34 / 6), 1.54 per sentence,
   every span and parent list equal to the kit's; the duplicate pair p10-08 = p23-02.
4. The planted mistakes (K5): align 0.400 / 0.750 / 1 / 1 / 1 / -, unsupported words, pronoun and id flags; the
   upstream astronaut proposition 0.667; the checklist flags and the recommendation.
5. Coverage (K6): the kit's four scopes; gold_reachability 6/12 over the 8 answerable seeds, per question.
6. The three scorings (K7) through score_order on the kit's made-up orders (D-002, D-007 twice, D-005).
7. The forecast (K9): Corpus D and the 5-page subset, per grading; index sizes; cost per 1k chunks; page tokens.
8. The prompt (K10): the built-in prop_gen_v1 is a byte copy of the frozen file; rendered p.10 size; the 8-gram
   leakage test clean (0) and with the injected leak (10); C10 fails on a leaky template.
9. Wilson (K11).
10. Inputs: text files (ids 1:i), several documents (ids stem#page:i, gold by stem), invalid records logged (C2),
    the 06 question form, a page field that disagrees, a resolved name not on the page, sample pages, errors.
11. The labelling sheet: columns, rows, read back; C5 with a Wilson bound; keep-good / catch-bad (C9).
12. Each recommendation branch end to end on small made-up documents (a word-count embedder stands in for MiniLM),
    and the rule order on synthetic checklists.
13. --dense without sentence-transformers is skipped with a message (or, where MiniLM is cached, runs).
14. The CLI writes the saved example report and labelling sheet byte for byte, a second run is byte-identical,
    --provider groq|anthropic refuses, --render-prompt prints the kit's rendering, and the tool's source makes no
    network or API call; no coach-banned phrase in the tool or the examples.

No API calls, no network. Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I4/i4_tool_test.py \\
        ["<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" "<...>/proposition_chunking.ipynb"]
Saved output: sources/verification/I4/out_i4_tool_test.txt
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]                                           # rag_learning/
TOOL = WS / "study" / "tools" / "proposition_fit_check.py"
EX = WS / "study" / "tools" / "examples"
UP = WS.parent / "upstream" / "RAG_Techniques"
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else UP / "data" / "Understanding_Climate_Change.pdf"
NB = Path(sys.argv[2]) if len(sys.argv) > 2 else UP / "all_rag_techniques" / "proposition_chunking.ipynb"
PROPS, PLANT, QFILE = EX / "climate_props.jsonl", HERE / "i4_planted_props.jsonl", EX / "climate_prop_questions.jsonl"
SEEDS = EX / "climate_seed_spans.jsonl"                        # byte copy of the 06 §6.7 block (P2)
REPORT, LABELS = EX / "climate_prop_report.md", EX / "climate_prop_labels.csv"
sys.path.insert(0, str(TOOL.parent))
import proposition_fit_check as pf                             # noqa: E402

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


def raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    except Exception:  # noqa: BLE001
        return False
    return False


V = lambda res, cid: next(i for i in res["checklist"] if i["id"] == cid)["verdict"]
E = lambda res, cid: next(i for i in res["checklist"] if i["id"] == cid)["evidence"]
verdicts = lambda res: " ".join(f"{i['id']}{i['verdict']}" for i in res["checklist"])
r3 = lambda x: None if x is None else round(x, 3)
TMP = Path(tempfile.mkdtemp(prefix="i4tool_"))

# ---------------------------------------------------------------- the kit measure, run in memory (its stdout discarded)
src = (HERE / "i4_kit_measure.py").read_text(encoding="utf-8")
G = {"__file__": str(HERE / "i4_kit_measure.py"), "__name__": "kit"}
argv = sys.argv
sys.argv = [str(HERE / "i4_kit_measure.py"), str(PDF), str(NB)]
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "i4_kit_measure", "exec"), G)
sys.argv = argv
KIT_OUT = (HERE / "out_i4_kit_measure.txt").read_text(encoding="utf-8")

# ================================================================ 1 parents
print("=== 1 parents: v0's 97 chunks (K1)")
docs = pf.load_documents([PDF])
ch = pf.make_chunks(docs)
check("1 v0 chunker: 97 chunks", len(ch), 97)
check("1 every chunk's offsets and text equal v0's (06 + 07 recipe)",
      [(c["start"], c["end"], c["text"]) for c in ch] == [(c["char_start"], c["char_end"], c["text"]) for c in G["chunks"]], True)
check("1 document: 33 pages, 72,593 characters", [len(docs[0]["pages"]), len(docs[0]["text"])], [33, 72593])
res_s = pf.run_check([PDF], props=PROPS, questions=SEEDS)
check("1 relevant chunks of the 8 answerable seeds equal K1", {q["id"]: q["rel_chunks"] for q in res_s["questions"] if q["rel_chunks"]},
      {"D-001": [7], "D-002": [27], "D-003": [68], "D-004": [23, 67, 68], "D-005": [3, 4], "D-006": [21], "D-007": [27, 85], "D-008": [69]})
check("1 the seeds' quotes match their offsets (no gold problem)", res_s["gold_problems"], [])
check("1 bad sizes raise", [raises(lambda: pf.make_chunks(docs, 100, 100), ValueError), raises(lambda: pf.make_chunks(docs, 0, 0), ValueError)], [True, True])

# ================================================================ 2 units
print("\n=== 2 units (K3)")
res = pf.run_check([PDF], props=PROPS, questions=QFILE, props_origin="hand")
U, units = res["unit_stats"], res["units"]
check("2 sentences, headings, units", [U["sentences"], U["headings"], U["units"]], [621, 286, 907])
check("2 sentences per page min / median / max; >= 4 words", [U["min"], U["median"], U["max"], U["words4"]], [6, 19, 22, 614])
check("2 every unit's offsets give back its text", U["spans_ok"], True)
kitU = G["UNITS"]
check("2 every unit equals the kit's (id, kind, doc offsets, text)",
      [(u["id"], u["kind"], u["da"], u["db"], u["text"]) for u in units.values()] == [(u["id"], u["kind"], u["da"], u["db"], u["text"]) for u in kitU.values()], True)
m = re.search(r"sentences per page: (\{[^}]+\})", KIT_OUT)
check("2 sentences per page equal the saved kit output", {r["page"]: r["s"] for r in res["page_rows"]} == {int(a): int(b) for a, b in re.findall(r"(\d+): (\d+)", m.group(1))}, True)
p10 = [u for u in units.values() if u["page"] == 10]
check("2 p.10: 16 sentences, 11 headings (10:0-10:26)", [sum(u["kind"] == "s" for u in p10), sum(u["kind"] == "h" for u in p10), p10[0]["id"], p10[-1]["id"]],
      [16, 11, "10:0", "10:26"])
check("2 splitter tests (1.5 degrees, pre-industrial, heading 10:6, 29:0 not a heading, market-\\nbased)",
      ["1.5 degrees Celsius." in units["10:7"]["text"], "pre-industrial" in units["10:7"]["text"],
       units["10:6"]["kind"] == "h" and units["10:6"]["text"] == "Paris Agreement", units["29:0"]["kind"] == "s", "market-\nbased" in units["29:2"]["text"]],
      [True] * 5)
check("2 known limits: 23:0 'resources.' is a page-start fragment; 0 'e.g.'", ["23:0" in res["limits"]["fragments"], units["23:0"]["text"], res["limits"]["eg"]],
      [True, "resources.", 0])

# ================================================================ 3 the tutor set
print("\n=== 3 the tutor set (K4; hand-written by the tutor, not LLM output)")
S = res["summary"]
check("3 40 propositions; by page 2:6, 10:25, 23:5, 29:4", [S["loaded"], dict(S["by_page"])], [40, {"2": 6, "10": 25, "23": 5, "29": 4}])
check("3 all ids exist, spans inside, one page", [S["valid"], S["bad_ids"], S["outside"], S["multi_page"]], [40, [], [], []])
check("3 resolved names: 15 uses, all earlier on the page", [S["resolved_uses"], S["resolved_bad"]], [15, []])
check("3 align = 1.000 for all 40; 0 pronoun-initial", [S["align_min"], S["flagged"], S["pronoun"]], [1.0, [], []])
check("3 parents: 40/40 contained; 34 with 1 parent, 6 with 2", [S["contained"], S["n_parents"][1], S["n_parents"][2]], [40, 34, 6])
check("3 1.54 propositions per source sentence (40 from 26)", [S["source_sentences"], round(S["per_sentence"], 2)], [26, 1.54])
check("3 every span and parent list equals the kit's", [(p["prop_id"], list(p["span"][1:]), p["parents"]) for p in res["props"]]
      == [(k, list(r["span"]), r["parents"]) for k, r in G["RT"].items()], True)
check("3 p10-08 and p23-02 share a normalised text (K4)", ["p10-08", "p23-02"] in S["dup_groups"], True)
check("3 all duplicate groups (the tool also finds p10-09 = p23-03)", S["dup_groups"], [["p10-08", "p23-02"], ["p10-09", "p23-03"]])
check("3 example verdicts", verdicts(res), "C1✓ C2? C3✓ C4✓ C5? C6✗ C7✓ C8✗ C9? C10✓ C11✓ C12?")
check("3 example recommendation: not decided yet", res["recommendation"].startswith("Not decided yet"), True)

# ================================================================ 4 planted mistakes
print("\n=== 4 planted mistakes (K5)")
rp = pf.run_check([PDF], props=PLANT)
P = {p["prop_id"]: p for p in rp["props"]}
check("4 align per planted proposition", [r3(P[x]["align"]) for x in ("x-01", "x-02", "x-03", "x-04", "x-05", "x-06")], [0.4, 0.75, 1.0, 1.0, 1.0, None])
check("4 unsupported words x-01, x-02", [P["x-01"]["unsupported"], P["x-02"]["unsupported"]], [["196", "countri", "sign"], ["2016"]])
check("4 equal to the kit's check_prop", [(r3(P[k]["align"]), P[k]["ids_ok"], P[k]["pronoun"]) for k in P] == [(r3(r["align"]), r["ids_ok"], r["pronoun"]) for r in G["RP"].values()], True)
check("4 flags: align < 1 = x-01, x-02; pronoun = x-05; bad id = x-06 (10:31)",
      [rp["summary"]["flagged"], rp["summary"]["pronoun"], rp["summary"]["bad_ids"], P["x-06"]["bad_ids"]], [["x-01", "x-02"], ["x-05"], ["x-06"], ["10:31"]])
check("4 x-03 and x-04 pass every code check", [P[x]["align"] == 1 and not P[x]["pronoun"] and P[x]["ids_ok"] for x in ("x-03", "x-04")], [True, True])
al, uns = pf.align_text("Neil Armstrong was an astronaut.", G["ex_doc"])
check("4 upstream astronaut proposition: align 0.667, unsupported 'astronaut'", [r3(al), uns], [0.667, ["astronaut"]])
check("4 planted checklist: C3 ✗ C4 ✗ C7 ✗", [V(rp, "C3"), V(rp, "C4"), V(rp, "C7")], ["✗", "✗", "✗"])
check("4 C4 lists x-01 0.400 and x-02 0.750 with their words", ["x-01 0.400 (196 countri sign)" in E(rp, "C4"), "x-02 0.750 (2016)" in E(rp, "C4")], [True, True])
check("4 recommendation: fix generation first (bad id)", rp["recommendation"].startswith("Fix generation"), True)
rp2 = pf.run_check([PDF], props=[json.loads(l) for l in PLANT.read_text(encoding="utf-8").splitlines() if l.strip() and "x-06" not in l])
check("4 without x-06: 2 of 5 below 1 -> propositions are rewriting facts", [V(rp2, "C3"), rp2["recommendation"].startswith("Propositions are rewriting facts")], ["✓", True])

# ================================================================ 5 coverage
print("\n=== 5 coverage (K6)")
SC = {"p.10": [u for u in units if units[u]["page"] == 10], "p.23 Paris": ["23:25", "23:26", "23:27"], "p.29 COP": ["29:12", "29:13", "29:14"],
      "p.2 coal and gas": ["2:0", "2:1", "2:2", "2:8", "2:9", "2:10"]}
cov = {k: pf.coverage(units, res["index"], ids) for k, ids in SC.items()}
check("5 sentence_coverage per scope: 16/16, 3/3, 3/3, 4/6", [f"{len(h)}/{len(h) + len(m_)}" for h, m_ in cov.values()], ["16/16", "3/3", "3/3", "4/6"])
check("5 uncovered on p.2: the methane and fracking sentences", cov["p.2 coal and gas"][1], ["2:9", "2:10"])
check("5 gold_reachability over the 8 answerable seeds: 6/12 = 0.500", [res_s["reach"], round(res_s["reach"][0] / res_s["reach"][1], 3)], [(6, 12), 0.5])
check("5 groups reachable per seed equal K6", {q["id"]: [any(g) for g in q["reach"]] for q in res_s["questions"] if q["reach"]},
      {"D-001": [False], "D-002": [True], "D-003": [True], "D-004": [False], "D-005": [True, True], "D-006": [False, False], "D-007": [True, True], "D-008": [False]})
check("5 the example questions (D-002, D-003, D-005, D-007): 6/6", res["reach"], (6, 6))
check("5 coverage on the example's 4 pages: 26/75 (pages written only in part)", res["coverage"]["total"], (26, 75))

# ================================================================ 6 the three scorings
print("\n=== 6 the three scorings on the kit's made-up orders (K7; NOT model output)")
pos = {p["prop_id"]: n for n, (p, r) in enumerate(res["index"])}
Q = {q["id"]: q for q in res["questions"]}
so = lambda qid, order: pf.score_order(res, Q[qid], [pos[x] for x in order], 4)
a = so("D-002", ["p10-08", "p23-02", "p10-07", "p10-10", "p23-01", "p10-09"])
check("6 D-002 arm (a): parents [27, 68], RR 1.000, 2 distinct parents in the top 4, CE@4 1",
      [a["parents"], a["rr_a"], a["top_parents"], a["ce_a"]], [[27, 68], 1.0, [27, 68], 1])
check("6 D-002 arm (b): RR 1.000, CE@4 1, distinct-facts@4 3; text check RR 0.333", [a["rr_b"], a["ce_b"], a["distinct_facts"], r3(a["rr_text"])], [1.0, 1, 3, 0.333])
a = so("D-007", ["p29-01", "p10-01", "p10-06", "p10-05", "p29-04", "p10-03"])
check("6 D-007 order 1: arm (a) [85, 27] CE@4 1; arm (b) CE@4 1; distinct-facts@4 4", [a["parents"], a["ce_a"], a["ce_b"], a["distinct_facts"]], [[85, 27], 1, 1, 4])
a = so("D-007", ["p29-01", "p10-01", "p10-06", "p29-04", "p10-05", "p10-03"])
check("6 D-007 with p10-05 at rank 5: arm (a) CE@4 still 1, arm (b) CE@4 0", [a["ce_a"], a["ce_b"]], [1, 0])
a = so("D-005", ["p02-01", "p02-02", "p02-04", "p02-03", "p02-05", "p02-06"])
check("6 D-005: arm (a) 1 distinct parent [3], CE@4 1; arm (b) CE@4 0; RR 1 / 1", [a["top_parents"], a["ce_a"], a["ce_b"], a["rr_a"], a["rr_b"]], [[3], 1, 0, 1.0, 1.0])

# ================================================================ 7 forecast
print("\n=== 7 forecast (K9; per-call tokens ASSUMED)")
F = res["forecast"]
check("7 621 sentences -> about 1,400 propositions (Dense X), about 955 (tutor ratio)", [F["sentences"], F["p_est"], F["p_file"]], [621, 1400, 955])
row = lambda r: [r["calls"], r["tokens"], round(r["usd"], 3), round(r["days"], 2), round(r["minutes"])]
check("7 Corpus D grading off: 33 calls, 87,450 tokens, $0.018, 0.44 days, 11 min", row(F["rows"]["off"]), [33, 87450, 0.018, 0.44, 11])
check("7 Corpus D batched: 66 calls, 199,650 tokens, $0.039, 1.00 day, 25 min", row(F["rows"]["batched"]), [66, 199650, 0.039, 1.0, 25])
check("7 Corpus D per-proposition: 1,433 calls, 1,725,450 tokens, $0.236, 8.63 days, 216 min", row(F["rows"]["per-prop"]), [1433, 1725450, 0.236, 8.63, 216])
sub = round(F["p_est"] * 5 / 33)
check("7 subset 5 pages (about 212 propositions): off / batched / per-prop",
      [sub, row(pf.forecast(5, sub, "off")), row(pf.forecast(5, sub, "batched")), row(pf.forecast(5, sub, "per_prop"))],
      [212, [5, 13250, 0.003, 0.07, 2], [10, 30250, 0.006, 0.15, 4], [217, 261290, 0.036, 1.31, 33]])
check("7 index KiB: MiniLM 146 -> 2,100; Cohere 582 -> 8,400; x14.4", [[round(r["chunks_kib"]), round(r["props_kib"])] for r in F["index"]] + [round(F["x"], 1)],
      [[146, 2100], [582, 8400], 14.4])
check("7 cost per 1k chunks: $0.19 / $0.40 (680 calls) / $2.43 (14,773 calls)",
      [round(F["per_1k"][g]["usd"], 2) for g in pf.GRADINGS] + [round(F["per_1k"]["batched"]["calls"]), round(F["per_1k"]["per-prop"]["calls"])],
      [0.19, 0.40, 2.43, 680, 14773])
check("7 page tokens (DERIVED): mean 389, p.10 367", [round(F["mean_page_tokens"]), round(len(docs[0]["pages"][9]) * pf.TOK_PER_CHAR)], [389, 367])
check("7 C1: batched fits the quota; per-prop does not; a $0.01 budget fails",
      [V(res, "C1"), V(pf.run_check([PDF], grading="per-prop"), "C1"), V(pf.run_check([PDF], budget_usd=0.01), "C1")], ["✓", "✗", "✗"])
check("7 default sample pages 1, 17, 33; --pages 10,23", [[r["key"] for r in F["sample"]], [r["key"] for r in pf.run_check([PDF], pages="10,23")["forecast"]["sample"]]],
      [["1", "17", "33"], ["10", "23"]])

# ================================================================ 8 prompt and leakage
print("\n=== 8 prompt prop_gen_v1 and the 8-gram leakage test (K10)")
pfile = (HERE / "prop_gen_v1.txt").read_text(encoding="utf-8")
check("8 built-in prompt = the frozen file (1,506 chars, sha256 bdff5976...)",
      [pf.PROMPT_V1 == pfile, len(pf.PROMPT_V1), hashlib.sha256(pf.PROMPT_V1.encode("utf-8")).hexdigest()[:8]], [True, 1506, "bdff5976"])
r10 = pf.render_prompt(units, docs, 0, 10)
check("8 rendered p.10: 3,858 chars, about 682 tokens; equal to the kit's render(10)", [len(r10), round(len(r10) * pf.TOK_PER_CHAR), r10 == G["render"](10)], [3858, 682, True])
check("8 first three unit lines", r10.split("Page:\n")[1].splitlines()[:3],
      ["[10:0] (heading) Chapter 6: Global and Local Climate Action", "[10:1] (heading) International Collaboration",
       "[10:2] (heading) United Nations Framework Convention on Climate Change (UNFCCC)"])
seeds_q = pf.load_questions(SEEDS)
tx = pf.eval_texts(seeds_q)
ex = pf.prompt_example_part(pf.PROMPT_V1)
lk = pf.leakage(ex, tx)
check("8 eval texts 22 (10 questions + 12 quotes), 172 distinct 8-grams, clean: 0 shared", [len(tx), lk["eval_ngrams"], len(lk["shared"])], [22, 172, 0])
leaky = ex.replace("The town library opened in 1998.", "The Paris Agreement, adopted in 2015, aims to limit global warming to well below 2 degrees Celsius.")
check("8 injected leak: 10 shared 8-grams", len(pf.leakage(leaky, tx)["shared"]), 10)
rl = pf.run_check([PDF], questions=SEEDS, prompt=pf.PROMPT_V1.replace("The town library opened in 1998.", "The Paris Agreement, adopted in 2015, aims to limit global warming to well below 2 degrees Celsius."))
check("8 a leaky template fails C10; the built-in one passes", [V(rl, "C10"), V(res_s, "C10")], ["✗", "✓"])

# ================================================================ 9 Wilson
print("\n=== 9 Wilson (K11)")
check("9 27/30, 54/60, 51/60, 57/60", [[r3(x) for x in pf.wilson(a_, n)] for a_, n in ((27, 30), (54, 60), (51, 60), (57, 60))],
      [[0.744, 0.965], [0.799, 0.953], [0.739, 0.919], [0.863, 0.983]])

# ================================================================ 10 inputs
print("\n=== 10 inputs")
t1 = TMP / "alpha.txt"
t1.write_text("Rivers\nThe Venn river floods each spring. It carries silt to the plain.\n", encoding="utf-8")
t2 = TMP / "beta.md"
t2.write_text("The Dart valley is narrow. Its slopes are steep.\n", encoding="utf-8")
r1 = pf.run_check([t1], props=[{"prop_id": "a", "text": "The Venn river floods each spring.", "source_ids": ["1:1"]}])
check("10 a text file is one page: ids 1:i (heading 1:0)", [list(r1["units"]), r1["units"]["1:0"]["kind"], r1["summary"]["valid"]], [["1:0", "1:1", "1:2"], "h", 1])
r2 = pf.run_check([t1, t2], props=[{"prop_id": "a", "text": "The Venn river carries silt to the plain.", "source_ids": ["alpha#1:2"], "resolved": ["Venn river"]},
                                   {"prop_id": "b", "text": "The Dart valley is narrow.", "source_ids": ["1:0"]}],
                   questions=[{"q": "What does the Venn carry?", "gold": [{"group_id": "g1", "alternatives": [{"alt_id": "a", "segments":
                               [{"doc_id": "alpha", "page": 1, "char_start": 44, "char_end": 72}]}]}]}])
check("10 several documents: ids stem#page:i; a bare id is a bad id; gold by stem",
      [list(r2["units"])[:2], r2["summary"]["bad_ids"], r2["props"][0]["align"], r2["questions"][0]["rel_chunks"]], [["alpha#1:0", "alpha#1:1"], ["b"], 1.0, [0]])
(TMP / "bad.jsonl").write_text('{"prop_id": "a", "text": "The Venn river floods each spring.", "source_ids": ["1:1"]}\nnot json\n'
                               '{"prop_id": "b", "source_ids": ["1:1"]}\n{"prop_id": "a", "text": "x", "source_ids": ["1:1"]}\n'
                               '{"prop_id": "c", "text": "y", "source_ids": "1:1"}\n', encoding="utf-8")
rb = pf.run_check([t1], props=TMP / "bad.jsonl")
check("10 invalid records are logged and left out: 4 of 5; C2 ✗; fix generation",
      [len(rb["prop_problems"]), rb["summary"]["loaded"], V(rb, "C2"), rb["recommendation"].startswith("Fix generation")], [4, 1, "✗", True])
check("10 the problems name the record", [x.split(":")[0] for x in rb["prop_problems"]], ["record 2", "record 3 (b)", "record 4 (a)", "record 5 (c)"])
rq = pf.load_questions(SEEDS)
check("10 the 06 question form is read (qid, question, category, evidence_groups, answerable)",
      [rq[1]["id"], rq[1]["type"], len(rq[1]["gold"]), rq[8]["answerable"], rq[1]["created_by"]], ["D-002", "factual-single-span", 1, False, "llm-draft"])
rpg = pf.run_check([PDF], props=[{"prop_id": "a", "page": 9, "text": "The Paris Agreement was adopted in 2015.", "source_ids": ["10:7"]}])
check("10 a page field that disagrees with its units fails C3", [rpg["summary"]["page_mismatch"], V(rpg, "C3")], [["a"], "✗"])
rr = pf.run_check([PDF], props=[{"prop_id": "a", "text": "The Montreal Protocol aims to limit global warming.", "source_ids": ["10:7"], "resolved": ["Montreal Protocol"]}])
check("10 a resolved name not earlier on the page is rejected (its words count as unsupported)",
      [rr["summary"]["resolved_bad"], rr["props"][0]["unsupported"], "NOT found" in E(rr, "C7")], [["a"], ["montreal", "protocol"], True])
(TMP / "x.docx").write_text("x", encoding="utf-8")
(TMP / "bq.jsonl").write_text("nope\n", encoding="utf-8")
(TMP / "sub").mkdir()
(TMP / "sub" / "alpha.md").write_text("x", encoding="utf-8")
check("10 errors: file type, missing path, bad JSON questions, missing q, two equal stems, bad page, bad grading",
      [raises(lambda: pf.load_documents([TMP / "x.docx"]), ValueError), raises(lambda: pf.load_documents([TMP / "nope.pdf"]), FileNotFoundError),
       raises(lambda: pf.load_questions(TMP / "bq.jsonl"), ValueError), raises(lambda: pf.load_questions([{"expect": "x"}]), ValueError),
       raises(lambda: pf.load_documents([t1, TMP / "sub" / "alpha.md"]), ValueError),
       raises(lambda: pf.run_check([PDF], pages="40"), ValueError), raises(lambda: pf.run_check([PDF], grading="all"), ValueError)], [True] * 7)

# ================================================================ 11 labelling sheet
print("\n=== 11 labelling sheet (C5) and the filter (C9)")
sheet = pf.labels_csv(res)
lines = sheet.splitlines()
check("11 header and one row per proposition", [lines[0], len(lines)], ["prop_id,page,source_ids,source_text,proposition,align,unsupported,label,note", 41])
check("11 p10-03 row: the source sentence with its pronoun, the proposition, align 1.000",
      lines[3], 'p10-03,10,10:4,"It provides a framework for negotiating specific protocols and agreements, such as the Kyoto Protocol and the Paris Agreement.",'
                "The UNFCCC provides a framework for negotiating specific protocols and agreements.,1.000,,,")
filled = TMP / "labels.csv"
rows = sheet.splitlines()
filled.write_text("\n".join([rows[0]] + [r[:-1] + ("added,x" if n < 2 else "supported,") for n, r in enumerate(rows[1:31])] + rows[31:]) + "\n", encoding="utf-8")
rlab = pf.run_check([PDF], props=PROPS, labels=filled)
check("11 28/30 supported read back: Wilson lower 0.787 < 0.85 -> C5 ✗, rewriting facts",
      [rlab["labels"]["n"], rlab["labels"]["supported"], r3(rlab["labels"]["wilson"][0]), V(rlab, "C5"), rlab["recommendation"].startswith("Propositions are rewriting")],
      [30, 28, 0.787, "✗", True])
rall = pf.run_check([PDF], props=PROPS, labels={p["prop_id"]: "supported" for p in res["props"]})
check("11 40/40 supported: Wilson lower 0.912 -> C5 ✓", [r3(rall["labels"]["wilson"][0]), V(rall, "C5")], [0.912, "✓"])
check("11 fewer than 30 labels: C5 ?", V(pf.run_check([PDF], props=PROPS, labels={"p10-01": "supported"}), "C5"), "?")
kp = [dict(json.loads(l), kept=k) for l, k in zip(PROPS.read_text(encoding="utf-8").splitlines()[:6], (True, True, True, False, True, False))]
rk = pf.run_check([PDF], props=kp, labels={"p10-01": "supported", "p10-02": "supported", "p10-03": "added", "p10-04": "added", "p10-05": "supported",
                                           "p10-06": "distorted", "nope": "supported", "p10-07": "maybe"})
f = rk["labels"]["filter"]
check("11 keep-good 3/3, catch-bad 2/3 with n = 6; C9 ✓", [f["n"], r3(f["keep_good"]), r3(f["catch_bad"]), V(rk, "C9")], [6, 1.0, 0.667, "✓"])
check("11 unknown label value and unknown prop_id are reported", len(rk["label_problems"]), 2)
check("11 dropped propositions are not indexed (coverage counts kept ones)", [rk["summary"]["indexed"], rk["coverage"]["total"]], [4, (2, 16)])
check("11 grading off: C9 ✓ (no filter)", V(pf.run_check([PDF], props=PROPS, grading="off"), "C9"), "✓")

# ================================================================ 12 recommendation branches
print("\n=== 12 recommendation branches (made-up documents; a word-count embedder stands in for MiniLM)")
TOWNS = ["Tolbar", "Kelso", "Arden", "Brisk", "Corvo", "Dunmore", "Elgin", "Fenwick", "Galt", "Halden", "Iver", "Jarrow"]
ATTR = ["harbour", "bridge", "library", "museum", "school", "tower", "market", "station", "theatre", "chapel", "mill", "park"]
FILL = ("Visitors often walk along the narrow streets and stop at small cafes near the old square in the evening. "
        "Local guides describe the long history of the region in friendly talks that last most of the afternoon.")


def toy_embed(texts):
    M = np.zeros((len(texts), 512))
    for i, t in enumerate(texts):
        for w in pf.words(t):
            M[i, int(hashlib.sha256(w.encode()).hexdigest(), 16) % 512] += 1
    return M


def towns(distract):
    f_ = TMP / f"towns_{int(distract)}.txt"
    paras = []
    for i, (t, a_) in enumerate(zip(TOWNS, ATTR)):
        paras.append(f"The {a_} of {t} opened in {1901 + i}. " + FILL)
        if distract:
            paras.append(f"{t} {a_} tours run daily.")            # a short distractor chunk with the question's words
    f_.write_text("\n\n".join(paras) + "\n", encoding="utf-8")
    us = pf.make_units(pf.load_documents([f_]))
    props = [{"prop_id": f"t{n}", "text": u["text"], "source_ids": [u["id"]]} for n, u in enumerate(us.values()) if "tours" not in u["text"]]
    return f_, props


QS = [{"id": f"q{i}", "q": f"When did the {a_} of {t} open?", "expect": [str(1901 + i)], "type": "factual"} for i, (t, a_) in enumerate(zip(TOWNS, ATTR))]
fd, pd_ = towns(True)
fn_, pn_ = towns(False)
ALL = lambda ps: {p["prop_id"]: "supported" for p in ps}
run = lambda f_, ps, **kw: pf.run_check([f_], props=ps, questions=kw.pop("qs", QS), dense=True, embedder=toy_embed, chunk_size=260, overlap=0, **kw)
r_adopt = run(fd, pd_, labels=ALL(pd_))
sm = r_adopt["dense"]["summary"]
check("12 adopt: 24 chunks, 36 propositions; arm (a) MRR@10 1.000 beats the chunks 0.500 (the short distractor chunks win there)",
      [len(r_adopt["chunks"]), r_adopt["summary"]["valid"], sm["mrr_a"], sm["mrr_chunks"], sm["improved"]], [24, 36, 1.0, 0.5, True])
check("12 adopt: recommendation", r_adopt["recommendation"].startswith("Adopt as a multi-vector index"), True)
r_none = run(fn_, pn_, labels=ALL(pn_))
check("12 no gain: chunks and arm (a) both 1.000 -> keep chunks, inconclusive", [r_none["dense"]["summary"]["mrr_chunks"], r_none["dense"]["summary"]["mrr_a"],
                                                                                 r_none["recommendation"].startswith("No gain measured")], [1.0, 1.0, True])
r_cost = run(fn_, pn_, labels=ALL(pn_), budget_usd=0.0)
check("12 no gain and over budget: not worth the index cost", [V(r_cost, "C1"), r_cost["recommendation"].startswith("Not worth the index cost")], ["✗", True])
r_und = run(fd, pd_)
check("12 no labels: not decided yet (C5)", [V(r_und, "C5"), r_und["recommendation"].startswith("Not decided yet: label at least 30")], ["?", True])
r_few = run(fd, pd_, labels=ALL(pd_), qs=QS[:4])
check("12 4 labelled questions: not decided yet (ranking)", r_few["recommendation"].startswith("Not decided yet: run --dense with at least 10"), True)
r_rel = run(fd, pd_, labels=ALL(pd_), qs=[dict(q, type="multi-hop") for q in QS[:7]] + QS[7:])
check("12 7 of 12 questions multi-hop: C11 ✗, keep chunks", [V(r_rel, "C11"), r_rel["recommendation"].startswith("Keep chunks")], ["✗", True])
r_kw = pf.run_check([fd], questions=[{"q": "Compare the harbour of Tolbar and the bridge of Kelso"}, {"q": "When did the mill open?"}])
check("12 the wording heuristic: 'Compare' is a relation question, a plain lookup is not", [q["relation"] for q in r_kw["questions"]], [True, False])
r_bad = run(fd, pd_, labels={p["prop_id"]: ("added" if n < 4 else "supported") for n, p in enumerate(pd_)})
check("12 32/36 supported (Wilson lower < 0.85): rewriting facts", [r3(r_bad["labels"]["wilson"][0]), r_bad["recommendation"].startswith("Propositions are rewriting")],
      [0.747, True])
rep_d = pf.render_report(r_adopt)
check("12 the report shows section 6 with the ranking table", ["| q0 | 0.500 / - | 1.000 / - (4) |" in rep_d, "Arm (a) beats the plain chunks" in rep_d], [True, True])
base_cl = {f"C{i}": "✓" for i in range(1, 13)}
fake = lambda summ=None, flagged=0, **kw: {"checklist": [{"id": k, "verdict": v} for k, v in {**base_cl, **kw}.items()],
                                           "summary": {"valid": 10, "flagged": ["x"] * flagged}, "labels": None,
                                           "dense": {"summary": summ}}
GAIN, NOGAIN = {"n": 12, "improved": True}, {"n": 12, "improved": False}
order = [pf.recommend(fake(GAIN, C3="✗", C5="✗")).startswith("Fix"), pf.recommend(fake(GAIN, C2="✗")).startswith("Fix"),
         pf.recommend(fake(GAIN, C5="✗", C11="✗")).startswith("Propositions"), pf.recommend(fake(GAIN, flagged=1, C11="✗")).startswith("Propositions"),
         pf.recommend(fake(NOGAIN, C11="✗", C1="✗")).startswith("Keep chunks"), pf.recommend(fake(NOGAIN, C1="✗", C5="?")).startswith("Not worth"),
         pf.recommend(fake(GAIN, C5="?")).startswith("Not decided"), pf.recommend(fake(None)).startswith("Not decided"),
         pf.recommend(fake(NOGAIN)).startswith("No gain"), pf.recommend(fake(GAIN, C6="✗", C8="✗")).startswith("Adopt")]
check("12 rule order: C2/C3 > C5/C4 > C11 > no gain + C1 > not decided > no gain > adopt", order, [True] * 10)

# ================================================================ 13 dense
print("\n=== 13 --dense")
has_st = importlib.util.find_spec("sentence_transformers") is not None
rd = pf.run_check([PDF], props=PROPS, questions=QFILE, dense=True)
if has_st:
    check("13 sentence-transformers is installed: --dense ran or names the missing model (observation, not a K value)",
          rd["dense"]["status"].startswith(pf.MINILM) or "local Hugging Face cache" in rd["dense"]["status"], True)
else:
    check("13 sentence-transformers missing: --dense is SKIPPED with a reason; section 6 says so",
          [rd["dense"]["status"], rd["dense"]["status"] in pf.render_report(rd)],
          ["SKIPPED (sentence-transformers is not installed; section 6 needs --dense with a local MiniLM)", True])
    cp = subprocess.run([sys.executable, str(TOOL), "--docs", str(t1), "--dense"], capture_output=True, text=True, encoding="utf-8",
                        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    check("13 the CLI exits 0 and prints the skip on stderr", [cp.returncode, "SKIPPED" in cp.stderr], [0, True])

# ================================================================ 14 CLI
print("\n=== 14 CLI, saved examples, refusals, no network")
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
args = [sys.executable, str(TOOL), "--docs", str(PDF), "--props", str(PROPS), "--props-origin", "hand", "--questions", str(QFILE)]
outs = []
for n in (1, 2):
    o, l_ = TMP / f"r{n}.md", TMP / f"l{n}.csv"
    cp = subprocess.run(args + ["--report", str(o), "--labels-csv", str(l_)], capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(WS))
    outs.append((cp.returncode, o.read_bytes() if o.exists() else b"", l_.read_bytes() if l_.exists() else b""))
check("14 the CLI exits 0 and equals the saved example report", [outs[0][0], outs[0][1] == REPORT.read_bytes()], [0, True])
check("14 the labelling sheet equals the saved example sheet", outs[0][2] == LABELS.read_bytes(), True)
check("14 a second run is byte-identical (report and sheet)", [outs[0][1] == outs[1][1], outs[0][2] == outs[1][2]], [True, True])
check("14 the saved report equals render_report(run_check(...)); the sheet equals labels_csv",
      [REPORT.read_text(encoding="utf-8") == pf.render_report(res), LABELS.read_text(encoding="utf-8-sig") == sheet], [True, True])
rep = REPORT.read_text(encoding="utf-8")
check("14 the report has the 8 parts", [f"## {n} " in rep for n in range(1, 9)], [True] * 8)
check("14 the report says the propositions are hand-written and section 6 needs --dense",
      ["hand-written (not LLM output)" in rep, "needs `--dense`" in rep, "`created_by: llm-draft`" in rep, "**ASSUMED**" in rep], [True] * 4)
for prov in ("groq", "anthropic"):
    cp = subprocess.run([sys.executable, str(TOOL), "--docs", str(t1), "--provider", prov], capture_output=True, text=True, encoding="utf-8", env=env)
    check(f"14 --provider {prov} refuses (exit 2) and names the missing study/llmops cache", [cp.returncode, "study/llmops" in cp.stderr, cp.stdout], [2, True, ""])
cp = subprocess.run([sys.executable, str(TOOL), "--docs", str(PDF), "--render-prompt", "10"], capture_output=True, text=True, encoding="utf-8", env=env)
check("14 --render-prompt 10 prints the kit's rendered p.10 prompt", [cp.returncode, cp.stdout == G["render"](10)], [0, True])
tsrc = TOOL.read_text(encoding="utf-8")
check("14 the tool imports no network or API client", [w for w in ("requests", "urllib", "http", "groq", "cohere", "anthropic", "langsmith", "dotenv", "openai", "socket")
                                                       if re.search(rf"^\s*(import|from)\s+{re.escape(w)}", tsrc, re.M)], [])
check("14 the tool imports nothing from sources/ (standalone)", [bool(re.search(r"^\s*(import|from)\s+(contracts_check|i4_kit_measure)", tsrc, re.M)), "sys.path.insert" in tsrc], [False, False])
check("14 the tool forces the offline Hugging Face mode", 'os.environ.setdefault("HF_HUB_OFFLINE", "1")' in tsrc, True)
check("14 climate_props.jsonl is a byte copy of i4_tutor_props.jsonl", PROPS.read_bytes() == (HERE / "i4_tutor_props.jsonl").read_bytes(), True)
BANNED_REV = ["syas ediug a", "orez evoba llew", "dnab evitisop worran", "thgir si ohw", "htxis", "fdp a dda", "tnemucod a gnidda",
              "tnemucod wen", "fdp rehtona", "tnanet", "fdp 003"]           # the coach-banned phrases, reversed so this file holds none
banned = [b[::-1] for b in BANNED_REV]
texts = {p.name: p.read_text(encoding="utf-8-sig").lower() for p in (TOOL, REPORT, LABELS, QFILE, PROPS, Path(__file__))}
check("14 no coach-banned phrase in the tool, the examples or this test", [f"{n}: {b}" for n, t in texts.items() for b in banned if b in t], [])

shutil.rmtree(TMP, ignore_errors=True)
n_ok = sum(ok for _, ok in RESULTS)
print(f"\n{n_ok}/{len(RESULTS)} tool checks passed")
sys.exit(0 if n_ok == len(RESULTS) else 1)
