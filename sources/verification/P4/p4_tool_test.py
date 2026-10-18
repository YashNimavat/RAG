"""Test study/tools/embed_fit_check.py against P4_FACTS (K2-K12) and small made-up cases.

1. Chunking: the v0 chunker gives exactly v0's 97 chunk texts (as built by p4_kit_measure.py from 06 + 07); the
   windows chunker gives P3's 91 windows; bad sizes raise.
2. Inputs: .txt and .jsonl questions, a list-valued expect, bad JSON, a missing "q", unsupported file types.
3. The climate example equals K2, K4, K6, K7, K9, K11 and K12: token counts, lengths, self-retrieval, pair median,
   per-question ranks, MRR@10 per arm (base, rerank, dims 256 / 128, int8), best scores of the no-answer questions.
4. Checklist verdicts on the example; C6 with no threshold, a threshold inside and outside the spread.
5. Each recommendation branch end to end on small made-up documents: chunks over the limit (C1), a model without a
   Normalize module (C2, paraphrase-MiniLM-L3-v2), a manifest with another model id (C3), near-duplicates (C7),
   10+ labelled questions (C8), and the rule order on synthetic checklists.
6. The CLI writes the saved example report byte for byte, a second run is byte-identical, --provider cohere refuses,
   and the tool's source makes no network or API call.

No API calls; the models load from the local Hugging Face cache (offline). Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P4/p4_tool_test.py ["<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"]
Saved output: sources/verification/P4/out_p4_tool_test.txt
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]                                           # rag_learning/
TOOL = WS / "study" / "tools" / "embed_fit_check.py"
EX = WS / "study" / "tools" / "examples"
QFILE = EX / "climate_embed_questions.jsonl"
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
sys.path.insert(0, str(TOOL.parent))
import embed_fit_check as ef                                   # noqa: E402

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
verdicts = lambda res: " ".join(f"{i['id']}{i['verdict']}" for i in res["checklist"])
TMP = Path(tempfile.mkdtemp(prefix="p4tool_"))

# ---------------------------------------------------------------- 1 chunking
print("=== 1 chunking")
src = (HERE / "p4_kit_measure.py").read_text(encoding="utf-8")
G = {"__file__": str(HERE / "p4_kit_measure.py"), "__name__": "kit"}
sys.argv = [sys.argv[0], str(PDF)]
exec(compile(src[:src.index("# ---------------------------------------------------------------- K1")], "kit", "exec"), G)
docs = ef.load_documents([PDF])
v0 = ef.make_chunks(docs)
check("1 v0 chunker: 97 chunks", len(v0), 97)
check("1 v0 chunker: every text equals v0's chunks (06 + 07 recipe)", [c["text"] for c in v0] == G["TEXT"], True)
check("1 v0 chunker: pages equal v0's", [c["page"] for c in v0] == G["PAGE"], True)
win = ef.make_chunks(docs, chunker="windows")
full = "\n".join(G["pages"])
check("1 windows chunker: P3's 91 windows (1000 / step 800)", [len(win), [c["text"] for c in win] == [full[i:i + 1000] for i in range(0, len(full), 800)]], [91, True])
check("1 bad sizes raise", [raises(lambda: ef.make_chunks(docs, 100, 100), ValueError), raises(lambda: ef.make_chunks(docs, 0, 0), ValueError),
                            raises(lambda: ef.make_chunks(docs, chunker="x"), ValueError)], [True, True, True])
check("1 recursive_spans tile a text within the size", (lambda t: all(b - a <= 50 for a, b in ef.recursive_spans(t, 50, 10))
                                                       and ef.recursive_spans(t, 50, 10)[0][0] == 0 and ef.recursive_spans(t, 50, 10)[-1][1] == len(t))(
    "word " * 40 + "\n\n" + "x" * 120), True)

# ---------------------------------------------------------------- 2 inputs
print("=== 2 inputs")
(TMP / "q.txt").write_text("# a comment\nfirst question\n\nsecond question\n", encoding="utf-8")
check("2 .txt questions skip comments and blanks", [q["q"] for q in ef.load_questions(TMP / "q.txt")], ["first question", "second question"])
(TMP / "q.jsonl").write_text('{"q": "a", "expect": "x"}\n{"q": "b", "expect": ["y", "z"], "type": "t", "id": "B"}\n', encoding="utf-8")
qs = ef.load_questions(TMP / "q.jsonl")
check("2 .jsonl questions: string expect becomes a list; ids default to Q<n>", [qs[0]["expect"], qs[0]["id"], qs[1]["expect"], qs[1]["id"], qs[1]["type"]],
      [["x"], "Q1", ["y", "z"], "B", "t"])
(TMP / "bad.jsonl").write_text('{"q": "a"}\nnot json\n', encoding="utf-8")
check("2 bad JSON names the line", raises(lambda: ef.load_questions(TMP / "bad.jsonl"), ValueError), True)
check("2 a missing q raises", raises(lambda: ef.load_questions([{"expect": "x"}]), ValueError), True)
(TMP / "x.docx").write_text("x", encoding="utf-8")
check("2 unsupported file type raises", raises(lambda: ef.load_documents([TMP / "x.docx"]), ValueError), True)
check("2 a missing path raises", raises(lambda: ef.load_documents([TMP / "nope.pdf"]), FileNotFoundError), True)

# ---------------------------------------------------------------- 3 the climate example vs P4_FACTS
print("=== 3 the climate example")
res = ef.run_check([PDF], QFILE, k=4, rerank=True, dims=(256, 128), int8=True, threshold=0.5)
L, Vv = res["lengths"], res["vectors"]
check("3 setup: dim, limit, pooling, Normalize, prompts (K1)", [res["setup"]["dim"], res["setup"]["max_seq_length"], res["setup"]["pooling"],
                                                            res["setup"]["normalize"], res["setup"]["prompts"]], [384, 256, "mean", True, {"query": "", "document": ""}])
check("3 tokens per chunk min / median / max; over 256; over 128 (K7)", [L["min"], L["median"], L["max"], len(L["over"]), L["over_128"]], [59, 149, 182, 0, 70])
check("3 vector lengths as returned (K2)", [Vv["norm_min"], Vv["norm_max"]], [1.0, 1.0], 5e-7)
check("3 self-retrieval 5/5 (K5); no near-duplicates; pair median (K6)", [sum(Vv["self_ok"]), len(Vv["dups"]), Vv["pair_median"]], [5, 0, 0.3906], 5e-5)
rows = {r["id"]: r for r in res["rows"]}
check("3 right chunks found per draft question (K1, opening words of each span)",
      [[int(res["chunks"][i]["id"][1:]) for i in rows[q]["targets"]] for q in ("D-001", "D-002", "D-004", "D-005", "D-007")],
      [[7], [27], [23, 67], [3, 4], [27, 85]])
check("3 base ranks D-001..D-008 (K4)", [res["arms"]["base"][f"D-00{i}"] for i in range(1, 9)], [3, 3, 1, 1, 1, 1, 2, 2])
M = lambda arm: res["measuring"][arm]["all"]
check("3 base: Hit@1, Hit@4, MRR@10 (K4)", [M("base")["hit1"], M("base")["hitk"], M("base")["mrr"]], [4, 8, 0.708], 5e-4)
check("3 rerank: every right chunk first (K9)", [res["arms"]["rerank"][f"D-00{i}"] for i in range(1, 9)], [1] * 8)
check("3 dims 256, 128: MRR@10 (K11)", [M("dims 256")["mrr"], M("dims 128")["mrr"]], [0.750, 0.583], 5e-4)
check("3 int8: ranks and MRR@10 (K12)", [[res["arms"]["int8"][f"D-00{i}"] for i in range(1, 9)], M("int8")["mrr"]], [[4, 3, 1, 1, 1, 1, 2, 1], 0.760], 5e-4)
check("3 best score of D-002, D-009, D-010 (K4)", [rows["D-002"]["top1"], rows["D-009"]["top1"], rows["D-010"]["top1"]], [0.4606, 0.3099, 0.5196], 5e-5)
check("3 D-002 top 4 = chunks 69, 68, 27, 17 (K3)", [res["chunks"][i]["id"] for i, _ in rows["D-002"]["top"]], ["#69", "#68", "#27", "#17"])
check("3 8 labelled questions", res["n_labelled"], 8)

# ---------------------------------------------------------------- 4 checklist on the example
print("=== 4 checklist")
check("4 example verdicts", verdicts(res), "C1✓ C2✓ C3? C4? C5✓ C6✗ C7✓ C8? C9✓ C10✗ C11? C12?")
check("4 recommendation: mechanism only (8 < 10 labelled)", res["recommendation"].startswith("Mechanism only"), True)
r0 = ef.run_check([PDF], QFILE, k=4)
check("4 no threshold: C6 ✓; C9, C10 not run", [V(r0, "C6"), V(r0, "C9"), V(r0, "C10")], ["✓", "?", "?"])
check("4 threshold 0.9 (outside the spread): C6 ?", V(ef.run_check([PDF], QFILE, k=4, threshold=0.9), "C6"), "?")
check("4 the licence is read from the local model card", "apache-2.0" in next(i for i in res["checklist"] if i["id"] == "C12")["evidence"], True)

# ---------------------------------------------------------------- 5 branches on made-up documents
print("=== 5 branches")
long_txt = TMP / "long.txt"
long_txt.write_text(" ".join(f"word{i} alpha beta gamma" for i in range(400)), encoding="utf-8")
rl = ef.run_check([long_txt], ["what is word12"], chunk_size=3000, overlap=0)
check("5 chunks over 256 tokens: C1 ✗, recommendation shorten", [V(rl, "C1"), rl["recommendation"].startswith("Shorten")], ["✗", True])
check("5 the ignored characters are counted", all(v > 0 for v in rl["lengths"]["ignored_chars"].values()) and len(rl["lengths"]["over"]) > 0, True)
paras = ["Solar panels turn sunlight into electricity for homes.", "Wind turbines use moving air to make power.",
         "Forests store carbon in wood and soil.", "Glaciers are melting faster in warm summers."]
small = TMP / "small.txt"
small.write_text("\n\n".join(paras), encoding="utf-8")
rl3 = ef.run_check([small], [{"q": "how do forests help", "expect": "store carbon"}], model="sentence-transformers/paraphrase-MiniLM-L3-v2", chunk_size=60, overlap=0)
check("5 a model without Normalize: C2 ✗, recommendation normalise", [V(rl3, "C2"), rl3["setup"]["normalize"], rl3["recommendation"].startswith("Normalise")],
      ["✗", False, True])
rm = ef.run_check([small], ["how do forests help"], chunk_size=60, overlap=0, manifest={"model_id": "sentence-transformers/paraphrase-MiniLM-L3-v2"})
check("5 a manifest with another model id: C3 ✗, recommendation re-embed", [V(rm, "C3"), rm["recommendation"].startswith("Re-embed")], ["✗", True])
rok = ef.run_check([small], ["how do forests help"], chunk_size=60, overlap=0, manifest={"model_id": ef.DEFAULT_MODEL})
check("5 a matching manifest: C3 ✓", V(rok, "C3"), "✓")
dup = TMP / "dup.txt"
dup.write_text("\n\n".join(paras + [paras[0]]), encoding="utf-8")
rd = ef.run_check([dup], None, chunk_size=60, overlap=0)
check("5 a repeated paragraph: C7 ✗ with one pair", [V(rd, "C7"), len(rd["vectors"]["dups"])], ["✗", 1])
many = [{"q": q, "expect": e} for q, e in [("sunlight electricity", "Solar panels"), ("moving air power", "Wind turbines"), ("carbon in wood", "Forests store"),
                                          ("melting ice", "Glaciers are")] * 3]
rmany = ef.run_check([small], many, chunk_size=60, overlap=0, k=1)
check("5 12 labelled questions: C8 judged (✓), recommendation not 'mechanism only'", [rmany["n_labelled"], V(rmany, "C8"), rmany["recommendation"].startswith("Mechanism")],
      [12, "✓", False])
rmiss = ef.run_check([small], [{"q": "x", "expect": "not in the text at all"}], chunk_size=60, overlap=0)
check("5 an expect text found nowhere is flagged", [rmiss["rows"][0]["missing_target"], rmiss["n_labelled"]], [True, 0])
base_cl = {"C1": "✓", "C2": "✓", "C3": "?", "C5": "✓", "C8": "?", "C10": "?"}
fake = lambda **kw: {"checklist": [{"id": k, "verdict": v} for k, v in {**base_cl, **kw}.items()], "n_labelled": 20, "arms": {"base": {}}}
order_ok = [ef.recommend(fake(C1="✗", C5="✗")).startswith("Shorten"), ef.recommend(fake(C5="✗", C3="✗")).startswith("Stop"),
            ef.recommend(fake(C3="✗", C2="✗")).startswith("Re-embed"), ef.recommend(fake(C2="✗", C8="✗")).startswith("Normalise"),
            ef.recommend(fake(C8="✗")).startswith("Retrieval misses"), ef.recommend(fake(C10="✓")).startswith("Setup looks sound, and"),
            ef.recommend(fake()).startswith("Setup looks sound. Next")]
check("5 recommendation rule order (C1 > C5 > C3 > C2 > data > C8 > rerank > C10 > default)", order_ok, [True] * 7)

# ---------------------------------------------------------------- 6 CLI
print("=== 6 CLI")
args = [sys.executable, str(TOOL), "--docs", str(PDF), "--questions", str(QFILE), "--k", "4", "--rerank", "--dims", "256,128", "--int8", "--threshold", "0.5"]
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
outs = []
for n in (1, 2):
    out = TMP / f"r{n}.md"
    cp = subprocess.run(args + ["--report", str(out)], capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(WS))
    outs.append((cp.returncode, out.read_bytes() if out.exists() else b""))
check("6 the CLI exits 0 and equals the saved example report", [outs[0][0], outs[0][1] == (EX / "climate_embed_report.md").read_bytes()], [0, True])
check("6 a second run is byte-identical", outs[0][1] == outs[1][1], True)
cp = subprocess.run([sys.executable, str(TOOL), "--docs", str(small), "--provider", "cohere"], capture_output=True, text=True, encoding="utf-8", env=env)
check("6 --provider cohere refuses (exit 2) and names the missing llmops cache", [cp.returncode, "study/llmops" in cp.stderr], [2, True])
tsrc = TOOL.read_text(encoding="utf-8")
check("6 the tool imports no network or API client", [w for w in ("requests", "urllib", "http.client", "groq", "cohere", "anthropic", "langsmith", "dotenv", "openai")
                                                      if re.search(rf"^\s*(import|from)\s+{re.escape(w)}", tsrc, re.M)], [])
check("6 the tool forces the offline Hugging Face mode", 'os.environ.setdefault("HF_HUB_OFFLINE", "1")' in tsrc, True)

shutil.rmtree(TMP, ignore_errors=True)
n_ok = sum(ok for _, ok in RESULTS)
print(f"\n{n_ok}/{len(RESULTS)} tool checks passed")
sys.exit(0 if n_ok == len(RESULTS) else 1)
