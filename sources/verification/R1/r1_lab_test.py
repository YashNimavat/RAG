"""R1 lab test: run labs/R1_hybrid_fusion_lab.ipynb with the reference solution (must pass every CHECK), with no
solution (must fail), and with broken variants of the solution (each must fail at its own task).

Variants are made from r1_lab_solution.py by text replacement in a temporary folder outside the workspace.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_lab_test.py > sources/verification/R1/out_r1_lab_test.txt
"""
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
NB = WS / "labs" / "R1_hybrid_fusion_lab.ipynb"
RUNNER = HERE / "r1_lab_runner.py"
GOOD = (HERE / "r1_lab_solution.py").read_text(encoding="utf-8")

POSITIONAL = '''def weighted_fusion(lists, weights, norm):
    names = list(lists)
    a, b = (list(norm(lists[n]).items()) for n in names)          # BUG: pairs list items by POSITION
    return {a[i][0]: weights[names[0]] * a[i][1] + weights[names[1]] * (b[i][1] if i < len(b) else 0.0)
            for i in range(len(a))}
'''
WEAK_TEST = '''def test_fusion_preserves_identity(fuse):
    out = fuse({"a": 0.9, "b": 0.1, "c": 0.5, "d": 0.3}, {"a": 1.0, "b": 2.0}, 0.5)
    assert len(out) == 4, "four documents in, four out"
'''


def replace_def(src, name, new):
    m = re.search(rf"^def {name}\(.*?(?=^def |^# == |\Z)", src, re.S | re.M)
    assert m, name
    return src[:m.start()] + new + "\n" + src[m.end():]


VARIANTS = {
    "good": GOOD,
    "good_alt_literal_weights": GOOD.replace('{"dense": 0.7, "bm25": 1 - 0.7}', '{"dense": 0.7, "bm25": 0.3}')
                                    .replace("fused[d] = fused.get(d, 0.0) + 1.0 / (k + rank)",
                                             "fused[d] = fused.get(d, 0) + 1 / (rank + k)"),
    "blank": "",
    "rrf_ranks_from_0": GOOD.replace("for rank, d in enumerate(lst, 1):", "for rank, d in enumerate(lst):"),
    "no_tie_rule": GOOD.replace("return sorted(scores, key=lambda d: (-scores[d], d))",
                                "return sorted(scores, key=lambda d: -scores[d])"),
    "minmax_constant_is_0": GOOD.replace("return {d: 1.0 for d in scores}", "return {d: 0.0 for d in scores}"),
    "missing_gets_0.5": GOOD.replace("normed[name].get(d, 0.0)", "normed[name].get(d, 0.5)"),
    "zscore_sample_sd": GOOD.replace("float(v.std())", "float(v.std(ddof=1))"),
    "positional_fusion": replace_def(GOOD, "weighted_fusion", POSITIONAL),
    "bm25_split_tokenizer": GOOD.replace('BM25Okapi([tok_norm(c["text"]) for c in chunks])',
                                         'BM25Okapi([c["text"].split() for c in chunks])')
                                .replace("bm25.get_scores(tok_norm(question))", "bm25.get_scores(question.split())"),
    "weak_identity_test": replace_def(GOOD, "test_fusion_preserves_identity", WEAK_TEST),
}
for name, src in VARIANTS.items():
    assert name == "good" or src != GOOD, f"variant {name} did not change the solution"

print(f"# R1 lab test. Notebook sha256 {hashlib.sha256(NB.read_bytes()).hexdigest()}; "
      f"solution sha256 {hashlib.sha256(GOOD.encode('utf-8')).hexdigest()[:16]}; runner {RUNNER.name} (no solution code).")
summary = []
with tempfile.TemporaryDirectory(prefix="r1_labtest_") as tmp:
    for name, src in VARIANTS.items():
        p = Path(tmp) / f"solution_{name}.py"
        p.write_text(src, encoding="utf-8")
        r = subprocess.run([sys.executable, str(RUNNER), str(NB), str(p)], capture_output=True, text=True,
                           encoding="utf-8", cwd=str(WS))
        out = r.stdout
        tail = out[out.index("=== CHECK summary"):] if "=== CHECK summary" in out else out[-2000:] + r.stderr[-2000:]
        print(f"\nvariant={name}")
        print(tail.rstrip())
        m = re.search(r"(\d+)/(\d+) CHECK cells passed", tail)
        fails = re.findall(r"^FAIL cell \d+: # CHECK (Task \w+)", tail, re.M)
        summary.append((name, m.group(0) if m else "runner error", fails))
        if name == "good":
            (HERE / "out_r1_lab_good_full.txt").write_text(out, encoding="utf-8")

print("\n=== SUMMARY")
ok = True
for name, res, fails in summary:
    print(f"{name:22s} {res:28s} fails: {', '.join(fails) if fails else '-'}")
for name, res, fails in summary:
    m = re.match(r"(\d+)/(\d+)", res)
    if name.startswith("good"):
        ok &= bool(m) and m.group(1) == m.group(2)
    else:
        ok &= bool(fails)
print("LAB TEST", "PASS: the solution passes every CHECK and every broken variant fails at least one" if ok else "FAIL")
