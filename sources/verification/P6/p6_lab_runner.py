"""Execute labs/P6_ir_metrics_lab.ipynb top to bottom with the learner/prediction cells replaced by blocks
from a solutions file, and report every CHECK cell as PASS or FAIL. Contains no solution code.

Solutions file format: blocks that start with a line '# == <task id>' (the `task` value in the cell metadata).
Cells without a matching block keep their original (empty) source. Each cell runs in one shared namespace,
like a kernel; an error in one cell is reported and the run continues.

Run from rag_learning/ (the solutions file lives OUTSIDE the workspace, e.g. in a scratch folder):
    uv run python sources/verification/P6/p6_lab_runner.py labs/P6_ir_metrics_lab.ipynb <solutions.py>
"""
import contextlib
import io
import json
import re
import sys
import traceback

nb_path, sol_path = sys.argv[1], sys.argv[2]
blocks, cur = {}, None
for line in open(sol_path, encoding="utf-8").read().splitlines(keepends=True):
    m = re.match(r"# == (\S+)\s*$", line)
    if m:
        cur = m.group(1)
        blocks[cur] = ""
    elif cur:
        blocks[cur] += line

cells = json.load(open(nb_path, encoding="utf-8"))["cells"]
ns = {"__name__": "__main__"}
results = []
for i, c in enumerate(cells):
    if c["cell_type"] != "code":
        continue
    tags = c["metadata"].get("tags", [])
    task = c["metadata"].get("task")
    src = "".join(c["source"])
    if task in blocks:
        src = blocks[task]
    buf = io.StringIO()
    ok, err = True, ""
    with contextlib.redirect_stdout(buf):
        try:
            exec(compile(src, f"<cell {i}>", "exec"), ns)
        except Exception as e:  # noqa: BLE001
            ok, err = False, f"{type(e).__name__}: {e}"
            if not isinstance(e, AssertionError):
                err += " | " + traceback.format_exc().strip().splitlines()[-2].strip()
    label = src.splitlines()[0] if src.strip() else "(empty)"
    kind = "CHECK" if "check" in tags else (tags[0] if tags else "code")
    print(f"--- cell {i} [{kind}{'/' + task if task else ''}] {label[:70]}")
    out = buf.getvalue().rstrip()
    if out:
        print("    " + out.replace("\n", "\n    "))
    if not ok:
        print(f"    ERROR {err}")
    if kind == "CHECK":
        results.append((i, label, ok, err))

print("\n=== CHECK summary")
for i, label, ok, err in results:
    print(f"{'PASS' if ok else 'FAIL'} cell {i}: {label}" + ("" if ok else f"  <- {err[:160]}"))
n_ok = sum(ok for *_, ok, _ in results)
print(f"{n_ok}/{len(results)} CHECK cells passed")
