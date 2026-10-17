"""Test study/tools/bm25_fit_check.py: the climate run against P3_FACTS, plus three small cases.

1. Climate PDF, 1000/200 windows (= P3's 91 windows), tokenizer norm: collection numbers (S10, K1, K8, the valley of
   §7), the labelled ranks under norm and split (S9), the BECCS / IPCC / vague question details (K2, K3, K7). The
   same run with split: zero-score warning and the argsort fallback (S9), C2 fails, "fix the tokenizer first". The
   CLI writes a report with the FACTS numbers.
2. A small identifier text with getUserId get_user_id ERR_CONN_RESET v2.10.3: the audit flags what norm cuts.
3. A two-document corpus: C5 fails with the negative-floor reason; the floor is K9's -0.080472.
4. An all-zero question on the climate PDF: the zero-score warning, the fallback chunks, C7 fails.

No API calls, no dense model (the dense path is exercised by the example report run). Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_tool_test.py ["<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"]
"""
import math
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]                                           # rag_learning/
TOOL = WS / "study" / "tools" / "bm25_fit_check.py"
QUESTIONS = WS / "study" / "tools" / "examples" / "climate_questions.jsonl"
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
sys.path.insert(0, str(TOOL.parent))
import bm25_fit_check as fc                                   # noqa: E402

RESULTS = []
T6, T4 = 5e-7, 5e-5


def same(got, exp, tol):
    if isinstance(exp, (list, tuple)):
        return isinstance(got, (list, tuple)) and len(got) == len(exp) and all(same(g, e, tol) for g, e in zip(got, exp))
    if exp is None or isinstance(exp, (str, bool)) or got is None:
        return got == exp
    return abs(float(got) - float(exp)) <= tol


def check(name, got, exp, tol=0.0):
    ok = same(got, exp, tol)
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got!r} | expected {exp!r}")
    return ok


verdict = lambda res, cid: next(i for i in res["checklist"] if i["id"] == cid)

# ================================================================ 1 the climate run (FACTS)
print("=== 1 climate PDF, tokenizer norm (P3_FACTS)")
res = fc.run_check([PDF], QUESTIONS, tokenizer="norm", k=4)
col = res["collection"]
check("1 chunks N (91 windows)", col["N"], 91)
check("1 avgdl (S10: 129.67)", round(col["avgdl"], 2), 129.67)
check("1 vocabulary (S10)", col["vocab"], 1870)
check("1 mean idf (S10)", col["mean_idf"], 3.352948, T6)
check("1 floor (S10, K1)", col["floor"], 0.838237, T6)
check("1 floored words (S10: 18)", len(col["floored"]), 18)
check("1 the valley n = 28 to 45 (lesson §7)", list(col["valley_n"]), [28, 45])
check("1 once-only tokens, doubled, % (K8)", [col["once"], col["doubled"], round(col["pct_doubled"], 1)], [799, 184, 23.0])
check("1 fragments (K8)", col["fragments"], 101)
rows = {r["id"]: r for r in res["measuring"]["rows"]}
ids5 = ["IPCC", "BECCS", "CH4", "Kyoto", "1.5C"]
check("1 right chunks = S9 target windows", [rows[i]["targets"] for i in ids5],
      [["#1"], ["#82", "#83"], ["#2"], ["#64"], ["#26", "#63", "#64"]])
check("1 ranks under norm (S9: all 1)", [rows[i]["rank_norm"] for i in ids5], [1, 1, 1, 1, 1])
check("1 ranks under split (S9: none, none, 3, 1, 1)", [rows[i]["rank_split"] for i in ids5], [None, None, 3, 1, 1])
q = {x["id"]: x for x in res["questions"]}
b = q["BECCS"]
check("1 BECCS: windows above 0 (K2)", b["n_pos"], 80)
check("1 BECCS: top 4 chunks (K2)", [t["chunk"] for t in b["top"]], ["#83", "#82", "#16", "#53"])
check("1 BECCS: top 4 scores (K2)", [t["score"] for t in b["top"]], [5.0623, 4.8803, 1.672, 1.6156], T4)
check("1 BECCS: not in the index (K2)", b["unknown"], ["what", "does", "stand"])
check("1 BECCS: rarest token and idf (K2)", [b["rarest"], b["idf"]["beccs"]], ["beccs", 3.577948], T6)
check("1 BECCS: matches through 'for' only (lesson §8: 78)", b["weak_only"], 78)
check("1 BECCS: page of window 83", b["top"][0]["page"], 30)
check("1 IPCC: window 1 at 3.892792 (K3)", [q["IPCC"]["top"][0]["chunk"], q["IPCC"]["top"][0]["score"]], ["#1", 3.892792], T6)
v = q["vague"]
check("1 vague: windows above 0, top score (K7)", [v["n_pos"], v["top_score"]], [81, 5.7608], T4)
check("1 vague: not in the index; vague warning (K7)", [v["unknown"], v["vague"]], [["what", "done"], True])
check("1 C2 and C5 pass under norm", [verdict(res, "C2")["verdict"], verdict(res, "C5")["verdict"]], [fc.OK, fc.OK])
check("1 C6 fails on the vague question", verdict(res, "C6")["verdict"], fc.BAD)
report = fc.render_report(res)
check("1 the report shows the FACTS numbers", all(s in report for s in ("| Chunks N | 91 |", "129.67 tokens", "0.838237",
                                                                         "n = 28 to 45", "184 of 799 (23.0%)")), True)

print("\n=== 1b the same with split()")
res_s = fc.run_check([PDF], QUESTIONS, tokenizer="split", k=4)
qs = {x["id"]: x for x in res_s["questions"]}
check("1b IPCC and BECCS: zero-score (S9: 0 windows above 0)", [qs["IPCC"]["zero"], qs["BECCS"]["zero"]], [True, True])
check("1b the argsort fallback (S9: [90, 89, 88, 87, 86], first 4)", qs["IPCC"]["fallback"], ["#90", "#89", "#88", "#87"])
check("1b CH4 under split: windows above 0 (S9: 3)", qs["CH4"]["n_pos"], 3)
check("1b C2 fails under split", verdict(res_s, "C2")["verdict"], fc.BAD)
check("1b recommendation", res_s["recommendation"]["verdict"], "fix the tokenizer first")
aud = {r["ident"]: r for r in res_s["audit"]["rows"]}
check("1b audit: the forms of IPCC and BECCS under split (S9)", [list(aud["IPCC"]["forms"]), list(aud["BECCS"]["forms"])],
      [["(IPCC)"], ["(BECCS),"]])

print("\n=== 1c the command line")
with tempfile.TemporaryDirectory(prefix="p3_tool_") as tmp:
    out = Path(tmp) / "report.md"
    r = subprocess.run([sys.executable, str(TOOL), "--docs", str(PDF), "--questions", str(QUESTIONS), "--report", str(out)],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(WS))
    check("1c exit code", r.returncode, 0)
    text = out.read_text(encoding="utf-8") if out.exists() else ""
    check("1c the CLI report = the imported report", text == report, True)
    check("1c stdout summary", "chunks 91, avgdl 129.67, floor 0.838237" in r.stdout, True)

# ================================================================ 2 identifiers
print("\n=== 2 identifier text")
with tempfile.TemporaryDirectory(prefix="p3_tool_") as tmp:
    f = Path(tmp) / "identifiers.txt"
    f.write_text("Call getUserId and get_user_id first.\nIf you see ERR_CONN_RESET, upgrade to v2.10.3 and retry.\n"
                 "getUserId(token) returns an int; get_user_id(session) too.\n", encoding="utf-8")
    res_i = fc.run_check([f], None, identifiers=["getOrderId"], tokenizer="norm")
aud = {r["ident"]: r for r in res_i["audit"]["rows"]}
check("2 classes", [aud[k]["class"] for k in ("getUserId", "get_user_id", "ERR_CONN_RESET", "v2.10.3", "getOrderId")],
      ["CamelCase", "snake_case", "snake_case", "version", "given"])
check("2 norm tokens (S7: ERR_CONN_RESET -> err, conn, reset; v2.10.3 whole)",
      [aud[k]["tokens"]["norm"] for k in ("getUserId", "get_user_id", "ERR_CONN_RESET", "v2.10.3")],
      [["getuserid"], ["get", "user", "id"], ["err", "conn", "reset"], ["v2.10.3"]])
check("2 norm flags: cut apart for get_user_id and ERR_CONN_RESET only",
      [aud[k]["flags"]["norm"] for k in ("getUserId", "get_user_id", "ERR_CONN_RESET", "v2.10.3")],
      [[], ["cut apart"], ["cut apart"], []])
check("2 code tokens of getUserId (the lesson's tokCode: parts + whole)", aud["getUserId"]["tokens"]["code"],
      ["get", "user", "id", "getuserid"])
check("2 code flags: getUserId case split (whole kept); v2.10.3 whole, no flag",
      [aud["getUserId"]["flags"]["code"], aud["v2.10.3"]["flags"]["code"]], [["case split, whole name kept"], []])
check("2 code keeps v2.10.3 and 1.5 whole; getUserId -> parts + whole; ERR_CONN_RESET -> parts + whole (lesson tokCode)",
      [fc.tok_code("v2.10.3"), fc.tok_code("1.5"), fc.tok_code("getUserId"), fc.tok_code("ERR_CONN_RESET")],
      [["v2.10.3"], ["1.5"], ["get", "user", "id", "getuserid"], ["err", "conn", "reset", "err_conn_reset"]])
check("2 split flags: ERR_CONN_RESET has a comma attached once", aud["ERR_CONN_RESET"]["ok"]["split"], False)
check("2 the given name is not in the text", aud["getOrderId"]["count"], 0)
c2 = verdict(res_i, "C2")
check("2 C2 fails under norm and names both", [c2["verdict"], "`get_user_id`" in c2["evidence"],
                                                 "`ERR_CONN_RESET`" in c2["evidence"]], [fc.BAD, True, True])
check("2 the report flags them", fc.render_report(res_i).count("✗ `err` · `conn` · `reset`"), 1)

# ================================================================ 3 two documents
print("\n=== 3 two-document corpus")
with tempfile.TemporaryDirectory(prefix="p3_tool_") as tmp:
    a, bb = Path(tmp) / "a.txt", Path(tmp) / "b.txt"
    a.write_text("BPA ban the", encoding="utf-8")
    bb.write_text("Climate policy the", encoding="utf-8")
    res_2 = fc.run_check([a, bb], [{"q": "the"}, {"q": "bpa"}], tokenizer="norm")
col2 = res_2["collection"]
check("3 chunks N", col2["N"], 2)
check("3 floor (K9: -0.080472)", col2["floor"], -0.080472, T6)
c5 = verdict(res_2, "C5")
check("3 C5 fails, with the negative-floor reason", [c5["verdict"], "negative floor" in c5["evidence"], "-0.080472" in c5["evidence"]],
      [fc.BAD, True, True])
q2 = {x["q"]: x for x in res_2["questions"]}
check("3 'the' scores -0.080472 in both: zero-score warning", q2["the"]["zero"], True)
check("3 'bpa' has idf 0 (K9): zero-score warning", [q2["bpa"]["idf"]["bpa"], q2["bpa"]["zero"]], [0.0, True])
check("3 recommendation", res_2["recommendation"]["verdict"], "not enough data to judge")

# ================================================================ 4 all-zero question
print("\n=== 4 an all-zero question on the climate PDF")
res_z = fc.run_check([PDF], [{"q": "zzzz qqqq", "id": "Z"}], tokenizer="norm", k=4)
z = res_z["questions"][0]
check("4 no token in the index, zero-score", [z["unknown"], z["zero"], z["n_pos"], z["top"]], [["zzzz", "qqqq"], True, 0, []])
check("4 the fallback k chunks", z["fallback"], ["#90", "#89", "#88", "#87"])
rep_z = fc.render_report(res_z)
check("4 the report warns and names the fallback", ["**Zero-score warning:**" in rep_z, "#90, #89, #88, #87" in rep_z], [True, True])
check("4 C7 fails", verdict(res_z, "C7")["verdict"], fc.BAD)

n_ok = sum(ok for _, ok in RESULTS)
print(f"\n{n_ok}/{len(RESULTS)} tool checks passed")
for name, ok in RESULTS:
    if not ok:
        print("FAILED:", name)
sys.exit(0 if n_ok == len(RESULTS) else 1)
