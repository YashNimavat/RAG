"""Run labs/C2_chunking_lab.ipynb in a REAL Jupyter kernel (the project's ipykernel, via jupyter_client),
on a temp copy OUTSIDE the workspace, with learner/prediction cells filled from a solutions file ('-' = as shipped).
Reports each CHECK cell as PASS/FAIL from the kernel's own replies, and saves the executed copy next to it.
(nbconvert is not installed in the project env and nothing is installed for this; jupyter_client ships with ipykernel.)

Run from rag_learning/:
    uv run python sources/verification/C2lab/c2_kernel_runner.py labs/C2_chunking_lab.ipynb <solutions.py | -> <outdir outside WS>
"""
import json
import os
import sys

from jupyter_client.manager import start_new_kernel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2_common import read_blocks  # noqa: E402

nb_path, sol_path, outdir = os.path.abspath(sys.argv[1]), sys.argv[2], os.path.abspath(sys.argv[3])
ws = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
assert not outdir.lower().startswith(ws.lower()), "outdir must be outside the workspace"
os.makedirs(outdir, exist_ok=True)
blocks = {} if sol_path == "-" else read_blocks(sol_path)
nb = json.load(open(nb_path, encoding="utf-8"))
for c in nb["cells"]:
    t = c["metadata"].get("task")
    if c["cell_type"] == "code" and t in blocks:
        c["source"] = blocks[t].splitlines(keepends=True)
copy_path = os.path.join(outdir, "C2_chunking_lab.filled.ipynb")
json.dump(nb, open(copy_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

km, kc = start_new_kernel(kernel_name="python3", cwd=outdir)
results = []
try:
    info = kc.execute_interactive("import sys, os; print(sys.executable); print(os.getcwd())", timeout=60,
                                  output_hook=lambda m: m["msg_type"] == "stream" and print("kernel:", m["content"]["text"].strip()))
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        outputs = []

        def hook(msg, outputs=outputs):
            if msg["msg_type"] == "stream":
                outputs.append({"output_type": "stream", "name": msg["content"]["name"], "text": msg["content"]["text"]})
            elif msg["msg_type"] == "error":
                outputs.append({"output_type": "error", "ename": msg["content"]["ename"], "evalue": msg["content"]["evalue"],
                                "traceback": msg["content"]["traceback"]})
        reply = kc.execute_interactive(src, timeout=600, output_hook=hook)
        c["outputs"] = outputs
        ok = reply["content"]["status"] == "ok"
        tags = c["metadata"].get("tags", [])
        if "check" in tags:
            err = "" if ok else f"{reply['content'].get('ename')}: {reply['content'].get('evalue')}"
            results.append((i, src.splitlines()[0], ok, err))
finally:
    kc.stop_channels()
    km.shutdown_kernel(now=True)

json.dump(nb, open(os.path.join(outdir, "C2_chunking_lab.executed.ipynb"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for i, label, ok, err in results:
    print(f"{'PASS' if ok else 'FAIL'} cell {i}: {label}" + ("" if ok else f"  <- {err[:170]}"))
print(f"{sum(r[2] for r in results)}/{len(results)} CHECK cells passed (real kernel)")
print("files written by the save cell:", sorted(os.path.relpath(os.path.join(d, f), outdir)
                                                 for d, _, fs in os.walk(os.path.join(outdir, "C2_out")) for f in fs))
