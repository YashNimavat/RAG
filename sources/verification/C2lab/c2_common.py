"""Shared helpers for the C2 lab tooling: read a solutions file in block format, run setup + blocks."""
import re

from c2_setup import SETUP


def read_blocks(path: str) -> dict[str, str]:
    """Blocks start with a line '# == <task id>'; text before the first marker is ignored."""
    blocks, cur = {}, None
    for line in open(path, encoding="utf-8").read().splitlines(keepends=True):
        m = re.match(r"# == (\S+)\s*$", line)
        if m:
            cur = m.group(1)
            blocks[cur] = ""
        elif cur:
            blocks[cur] += line
    return blocks


TASK_ORDER = ["T1", "T2", "T3", "T4p", "T4", "T5p", "T5", "T6p", "T6", "T7", "T8p", "T8"]


def run_reference(sol_path: str, quiet: bool = True) -> dict:
    """Execute the given setup cell and every solution block, in notebook order, in one namespace."""
    import contextlib
    import io
    ns = {"__name__": "__main__"}
    blocks = read_blocks(sol_path)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf) if quiet else contextlib.nullcontext():
        exec(compile(SETUP, "<setup>", "exec"), ns)
        for t in TASK_ORDER:
            exec(compile(blocks[t], f"<{t}>", "exec"), ns)
    return ns
