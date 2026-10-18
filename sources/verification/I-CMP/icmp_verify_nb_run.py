"""Execute study/notebooks/I-CMP_granularity_verify.ipynb top to bottom in a real Jupyter kernel and save it WITH outputs.

Same runner as sources/verification/P2/p2_verify_nb_run.py, pointed at the I-CMP notebook. Uses jupyter_client + the
project's ipykernel (the kernel spec `python3` of the uv environment). Every code cell runs in one kernel, in order; the
outputs (text, tables, Plotly figures as the small `application/vnd.plotly.v1+json` bundle, errors) are written back
into the notebook, so the charts show when the notebook is opened in VS Code. No plotly.js is embedded. The notebook
makes no API call; HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE are set for the kernel.

Reports: the notebook's own "N checks passed / M failed" line, every FAIL and SKIPPED line, cell errors, the runtime
and the saved file size. Exit code 0 only if every check passed and no cell raised (a SKIPPED line is not a failure:
the MiniLM-dependent checks skip, with a reason, if the model is not in the local cache).

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I-CMP/icmp_verify_nb_run.py \
        > sources/verification/I-CMP/out_icmp_verify_nb_run.txt
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
NB = WS / "study" / "notebooks" / "I-CMP_granularity_verify.ipynb"
TIMEOUT = 900                                                  # seconds per cell
PLOTLY = "application/vnd.plotly.v1+json"


def write_compact(nb, path):
    """Write the notebook as nbformat does (indent 1), but each Plotly figure as one compact JSON value, so its
    number arrays are not spread one number per line. The result is ordinary notebook JSON; it is read back and
    validated before this returns."""
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


def run(nb_path=NB):
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
    write_compact(nb, nb_path)
    text = "\n".join(o.get("text", "") for c in nb.cells if c.cell_type == "code" for o in c.outputs
                     if o.get("output_type") == "stream")
    return nb, text, errors, runtime


if __name__ == "__main__":
    nb, text, errors, runtime = run()
    summary = re.search(r"^(\d+) checks passed / (\d+) failed", text, re.M)
    for line in text.splitlines():
        if line.startswith(("FAIL ", "SKIPPED ")):
            print(line)
    n_fig = sum(1 for c in nb.cells if c.cell_type == "code" for o in c.outputs
                if "application/vnd.plotly.v1+json" in o.get("data", {}))
    print(f"cells with errors: {len(errors)}" + "".join(f"\n   cell {i}: {e}" for i, e in errors))
    print(f"Plotly figures saved: {n_fig}; runtime {runtime:.1f} s; file {NB.relative_to(WS)} "
          f"{NB.stat().st_size / 1024:.0f} KiB")
    print(summary.group(0) if summary else "no summary line found (the last cell did not run)")
    print(f"SKIPPED lines: {sum(1 for l in text.splitlines() if l.startswith('SKIPPED '))}")
    ok = bool(summary) and summary.group(2) == "0" and not errors
    sys.exit(0 if ok else 1)
