"""C6: interface checks between 06 (spec) and 07 (chunker code) that the v0 lessons must agree on.

Usage (from rag_learning/):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C6/c6_interface_checks.py <climate.pdf>
Checks:
  I1  06 sec. 2.4 YAML lists separators ["\\n\\n", "\\n", " ", ""]; 07 H.1 recursive_chunks has a built-in
      character fallback and its default is ("\\n\\n", "\\n", " "). Does passing "" to the 07 code terminate when
      a piece reaches the "" level? (child process with a timeout, so a hang cannot block this script)
  I2  The 06 YAML chunker name "recursive_char" vs the 07 REGISTRY keys ("fixed", "recursive").
  I3  A 20-char toy text where no piece reaches the "" level: same spans with and without "".
  I4  Corpus D per page with the 06 separator list: same spans as v0? (child process, timeout)
Saved output: sources/verification/C6/out_c6_interface_checks.txt
"""
import re
import subprocess
import sys
import types
from pathlib import Path

WS = Path(__file__).resolve().parents[3]
md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
PDF = sys.argv[1] if len(sys.argv) > 1 else None


def code_blocks(md, lang):
    return re.findall(r"^```" + re.escape(lang) + r"[ \t]*\n(.*?)^```", md, flags=re.S | re.M)


h1 = next(b for b in code_blocks(md07, "python") if "def recursive_chunks" in b and "def _split_spans" in b)
h3 = next(b for b in code_blocks(md07, "python") if "class ChunkerConfig" in b)
yaml_block = next(b for b in code_blocks(md06, "yaml") if "E000_v0_baseline" in b)

# child programs read the 07 H.1 code from stdin; the module is registered so @dataclass works
PRELUDE = ("import sys, types\n"
           "core = types.ModuleType('c07'); sys.modules['c07'] = core\n"
           "exec(compile(sys.stdin.read(), '07_H1', 'exec'), core.__dict__)\n"
           "SEP06 = ('\\n\\n', '\\n', ' ', '')\n")
CHILD_HANG = PRELUDE + (
    "text = 'word ' * 400 + 'x' * 1200   # a 1,200-char run with no whitespace must reach the '' level\n"
    "out = core.recursive_chunks(text, 1000, 200, separators=SEP06)\n"
    "print('returned', len(out), 'chunks')\n")
CHILD_D = PRELUDE + (
    "import re, pymupdf\n"
    "pages = [p.get_text() for p in pymupdf.open(sys.argv[1])]\n"
    "a = [[(c.char_start, c.char_end) for c in core.recursive_chunks(p, 1000, 200)] for p in pages]\n"
    "b = [[(c.char_start, c.char_end) for c in core.recursive_chunks(p, 1000, 200, SEP06)] for p in pages]\n"
    "longest = max(len(m) for p in pages for m in re.findall(r'\\S+', p))\n"
    "print('spans identical:', a == b, '| chunks:', sum(map(len, a)), '| longest whitespace-free run:', longest, 'chars')\n")


def run_child(code, args=(), timeout=30):
    try:
        r = subprocess.run([sys.executable, "-c", code, *args], input=h1, capture_output=True, text=True, timeout=timeout)
        return f"child exit {r.returncode} | " + (r.stdout or r.stderr).strip()[-300:]
    except subprocess.TimeoutExpired:
        return f"TIMEOUT: the child did not finish within {timeout} s"


print("=== I1 06 YAML separators vs 07 code")
print("06 sec. 2.4 separators:", re.search(r"separators:\s*(\[.*?\])", yaml_block).group(1))
print("07 H.1 DEFAULT_SEPARATORS:", re.search(r"DEFAULT_SEPARATORS = (.*)", h1).group(1))
print("text with a 1,200-char whitespace-free run, separators incl. '':", run_child(CHILD_HANG, timeout=20))
print("why: in _split_spans, text.find('', i, end) returns i, so the piece is (i, i) and i never advances")

print("\n=== I2 chunker name")
print("06 sec. 2.4 chunking.name:", re.search(r"name:\s*(\S+)", yaml_block.split("chunking:")[1]).group(1))
print("07 H.3 REGISTRY keys:", re.findall(r'^\s+"(\w+)": lambda cfg', h3, flags=re.M))

print("\n=== I3 a 20-char toy text where no piece reaches the '' level")
core = types.ModuleType("c07")
sys.modules["c07"] = core
exec(compile(h1, "07_H1", "exec"), core.__dict__)
t = "aaaa bbbb\ncccc dddd."
a = [(c.char_start, c.char_end) for c in core.recursive_chunks(t, 10, 4)]
b = [(c.char_start, c.char_end) for c in core.recursive_chunks(t, 10, 4, separators=("\n\n", "\n", " ", ""))]
print("default separators:", a, "| with '':", b, "| same:", a == b)

print("\n=== I4 Corpus D per page with the 06 separator list")
print(run_child(CHILD_D, (PDF,), timeout=60) if PDF else "skipped (pass the PDF path as argv[1])")
