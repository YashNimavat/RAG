"""Execute labs/C1_parsing_lab.ipynb top to bottom with the learner/prediction cells replaced by blocks from a
solutions file, and report every CHECK cell as PASS or FAIL. Contains no solution code.

Solutions file format: blocks that start with a line '# == <task id>' (the `task` value in the cell metadata).
Cells without a matching block keep their original (empty) source. All cells share one namespace, like a kernel;
an error in one cell is reported and the run continues.
The snapshot files of Task 4 go to <snap dir> (C1_SNAP_DIR), which must be OUTSIDE the workspace for tests.

Run from rag_learning/ (the solutions file lives OUTSIDE the workspace, e.g. in the session scratchpad):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_lab_runner.py labs/C1_parsing_lab.ipynb <solutions.py> <snap dir>
"""
import contextlib
import io
import json
import os
import re
import sys
import traceback

nb_path, sol_path, snap_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ["C1_SNAP_DIR"] = snap_dir
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
    print(f"{'PASS' if ok else 'FAIL'} cell {i}: {label[:60]}" + ("" if ok else f" -> {err[:160]}"))
print(f"{sum(ok for *_, ok, _ in results)}/{len(results)} CHECK cells pass")
