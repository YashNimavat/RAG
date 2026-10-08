"""Relocation of 2026-10-08: everything now lives under C:\\Yash\\New-Work\\Book RAG.
Rewrites absolute paths in the workspace's own documents and scripts.
Historical records keep their original paths and are NOT rewritten:
  - Codex's reports (reviews/CODEX_REVIEW_2026-10-08.md, reviews/CODEX_REREVIEW*_2026-10-08.md)
  - lab run records (sources/verification/LAB_FACTS.md, sources/verification/labscripts/out_*.txt)
Run from the workspace root: python -I sources/verification/relocate_paths.py"""
import pathlib

MAP = [  # (old, new) — longest first; backslash and forward-slash forms
    (r"C:\Yash\New-Work\RAG\rag_learning", r"C:\Yash\New-Work\Book RAG\rag_learning"),
    ("C:/Yash/New-Work/RAG/rag_learning", "C:/Yash/New-Work/Book RAG/rag_learning"),
    (r"C:\Yash\New-Work\RAG\upstream\RAG_Techniques", r"C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques"),
    ("C:/Yash/New-Work/RAG/upstream/RAG_Techniques", "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques"),
    (r"C:\Users\Yash\Documents\BOOK\RAG_Made_Simple_The_Complete_Visual_Guide",
     r"C:\Yash\New-Work\Book RAG\RAG_Made_Simple_The_Complete_Visual_Guide"),
    ("C:/Users/Yash/Documents/BOOK/RAG_Made_Simple_The_Complete_Visual_Guide",
     "C:/Yash/New-Work/Book RAG/RAG_Made_Simple_The_Complete_Visual_Guide"),
    (r"C:\Users\Yash\Documents\BOOK\\", r"C:\Yash\New-Work\Book RAG\\"),
]
HISTORICAL = {"reviews/CODEX_REVIEW_2026-10-08.md", "reviews/CODEX_REREVIEW_2026-10-08.md",
              "reviews/CODEX_REREVIEW2_2026-10-08.md", "sources/verification/LAB_FACTS.md",
              "sources/verification/relocate_paths.py"}
root = pathlib.Path(".")
total = 0
for p in sorted(root.rglob("*")):
    rel = p.relative_to(root).as_posix()
    if not p.is_file() or p.suffix not in {".md", ".py", ".csv", ".json", ".txt", ".yaml", ".yml"}:
        continue
    if rel in HISTORICAL or (rel.startswith("sources/verification/labscripts/out_")):
        continue
    raw = p.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        continue
    n = 0
    for old, new in MAP:
        c = t.count(old)
        if c:
            t = t.replace(old, new)
            n += c
    if n:
        p.write_bytes(t.encode("utf-8"))
        total += n
        print(f"{n:3d}  {rel}")
print("total replacements:", total)
