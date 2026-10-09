"""Execute labs/C2_chunking_lab.ipynb top to bottom in ONE namespace (like a kernel), with the learner/prediction
cells replaced by blocks from a solutions file, and report every CHECK cell as PASS or FAIL. Contains no solution code.

Solutions file format: blocks that start with a line '# == <task id>' (the `task` value in the cell metadata).
Cells without a matching block keep their original (empty) source. Pass '-' to run the notebook as shipped.
The working directory is switched to <workdir> (default: a fresh temp dir), so the save cell writes there, never
into the workspace.

Run from rag_learning/:
    uv run python sources/verification/C2lab/c2_lab_runner.py labs/C2_chunking_lab.ipynb <solutions.py | -> [workdir]
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2_common import read_blocks  # noqa: E402

nb_path = os.path.abspath(sys.argv[1])
sol_path = sys.argv[2]
workdir = sys.argv[3] if len(sys.argv) > 3 else tempfile.mkdtemp(prefix="c2lab_")
blocks = {} if sol_path == "-" else read_blocks(sol_path)
cells = json.load(open(nb_path, encoding="utf-8"))["cells"]
os.makedirs(workdir, exist_ok=True)
os.chdir(workdir)

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
    print(f"{'PASS' if ok else 'FAIL'} cell {i}: {label}" + ("" if ok else f"  <- {err[:170]}"))
n_ok = sum(ok for *_, ok, _ in results)
print(f"{n_ok}/{len(results)} CHECK cells passed")
