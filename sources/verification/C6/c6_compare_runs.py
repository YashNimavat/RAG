"""C6: compare two reference v0 runs (rebuild reproducibility; 02 Gate 2->3 item 4; 04 C6 gate check).

Usage (from rag_learning/):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C6/c6_compare_runs.py <run1_dir> <run2_dir>
Compares: params_hash and chunk ids, every index file byte for byte, the config, and the trace records with the
volatile fields (timestamp_utc, latency_ms) removed. Prints PASS/FAIL lines.
"""
import hashlib
import json
import sys
from pathlib import Path

A, B = Path(sys.argv[1]), Path(sys.argv[2])
fails = 0


def check(ok: bool, label: str) -> None:
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def only_dir(root: Path) -> Path:
    dirs = [p for p in (root / "index").glob("*/*/*") if p.is_dir()]
    assert len(dirs) == 1, dirs
    return dirs[0]


ia, ib = only_dir(A), only_dir(B)
check(ia.relative_to(A) == ib.relative_to(B), f"same index path: {ia.relative_to(A).as_posix()}")
ma, mb = json.loads((ia / "manifest.json").read_text()), json.loads((ib / "manifest.json").read_text())
check(ma["params_hash"] == mb["params_hash"], f"params_hash identical: {ma['params_hash']}")
ida = [json.loads(l)["chunk_id"] for l in (ia / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
idb = [json.loads(l)["chunk_id"] for l in (ib / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
check(ida == idb, f"chunk_id lists identical ({len(ida)} ids)")
for f in ("vectors.npy", "chunks.jsonl", "manifest.json"):
    check(sha(ia / f) == sha(ib / f), f"{f} byte-identical (sha256 {sha(ia / f)[:16]})")
for f in ("config.json", "snapshot_manifest.json"):
    check(sha(A / f) == sha(B / f), f"{f} byte-identical")
VOLATILE = ("timestamp_utc", "latency_ms")
ta = [json.loads(l) for l in (A / "results.jsonl").read_text(encoding="utf-8").splitlines()]
tb = [json.loads(l) for l in (B / "results.jsonl").read_text(encoding="utf-8").splitlines()]
strip = lambda r: {k: v for k, v in r.items() if k not in VOLATILE}
check(len(ta) == len(tb) == 10, f"{len(ta)} trace records each")
check([strip(r) for r in ta] == [strip(r) for r in tb], "trace records identical after removing timestamp_utc and latency_ms")
check(all(ra["candidates"] == rb["candidates"] for ra, rb in zip(ta, tb)), "retrieval part (candidates: ids, offsets, scores) identical")
raw_same = (A / "results.jsonl").read_bytes() == (B / "results.jsonl").read_bytes()
print(f"INFO results.jsonl byte-identical WITHOUT removing volatile fields: {raw_same} (expected False: timestamps and latencies differ)")
print("ALL PASS" if not fails else f"{fails} FAIL")
sys.exit(1 if fails else 0)
