"""Execute study/notebooks/C1_parsing_verify.ipynb top to bottom in a real Jupyter kernel, into a SCRATCH COPY.

Same kernel loop as sources/verification/P2/p2_verify_nb_run.py (jupyter_client + the project's ipykernel, kernel spec
`python3` of the uv environment; every code cell in one kernel, in order). Unlike P2's runner, the notebook in the
workspace is left as the builder wrote it (no outputs): the executed copy, with its outputs and the Plotly figures as
compact `application/vnd.plotly.v1+json` bundles, is written to <scratch dir>/C1_parsing_verify.executed.ipynb. The
kernel's working directory is study/notebooks/ so the notebook finds the workspace as it does when opened in VS Code.
The notebook makes no API call; its two toy PDFs go to the operating system's temporary folder and are deleted by its
last cell.

Reports: every PASS / FAIL / SKIPPED line, cell errors, the number of Plotly figures, the runtime, the sizes of the
workspace notebook and the executed copy, and the notebook's own "N checks passed / M failed" line. Exit code 0 only if
every check passed and no cell raised (a SKIPPED line is not a failure).

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_verify_nb_run.py <scratch dir> \
        > sources/verification/C1/out_c1_verify_nb_run.txt
"""
import copy
import json
import os
import re
import sys
import time
from pathlib import Path

import nbformat
from jupyter_client import KernelManager

WS = Path(__file__).resolve().parents[3]                       # rag_learning/
NB = WS / "study" / "notebooks" / "C1_parsing_verify.ipynb"
TIMEOUT = 900                                                  # seconds per cell
PLOTLY = "application/vnd.plotly.v1+json"


def write_compact(nb, path):
    """Write the notebook as nbformat does (indent 1), but each Plotly figure as one compact JSON value."""
    out = copy.deepcopy(nb)
    figs = {}
    for c in out.cells:
        for o in c.get("outputs", []):
            if PLOTLY in o.get("data", {}):
                key = f"@@plotly-figure-{len(figs)}@@"
                figs[key] = json.dumps(o["data"][PLOTLY], separators=(",", ":"), ensure_ascii=False)
                o["data"][PLOTLY] = key
    text = nbformat.writes(out, version=4)
    for key, value in figs.items():
        text = text.replace(json.dumps(key), value, 1)
    Path(path).write_text(text, encoding="utf-8")
    back = nbformat.read(str(path), as_version=4)
    nbformat.validate(back)
    assert sum(PLOTLY in o.get("data", {}) for c in back.cells for o in c.get("outputs", [])) == len(figs)


def run(nb_path, out_path):
    nb = nbformat.read(str(nb_path), as_version=4)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    km = KernelManager(kernel_name="python3")
    km.start_kernel(cwd=str(nb_path.parent), env=env)
    kc = km.client()
    kc.start_channels()
    errors = []
    t0 = time.time()
    try:
        kc.wait_for_ready(timeout=120)
        for idx, cell in enumerate(nb.cells):
            if cell.cell_type != "code":
                continue
            msg_id = kc.execute(cell.source, store_history=True)
            outputs, count = [], None
            while True:
                msg = kc.get_iopub_msg(timeout=TIMEOUT)
                if msg["parent_header"].get("msg_id") != msg_id:
                    continue
                kind, content = msg["msg_type"], msg["content"]
                if kind == "status" and content["execution_state"] == "idle":
                    break
                if kind == "execute_input":
                    count = content.get("execution_count")
                elif kind == "stream":
                    if outputs and outputs[-1].get("output_type") == "stream" and outputs[-1]["name"] == content["name"]:
                        outputs[-1]["text"] += content["text"]
                    else:
                        outputs.append(nbformat.v4.new_output("stream", name=content["name"], text=content["text"]))
                elif kind in ("display_data", "execute_result"):
                    kw = {"data": content["data"], "metadata": content.get("metadata", {})}
                    if kind == "execute_result":
                        kw["execution_count"] = content.get("execution_count")
                    outputs.append(nbformat.v4.new_output(kind, **kw))
                elif kind == "error":
                    outputs.append(nbformat.v4.new_output("error", ename=content["ename"], evalue=content["evalue"],
                                                          traceback=content["traceback"]))
                    errors.append((idx, f"{content['ename']}: {content['evalue']}"))
                elif kind == "clear_output":
                    outputs = []
            kc.get_shell_msg(timeout=TIMEOUT)
            cell.outputs, cell.execution_count = outputs, count
    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)
    runtime = time.time() - t0
    write_compact(nb, out_path)
    text = "\n".join(o.get("text", "") for c in nb.cells if c.cell_type == "code" for o in c.outputs
                     if o.get("output_type") == "stream")
    return nb, text, errors, runtime


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: c1_verify_nb_run.py <scratch dir outside the workspace>")
    scratch = Path(sys.argv[1]).resolve()
    if WS in (scratch, *scratch.parents):
        sys.exit("the scratch dir must be outside the workspace")
    scratch.mkdir(parents=True, exist_ok=True)
    out = scratch / "C1_parsing_verify.executed.ipynb"
    nb, text, errors, runtime = run(NB, out)
    summary = re.search(r"^(\d+) checks passed / (\d+) failed", text, re.M)
    for line in text.splitlines():
        if line.startswith(("PASS ", "FAIL ", "SKIPPED ")):
            print(line)
    n_fig = sum(1 for c in nb.cells if c.cell_type == "code" for o in c.outputs if PLOTLY in o.get("data", {}))
    print(f"cells with errors: {len(errors)}" + "".join(f"\n   cell {i}: {e}" for i, e in errors))
    print(f"Plotly figures: {n_fig}; runtime {runtime:.1f} s; workspace notebook {NB.relative_to(WS)} "
          f"{NB.stat().st_size / 1024:.0f} KiB (no outputs); executed copy {out.stat().st_size / 1024:.0f} KiB")
    print(summary.group(0) if summary else "no summary line found (the last cell did not run)")
    print(f"SKIPPED lines: {sum(1 for l in text.splitlines() if l.startswith('SKIPPED '))}")
    ok = bool(summary) and summary.group(2) == "0" and not errors
    sys.exit(0 if ok else 1)
