"""Second relocation step (2026-10-08): the learner's prior work was copied (source files only) into
C:\\Yash\\New-Work\\Book RAG\\prior_work\\. Point the workspace's own documents at those copies.
Historical records are not rewritten (same rule as relocate_paths.py).
Run from the workspace root: python -I sources/verification/relocate_prior_work.py"""
import pathlib

PAIRS = []
for name in ("my way", "VAI", "RAG book step by step"):
    PAIRS += [(f"C:\\Yash\\New-Work\\RAG\\{name}", f"C:\\Yash\\New-Work\\Book RAG\\prior_work\\{name}"),
              (f"C:/Yash/New-Work/RAG/{name}", f"C:/Yash/New-Work/Book RAG/prior_work/{name}")]
HISTORICAL = {"reviews/CODEX_REVIEW_2026-10-08.md", "reviews/CODEX_REREVIEW_2026-10-08.md",
              "reviews/CODEX_REREVIEW2_2026-10-08.md", "sources/verification/LAB_FACTS.md",
              "sources/verification/relocate_paths.py", "sources/verification/relocate_prior_work.py"}
root = pathlib.Path(".")
total = 0
for p in sorted(root.rglob("*")):
    rel = p.relative_to(root).as_posix()
    if (not p.is_file() or rel.startswith((".venv/", ".git/")) or p.suffix not in {".md", ".py", ".csv", ".json", ".txt"}
            or rel in HISTORICAL or rel.startswith("sources/verification/labscripts/out_")):
        continue
    try:
        t = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    n = sum(t.count(a) for a, _ in PAIRS)
    if n:
        for a, b in PAIRS:
            t = t.replace(a, b)
        p.write_bytes(t.encode("utf-8"))
        total += n
        print(f"{n:3d}  {rel}")
print("total replacements:", total)
