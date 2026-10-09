"""C1 S11: does the same PDF give the same text under another parser, or another parser version?

Runs under ANY interpreter that has pymupdf (and optionally pypdf). It was run twice:
  (a) the project env (pymupdf 1.26.7, no pypdf):
      PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_crossversion.py "<climate pdf>"
  (b) a throwaway venv in the session scratchpad, OUTSIDE the workspace (pymupdf 1.28.2 + pypdf 6.19.0;
      created with `uv venv` + `uv pip install pypdf==6.19.0 pymupdf==1.28.2`; nothing is installed into the
      project env):
      PYTHONIOENCODING=utf-8 <scratch venv>/Scripts/python.exe -I sources/verification/C1/c1_crossversion.py "<climate pdf>"
pypdf 6.19.0 is the version behind the 07 lab's PyPDFLoader numbers (LAB_FACTS §0, §7); PyPDFLoader wraps
pypdf's page.extract_text(), so the total is cross-checked against LAB_FACTS' 72,523 characters.
Saved outputs: out_c1_crossversion_project.txt, out_c1_crossversion_scratchenv.txt
"""
import hashlib
import re
import sys

import pymupdf as fitz

PDF = sys.argv[1]
REF_DOC_SHA = "5106772efa77003b0d6c79bc1a429b8dacf244d9556f412bae1c4fe6bc7368c6"   # 06 section 5.3, pymupdf 1.26.7


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def words(s):
    return re.findall(r"\w+", s)


print("python", sys.version.split()[0], "| pymupdf", fitz.VersionBind)
mu = [p.get_text() for p in fitz.open(PDF)]
doc = "\n".join(mu)
print("pymupdf: pages", len(mu), "| len(doc_text)", len(doc), "| doc_text_sha256", sha(doc)[:16],
      "| equals the 1.26.7 value in 06 section 5.3:", sha(doc) == REF_DOC_SHA)
try:
    import pypdf
except ImportError:
    print("pypdf not available in this interpreter")
    sys.exit(0)
print("pypdf", pypdf.__version__)
pp = [p.extract_text() for p in pypdf.PdfReader(PDF).pages]
print("pypdf extract_text: pages", len(pp), "| joined with \\n:", len("\n".join(pp)), "(LAB_FACTS PyPDFLoader: 72523)")
print("pages with identical text, pypdf vs pymupdf:", sum(a == b for a, b in zip(pp, mu)), "of", len(mu))
print("pages with the same word sequence (\\w+):", sum(words(a) == words(b) for a, b in zip(pp, mu)), "of", len(mu))
for i, (a, b) in enumerate(zip(pp, mu), 1):
    wa, wb = words(a), words(b)
    if wa != wb:
        k = next((j for j in range(min(len(wa), len(wb))) if wa[j] != wb[j]), min(len(wa), len(wb)))
        print(f"  first word difference p.{i}: pypdf {wa[k:k + 4]} | pymupdf {wb[k:k + 4]}")
print("pypdf: lines ending with a space", sum(1 for t in pp for ln in t.split("\n") if ln.endswith(" ")),
      "of", sum(t.count("\n") + 1 for t in pp), "| pages ending with \\n:", sum(t.endswith("\n") for t in pp))
print("pypdf page 1 last 12 chars", repr(pp[0][-12:]), "| pymupdf page 1 last 12 chars", repr(mu[0][-12:]))
print("pypdf page 1 first 40 chars", repr(pp[0][:40]))
print("pymupdf page 1 first 40 chars", repr(mu[0][:40]))
same_start = sum(a[:200] == b[:200] for a, b in zip(pp, mu))
print("pages whose first 200 characters are identical:", same_start, "of", len(mu))
print("pymupdf page == pypdf page + newline on", sum(b == a + "\n" for a, b in zip(pp, mu)), "of", len(mu), "pages")
