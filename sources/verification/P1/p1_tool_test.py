"""Test study/tools/token_budget_check.py: the climate run against P1_FACTS (S1-S4, S6, S9) and K2-K8, plus small cases.

1. Climate PDF, 1000/200 character windows, 06 §6.7 seed questions, defaults: corpus counts and ratios (S1, S3, K5),
   91 windows and their spread (S4), MiniLM truncation 0 (S6: limit 254 = 256 - [CLS]/[SEP]), the v0 prompt for D-001
   (S9: 107 + 842 + 20 -> 976), cost (K7: <= $0.000227 per call, <= $0.0227 per 100, output 67.7%, Haiku <= $0.0354),
   time (K7: 1,559 tokens per call, >= 19.5 min per 100 at 8K TPM), window share (K8 arithmetic), checklist and
   recommendation ("size chunks in tokens": C2 fails at +41%). The CLI writes the same numbers.
2. Trap K2: the provider-prefixed id raises KeyError in the naive call, the tool resolves o200k_harmony by name; an
   unknown model fails C1 -> "fix the counter first"; --encoding fixes it; Claude is a proxy (C1 "?").
3. Trap K3: a document with "<|endoftext|>" and "<|start|>" (and one with "[CLS]"): default encode raises ValueError,
   the tool counts 7 / 5 ordinary tokens, C4 fails -> "fix the counter first".
4. Window and cap: a cap above max output, and k huge chunks over the window, fail C6 -> "reduce k or chunk size".
5. Cost arithmetic with a made-up price sheet; a stale sheet fails C10; the shipped sheet equals the built-in one.
6. A fake traces file (written here, not a real run) with a `length` finish and an empty answer: C8 fails, C7 fails,
   C9 calibrates the overhead -> "raise max_completion_tokens or lower effort" (before C2's rule). Claude-shaped usage.
7. Recommendation order on synthetic checklists (first match wins), C5 > 5% end to end, C11, and "budget OK".
8. External flags (--pilot, --claude-count, --embedder cohere) call nothing and leave their checks at "?"; C12 rules.

No API calls; MiniLM's tokenizer comes from the local Hugging Face cache (offline). Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_tool_test.py ["<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]                                           # rag_learning/
TOOL = WS / "study" / "tools" / "token_budget_check.py"
EX = WS / "study" / "tools" / "examples"
QUESTIONS = EX / "climate_token_questions.txt"
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
sys.path.insert(0, str(TOOL.parent))
import token_budget_check as tb                               # noqa: E402

RESULTS = []
TODAY = "2026-10-18"


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
verdicts = lambda res: "".join(i["verdict"] for i in res["checklist"])
climate = lambda **kw: tb.run_check([PDF], kw.pop("questions", QUESTIONS), doc_ids=["climate"], today=kw.pop("today", TODAY), **kw)

# ================================================================ 1 the climate run
print("=== 1 climate PDF, defaults (P1_FACTS S1-S9, K5, K7, K8)")
res = climate()
cor = {r["tokenizer"]: r for r in res["corpus"]["rows"]}
check("1 characters (S1: 72,593)", res["corpus"]["chars"], 72593)
check("1 tokenizer resolved by name", [res["settings"]["encoding"], res["generator"]["how"]], ["o200k_harmony", "by name: gpt-oss-20b -> o200k_harmony"])
check("1 o200k_harmony tokens, chars/token (S3, K5: 12,840, 5.65)", [cor["o200k_harmony"]["tokens"], round(cor["o200k_harmony"]["ct"], 2)], [12840, 5.65])
check("1 cl100k tokens, ÷4 error (S3: 13,026, +39%)", [cor["cl100k_base"]["tokens"], round(cor["cl100k_base"]["err4"])], [13026, 39])
check("1 WordPiece tokens, chars/token (S3: 11,694, 6.21)", [cor["MiniLM WordPiece"]["tokens"], round(cor["MiniLM WordPiece"]["ct"], 2)], [11694, 6.21])
check("1 bytes/token (K5: 5.65)", round(cor["o200k_harmony"]["bt"], 2), 5.65)
ch = res["chunks"]
check("1 windows (S4: 91)", ch["N"], 91)
check("1 chars/token per window min/median/max (S4 o200k: 4.59 / 5.62 / 6.49)",
      [round(ch["ratio"]["min"], 2), round(ch["ratio"]["median"], 2), round(ch["ratio"]["max"], 2)], [4.59, 5.62, 6.49])
check("1 most tokens in a window: o200k 218, WordPiece 198 (S4)", [ch["gen"]["max"], ch["wp"]["max"]], [218, 198])
check("1 MiniLM limit 254 text tokens = 256 - 2 (S6)", [ch["truncation"]["limit"], ch["truncation"]["max_seq_length"]], [254, 256])
check("1 MiniLM truncation 0 of 91", [ch["truncation"]["n_over"], ch["truncation"]["rate"]], [0, 0.0])
d1 = res["budget"]["questions"][0]
check("1 D-001 is the first question, copied from 06 §6.7", [d1["id"], d1["q"]],
      ["D-001", "According to the document, by how much have global temperatures risen since the late 19th century?"])
check("1 S9: system 107, question 20, sources 842, input 976", [res["budget"]["system"], d1["q_tokens"], d1["sample_sources"], d1["sample_input"]],
      [107, 20, 842, 976])
check("1 S9: system + user = 4,659 characters", d1["sample_chars"], 4659)
check("1 K7: D-001 one call <= $0.000227, 100 calls <= $0.0227", [round(d1["cost_one"], 6), round(d1["cost_100"], 4)], [0.000227, 0.0227])
check("1 K7: 976 + 71 + 512 = 1,559 tokens; 100 calls >= 19.5 min at 8,000 TPM", [d1["sample_total"], round(d1["min_100"], 1)], [1559, 19.5])
gq = {r["model"]: r for r in res["cost"]["rows"]}
g, h = gq["groq:openai/gpt-oss-20b"], gq["anthropic:claude-haiku-5-5"]
check("1 K7: Groq output share 67.7%, out/in 4x", [round(g["q1_share"], 1), g["ratio"]], [67.7, 4.0])
check("1 K7: Haiku one call <= $0.000354, 100 <= $0.0354, output 72.4%, 5x",
      [round(h["one_q1"], 6), round(100 * h["one_q1"], 4), round(h["q1_share"], 1), h["ratio"]], [0.000354, 0.0354, 72.4, 5.0])
check("1 K8 arithmetic: 1,559 / 131,072 = 1.19%", round(100 * d1["sample_total"] / res["budget"]["window"], 2), 1.19)
check("1 checklist C1..C12", verdicts(res), "✓✗✓✓✓✓???✓✓✓")
check("1 C2 evidence: +41% over-count", "+41% (over-count)" in V(res, "C2")["evidence"], True)
check("1 recommendation (rule 5)", res["recommendation"]["verdict"], "size chunks in tokens, not characters")
rep = tb.render_report(res)
check("1 report has the 9 parts", [f"## {n} " in rep for n in range(1, 10)], [True] * 9)
check("1 report shows 976, $0.000227, $0.0227, 19.5, 72,593", [s in rep for s in ("| 976 |", "≤ $0.000227", "≤ $0.0227", "| 19.5 |", "72,593")], [True] * 5)
with tempfile.TemporaryDirectory(prefix="p1_tool_") as tmp:
    out = Path(tmp) / "r.md"
    cp = subprocess.run([sys.executable, str(TOOL), "--docs", str(PDF), "--doc-ids", "climate", "--questions", str(QUESTIONS),
                         "--today", TODAY, "--report", str(out)], capture_output=True, text=True, encoding="utf-8")
    check("1 CLI exit 0 and the same report", [cp.returncode, out.read_text(encoding="utf-8") == rep], [0, True])
    check("1 CLI summary line", cp.stdout.splitlines()[0], "chunks 91, o200k_harmony 5.65 chars/token")
saved = (EX / "climate_token_report.md").read_text(encoding="utf-8")
check("1 the saved example report has the same numbers (date-independent lines)",
      [line for line in saved.splitlines() if "C10" not in line] == [line for line in rep.splitlines() if "C10" not in line], True)

# ================================================================ 2 trap K2
print("\n=== 2 trap K2: provider prefix")
gi = tb.resolve_generator("groq:openai/gpt-oss-20b")
check("2 naive encoding_for_model('openai/gpt-oss-20b') -> KeyError", "-> KeyError" in gi["naive"], True)
check("2 resolved by name", [gi["encoding"], gi["resolved"], gi["proxy"]], ["o200k_harmony", True, False])
check("2 the plain id maps too (fix 2)", tb.resolve_generator("groq:gpt-oss-20b")["encoding"], "o200k_harmony")
r_unk = climate(questions=None, generator="groq:llama-3.1-8b-instant")
check("2 unknown model: C1 fails", V(r_unk, "C1")["verdict"], tb.BAD)
check("2 unknown model: fix the counter first", r_unk["recommendation"]["verdict"], "fix the counter first")
r_ovr = climate(questions=None, generator="groq:llama-3.1-8b-instant", encoding="o200k_base")
check("2 --encoding override: C1 passes", V(r_ovr, "C1")["verdict"], tb.OK)
r_cl = climate(questions=None, generator="anthropic:claude-haiku-5-5")
check("2 Claude: o200k proxy, C1 '?'", [r_cl["settings"]["encoding"], r_cl["generator"]["proxy"], V(r_cl, "C1")["verdict"]],
      ["o200k_base", True, tb.ASK])
check("2 Claude: the report says proxy and count_tokens", ["proxy" in tb.render_report(r_cl), "count_tokens" in tb.render_report(r_cl)], [True, True])

# ================================================================ 3 trap K3
print("\n=== 3 trap K3: special-token strings in a document")
with tempfile.TemporaryDirectory(prefix="p1_tool_") as tmp:
    a = Path(tmp) / "chat_log.txt"
    a.write_text("A pasted chat log ends with <|endoftext|> and a template line <|start|>assistant. " * 3, encoding="utf-8")
    b = Path(tmp) / "bert_notes.md"
    b.write_text("BERT puts [CLS] first and [SEP] last. " * 3, encoding="utf-8")
    r_sp = tb.run_check([a], [{"q": "what is in the log?"}], today=TODAY)
    r_wp = tb.run_check([b], None, today=TODAY)
sp = r_sp["specials"]
check("3 found: <|endoftext|> x3, <|start|> x3", sp["generator"], {"<|endoftext|>": 3, "<|start|>": 3})
check("3 default encode raises ValueError (demonstrated)", sp["demo"].startswith("encode('<|endoftext|>') -> ValueError"), True)
enc = tb.tiktoken.get_encoding("o200k_harmony")
check("3 counted as ordinary text: 7 and 5 tokens (K3)", [tb.ntok(enc, "<|endoftext|>"), tb.ntok(enc, "<|start|>")], [7, 5])
check("3 C4 fails", V(r_sp, "C4")["verdict"], tb.BAD)
check("3 fix the counter first", r_sp["recommendation"]["verdict"], "fix the counter first")
check("3 [CLS]/[SEP] text: C4 fails", [r_wp["specials"]["embedder"], V(r_wp, "C4")["verdict"]], [{"[CLS]": 3, "[SEP]": 3}, tb.BAD])

# ================================================================ 4 window and cap
print("\n=== 4 window and cap (C6)")
r_cap = climate(max_completion_tokens=70000)
check("4 cap 70,000 > max output 65,536: C6 fails", [V(r_cap, "C6")["verdict"], "> max output 65,536" in V(r_cap, "C6")["evidence"]], [tb.BAD, True])
check("4 recommendation (rule 2)", r_cap["recommendation"]["verdict"], "reduce k or chunk size, or raise nothing: the call cannot fit")
with tempfile.TemporaryDirectory(prefix="p1_tool_") as tmp:
    big = Path(tmp) / "big.txt"
    big.write_text("The quick brown fox jumps over the lazy dog. " * 40000, encoding="utf-8")      # 1.8M chars
    r_big = tb.run_check([big], [{"q": "fox?"}], chunk_size=40000, overlap=0, unit="tokens", k=4, today=TODAY)
wb = r_big["budget"]["questions"][0]
check("4 token windows of 40,000: 4 sources > 90% of 131,072", [wb["upper_input"] > 160000, V(r_big, "C6")["verdict"]], [True, tb.BAD])
check("4 a token-unit chunk holds 40,000 tokens", r_big["chunks"]["gen"]["max"], 40000)
check("4 recommendation (rule 2)", r_big["recommendation"]["verdict"], "reduce k or chunk size, or raise nothing: the call cannot fit")

# ================================================================ 5 cost arithmetic, price sheet
print("\n=== 5 cost arithmetic and the price sheet")
sheet = {"price_table_version": "2026-10-01", "models": {"groq:openai/gpt-oss-20b": {"input": 1.0, "output": 2.0, "context_window": 131072, "max_output": 65536}}}
r_p = climate(prices=sheet, runs=10)
q = r_p["budget"]["questions"][0]
c = r_p["cost"]["rows"][0]
check("5 one call = (976 x 1 + 512 x 2) / 1e6 = $0.002", [q["cost_one"], c["one_q1"]], [0.002, 0.002], 1e-12)
check("5 10 calls (upper) = 10 x (max upper input + 1024) / 1e6", c["run_upper"], 10 * (r_p["cost"]["max_upper_input"] + 1024) / 1e6, 1e-12)
check("5 + overhead adds 10 x 71 x $1 / 1e6", c["run_overhead"] - c["run_upper"], 10 * 71 / 1e6, 1e-12)
check("5 C10 passes at 17 days", V(r_p, "C10")["verdict"], tb.OK)
r_old = climate(questions=None, today="2026-12-01")
check("5 C10 fails 45 days after 2026-10-17", [V(r_old, "C10")["verdict"], "45 day(s)" in V(r_old, "C10")["evidence"]], [tb.BAD, True])
check("5 shipped prices_2026-10-17.json = built-in sheet",
      json.loads((EX / "prices_2026-10-17.json").read_text(encoding="utf-8")) == tb.DEFAULT_PRICES, True)
check("5 the sheet's prices (foundation §6.2)", [tb.DEFAULT_PRICES["models"]["groq:openai/gpt-oss-20b"][x] for x in ("input", "output", "cached_input")]
      + [tb.DEFAULT_PRICES["models"]["anthropic:claude-haiku-5-5"][x] for x in ("input", "output")], [0.075, 0.30, 0.037, 0.10, 0.50])
check("5 money format", [tb.money(0.000227), tb.money(0.0227), tb.money(1.5)], ["$0.000227", "$0.0227", "$1.50"])

# ================================================================ 6 fake traces
print("\n=== 6 a fake traces file (made up for this test; not a recorded run)")
msgs = [{"role": "system", "content": "Answer briefly."}, {"role": "user", "content": "In what year was the Paris Agreement adopted?"}]
counted = sum(tb.ntok(enc, m["content"]) for m in msgs)
fake = [
    {"messages": msgs, "usage": {"prompt_tokens": counted + 70, "completion_tokens": 150, "completion_tokens_details": {"reasoning_tokens": 100}},
     "choices": [{"finish_reason": "stop", "message": {"content": "2015 [climate:10]."}}]},
    {"messages": msgs, "usage": {"prompt_tokens": counted + 72, "completion_tokens": 160, "completion_tokens_details": {"reasoning_tokens": 110}},
     "choices": [{"finish_reason": "stop", "message": {"content": "2015 [climate:10]."}}]},
    {"response": {"usage": {"prompt_tokens": counted + 71, "completion_tokens": 170, "completion_tokens_details": {"reasoning_tokens": 120}},
                  "choices": [{"finish_reason": "stop", "message": {"content": "2015."}}]}, "counted_prompt_tokens": counted},
    {"messages": msgs, "usage": {"prompt_tokens": counted + 71, "completion_tokens": 512, "completion_tokens_details": {"reasoning_tokens": 512}},
     "finish_reason": "length", "answer": ""},
]
with tempfile.TemporaryDirectory(prefix="p1_tool_") as tmp:
    tf = Path(tmp) / "results.jsonl"
    tf.write_text("\n".join(json.dumps(x) for x in fake) + "\n", encoding="utf-8")
    r_tr = climate(traces=tf)
    r_tr_over = climate(questions=None, traces=tf, overhead=60)
ts = r_tr["traces"]
check("6 4 traces: finish stop x3, length x1; empty 1", [ts["n"], ts["finishes"], ts["length"], ts["empty"]], [4, {"stop": 3, "length": 1}, 1, 1])
check("6 completion p95 (linear) and reasoning p50", [round(ts["completion_p95"], 2), ts["reasoning_p50"]], [460.7, 115.0])
check("6 overhead: median 71, max 72 (billed - counted)", [ts["overhead_p50"], ts["overhead_max"], ts["overhead_n"]], [71.0, 72, 4])
check("6 C7 fails (p95 461 > 80% of 512)", V(r_tr, "C7")["verdict"], tb.BAD)
check("6 C8 fails (length 1/4, empty 1/4)", [V(r_tr, "C8")["verdict"], "cut at the cap 1/4" in V(r_tr, "C8")["evidence"]], [tb.BAD, True])
check("6 C9 fails with the assumed 71 < measured max 72", V(r_tr, "C9")["verdict"], tb.BAD)
check("6 C9 with --overhead 60 also fails; names --overhead 72", ["--overhead 72" in V(r_tr_over, "C9")["evidence"]], [True])
check("6 rule 3 comes before C2's rule 5", [V(r_tr, "C2")["verdict"], r_tr["recommendation"]["verdict"]],
      [tb.BAD, "raise `max_completion_tokens` or lower effort"])
claude_rec = tb.parse_trace({"usage": {"input_tokens": 900, "output_tokens": 512}, "stop_reason": "max_tokens",
                             "content": [{"type": "text", "text": ""}]})
check("6 Claude-shaped usage: max_tokens counts as a cap stop, empty answer", [claude_rec["prompt"], claude_rec["completion"], claude_rec["length"], claude_rec["empty"]],
      [900, 512, True, True])
good = [dict(x) for x in fake[:3]]
with tempfile.TemporaryDirectory(prefix="p1_tool_") as tmp:
    tf = Path(tmp) / "ok.jsonl"
    tf.write_text("\n".join(json.dumps(x) for x in good) + "\n", encoding="utf-8")
    r_ok = climate(questions=None, traces=tf, overhead=72)
check("6 clean traces: C7, C8, C9 pass", [V(r_ok, i)["verdict"] for i in ("C7", "C8", "C9")], [tb.OK] * 3)

# ================================================================ 7 recommendation order
print("\n=== 7 recommendation order (first match wins)")
ALL = [f"C{i}" for i in range(1, 13)]


def synth(bad):
    r = {"checklist": [{"id": i, "verdict": tb.BAD if i in bad else tb.OK, "evidence": f"{i} evidence"} for i in ALL],
         "cost": {"rows": [], "version": "x"}, "settings": {"runs": 100, "tpm": 8000}, "time": {"min_upper": 1.0}}
    return tb.recommend(r)["verdict"]


cases = [({"C4", "C6", "C7", "C5", "C2", "C11"}, "fix the counter first"), ({"C1", "C2"}, "fix the counter first"),
         ({"C6", "C8", "C5"}, "reduce k or chunk size, or raise nothing: the call cannot fit"),
         ({"C8", "C5", "C2"}, "raise `max_completion_tokens` or lower effort"), ({"C7"}, "raise `max_completion_tokens` or lower effort"),
         ({"C5", "C2", "C11"}, "chunks are being truncated: shrink chunks or switch embedder (see P4)"),
         ({"C2", "C11"}, "size chunks in tokens, not characters"), ({"C11", "C3", "C9", "C10", "C12"}, "split the run or lower volume; check the daily quota"),
         ({"C3", "C9", "C10", "C12"}, "budget OK"), (set(), "budget OK")]
for bad, exp in cases:
    check(f"7 failing {sorted(bad, key=lambda x: int(x[1:]))}", synth(bad), exp)
r_tr5 = climate(questions=None, chunk_size=2000, overlap=200)
t5 = r_tr5["chunks"]["truncation"]
check("7 2000-char windows: MiniLM truncation > 5%, C5 fails", [t5["rate"] > 5, V(r_tr5, "C5")["verdict"]], [True, tb.BAD])
check("7 C5's rule comes before C2's", [V(r_tr5, "C2")["verdict"], r_tr5["recommendation"]["verdict"]],
      [tb.BAD, "chunks are being truncated: shrink chunks or switch embedder (see P4)"])
r_q = climate(questions=None, runs=200)
check("7 200 calls: > 200,000 tokens/day, C11 fails (C2 still wins)", [V(r_q, "C11")["verdict"], r_q["recommendation"]["verdict"]],
      [tb.BAD, "size chunks in tokens, not characters"])
with tempfile.TemporaryDirectory(prefix="p1_tool_") as tmp:
    code = Path(tmp) / "helper_functions.txt"
    code.write_text((WS.parent / "upstream" / "RAG_Techniques" / "helper_functions.py").read_text(encoding="utf-8"), encoding="utf-8")
    r_code = tb.run_check([code], [{"q": "What does retrieve_context_per_question return?"}], chunk_size=500, overlap=100, today=TODAY)
    r_code11 = tb.run_check([code], None, chunk_size=500, overlap=100, runs=1000, today=TODAY)
check("7 repo code: 4.61 chars/token (K4), ÷4 error under 20%: C2 passes",
      [round(r_code["corpus"]["rows"][0]["ct"], 2), V(r_code, "C2")["verdict"]], [4.61, tb.OK])
check("7 repo code: code-like lines over 20%, C3 fails (not a rule)", V(r_code, "C3")["verdict"], tb.BAD)
check("7 repo code, 500-char chunks: budget OK", r_code["recommendation"]["verdict"], "budget OK")
check("7 1,000 calls: C11 fails -> split the run", r_code11["recommendation"]["verdict"], "split the run or lower volume; check the daily quota")

# ================================================================ 8 external flags, C12
print("\n=== 8 external flags call nothing; C12")
r_ext = climate(questions=None, pilot=5, claude_count=True, embedder="cohere")
check("8 three 'not built' notes", [len(r_ext["notes"]), all(tb.LLMOPS_NOTE in n for n in r_ext["notes"])], [3, True])
check("8 Cohere: C5 '?', no WordPiece counts", [V(r_ext, "C5")["verdict"], r_ext["chunks"]["truncation"], r_ext["chunks"]["wp"]], [tb.ASK, None, None])
check("8 pilot: C7 and C9 stay '?'", [V(r_ext, "C7")["verdict"], V(r_ext, "C9")["verdict"]], [tb.ASK, tb.ASK])
check("8 no WordPiece row in the corpus table", [r["tokenizer"] for r in r_ext["corpus"]["rows"]], ["o200k_harmony", "o200k_base", "cl100k_base"])
r_t = climate(questions=None, generator="anthropic:claude-haiku-5-5", temperature=0.0)
check("8 temperature sent to Claude: C12 fails", [V(r_t, "C12")["verdict"], "400" in V(r_t, "C12")["evidence"]], [tb.BAD, True])
r_t2 = climate(questions=None, generator="anthropic:claude-haiku-5-5")
check("8 Claude, temperature auto (not sent), effort low: C12 passes", [r_t2["settings"]["temperature"], V(r_t2, "C12")["verdict"]], [None, tb.OK])
r_e = climate(questions=None, effort="none")
check("8 effort not sent: C12 fails", V(r_e, "C12")["verdict"], tb.BAD)
r_e2 = climate(questions=None, effort="max")
check("8 effort 'max' on Groq: C12 fails", V(r_e2, "C12")["verdict"], tb.BAD)
r_t3 = climate(questions=None, temperature=2.5)
check("8 Groq temperature 2.5: C12 fails", V(r_t3, "C12")["verdict"], tb.BAD)
with tempfile.TemporaryDirectory(prefix="p1_tool_") as tmp:
    cp = subprocess.run([sys.executable, str(TOOL), "--docs", str(PDF), "--pilot", "--claude-count", "--today", TODAY,
                         "--report", str(Path(tmp) / "r.md")], capture_output=True, text=True, encoding="utf-8")
check("8 CLI: --pilot prints the note on stderr and exits 0", [cp.returncode, "--pilot: needs the shared LLMOps cache package" in cp.stderr], [0, True])

n_ok = sum(ok for _, ok in RESULTS)
print(f"\n{n_ok}/{len(RESULTS)} tool checks passed")
for name, ok in RESULTS:
    if not ok:
        print("FAILED:", name)
sys.exit(0 if n_ok == len(RESULTS) else 1)
