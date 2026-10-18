"""I4: check the HTML lesson study/lessons/I4_propositions.html against the measured facts.

1. The embedded data block (units, the 40 tutor propositions, the planted mistakes, chunk ranges) equals what
   i4_kit_measure.py computes: unit texts and offsets, spans, parents, align values, unsupported words.
2. Numbers: every decimal number and every integer >= 10 in the lesson's visible text is printed in
   out_i4_kit_measure.txt (after removing thousands separators), or is on the DERIVED / EXTERNAL / STRUCTURAL lists
   below with its reason. The made-up ranked lists in the script (K7) are compared with the K7 output.
3. The step anchors of the build spec exist; every in-page #link resolves; every data-kit path exists on disk.
4. The coach-banned phrases are absent; the page loads nothing from the network (no http(s) src/href except none).
5. Honesty labels are present: "hand-written", "made-up", "not re-opened", "assumed".
No API call, no network. Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I4/i4_lesson_check.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        "<Book RAG>/upstream/RAG_Techniques/all_rag_techniques/proposition_chunking.ipynb" \
        > sources/verification/I4/out_i4_lesson_check.txt
"""
import contextlib
import html as H
import io
import json
import re
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
LESSON = WS / "study" / "lessons" / "I4_propositions.html"
OUT = (HERE / "out_i4_kit_measure.txt").read_text(encoding="utf-8")
n = fails = 0


def check(ok, label):
    global n, fails
    n += 1
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} {label}")


src = LESSON.read_text(encoding="utf-8")
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(HERE / "i4_kit_measure.py"), run_name="i4")
U, RT, RP = g["UNITS"], g["RT"], g["RP"]

# ---------------------------------------------------------------- 1. embedded data = measured data
m = re.search(r"const D = (\{.*?\});\n", src, re.S)
D = json.loads(m.group(1).replace("<\\/", "</"))
bad = [u for u, x in D["units"].items() if re.sub(r"\s+", " ", U[u]["text"]) != x["t"] or (U[u]["a"], U[u]["b"], U[u]["da"], U[u]["db"]) != (x["a"], x["b"], x["da"], x["db"]) or U[u]["kind"] != x["k"]]
check(not bad, f"{len(D['units'])} embedded units equal the splitter's units (text, kind, offsets) {bad}")
bad = [p["id"] for p in D["props"] if list(RT[p["id"]]["span"]) != p["span"] or RT[p["id"]]["parents"] != p["par"] or round(RT[p["id"]]["align"], 3) != p["al"]]
check(len(D["props"]) == 40 and not bad, f"40 embedded propositions: spans, parents, align equal K4 {bad}")
bad = [p["id"] for p in D["plant"] if RP[p["id"]].get("unsupported") != p["un"]]
check(len(D["plant"]) == 6 and not bad, f"6 planted mistakes: unsupported words equal K5 {bad}")
ch = {c["seq"]: c for c in g["chunks"]}
bad = [k for k, v in D["chunks"].items() if [ch[int(k)]["char_start"], ch[int(k)]["char_end"], ch[int(k)]["page_segments"][0]["page"]] != v]
check(not bad, f"embedded chunk ranges equal the 97 v0 chunks {bad}")
check(sorted(D["stop"]) == sorted(g["STOP"]), "embedded stop-word list equals i4_kit_measure.STOP")

# K7 lists in the script vs the measured K7 output
k7 = OUT.split("=== K7")[1].split("=== K8")[0]
for key, qid in (("D-002", "D-002"), ("D-007a", "D-007"), ("D-007b", "D-007"), ("D-005", "D-005")):
    blk = re.search(r'\{ key: "' + key + r'".*?rows: (\[\[.*?\]\]),', src, re.S)
    rows = json.loads(blk.group(1).replace('"', '"'))
    ok = all(re.search(rf"{qid} rank {i + 1}: {pid} parent {par} .*?span-overlaps-gold={ov}", k7) for i, (pid, par, ov, _) in enumerate(rows))
    check(ok, f"scoring list {key}: ranks, parents and gold overlap match K7")

# ---------------------------------------------------------------- 2. numbers in the visible text
body = src.split("<body>")[1].split("<script>")[0]
text = H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<pre>.*?</pre>", " ", body, flags=re.S)))
outnums = set(re.findall(r"\d+(?:\.\d+)?", OUT.replace(",", "")))
DERIVED = {"0.267": "1/sqrt(14), the K8 formula at n = 14", "14": "propositions with parent 27 in K4 (p10-01..p10-14); also 'about 14 per chunk' = 1,400 / 97",
           "36": "not used", "20555": "page 10 start = doc offset of unit 10:0 (K3)",
           "951": "length of chunk 27 = 21506 - 20555 (K4 chunk range, embedded data)",
           "110": "the verify notebook's check count (out_i4_verify_nb_run.txt)"}
EXTERNAL = {"2023": "Dense X year", "2026": "Zhou et al. year", "2024": "LumberChunker year", "0.3888": "Zhou et al. (research, search-checked)",
            "0.4849": "Zhou et al. (research, search-checked)", "41": "Dense X 41M passages (README)", "10": "various small counts", "0.075": "price (LLMOPS 6.2)",
            "0.30": "price (LLMOPS 6.2)", "200": "200K TPD / 200-char overlap", "8": "8K TPM / 8-gram", "1.6.6": "langchain-core version", "0.2.0": "langchain tag",
            "1.0.8": "langchain-classic version", "009": "commit 009adba", "12": "dev 12-16 items (research summary)", "16": "dev 12-16 items / p.10 sentences",
            "0.4": "smallest detectable CE@4 difference (research summary)", "2.7": "Dense X supervised gain (search-checked)", "30": "hand sample size", "60": "hand sample size",
            "06": "plan file 06", "07": "plan file 07", "1000": "per 1k chunks", "1536": "Cohere default dimension (LLMOPS 6.2)", "1998": "the made-up library example",
            "0.85": "the faithfulness bar the research sets", "0.60": "the toy distractor", "1969": "the repo's example sentence", "11": "Apollo 11 / 11 headings",
            "0.9": "checklist C6 bar (research)", "8000": "LangChain template parents of 8,000 chars (research, verified)",
            "2.3": "plan section 06 §2.3", "6.7": "plan section 06 §6.7", "15": "book pages /15", "13": "book page 13/15", "100": "per 100", "5.5": "Claude model names"}
STRUCT = {"2": "small", "1": "small"}
found = sorted(set(re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)*", text)), key=lambda s: float(".".join(s.replace(",", "").split(".")[:2])))
unknown = []
for s in found:
    v = s.replace(",", "")
    if "." not in v and int(v) < 10:
        continue
    if v in outnums or v in DERIVED or v in EXTERNAL or v in STRUCT or v.lstrip("0") in outnums:
        continue
    unknown.append(s)
check("110 checks passed / 0 failed" in (HERE / "out_i4_verify_nb_run.txt").read_text(encoding="utf-8"), "the notebook count on the page (110) is the saved run's count")
check(not unknown, f"every decimal and every integer >= 10 in the visible text traces to out_i4_kit_measure.txt or a listed reason "
                   f"({len(found)} distinct numbers; untraced: {unknown})")
used_ext = sorted(k for k in EXTERNAL if re.search(rf"(?<![\w.]){re.escape(k)}(?![\w])", text))
print(f"  numbers allowed as EXTERNAL / structural and present: {used_ext}")

# ---------------------------------------------------------------- 3. anchors and links
ids = set(re.findall(r'\sid="([^"]+)"', src))
STEPS = ["answer", "theory", "glance", "dilution", "proposition", "decontext", "units", "prompt", "anchor", "align", "grade", "score",
         "relations", "cost", "project", "repo", "research", "book", "verify", "apply", "check"]
check(all(s in ids for s in STEPS), f"all {len(STEPS)} spec anchors exist")
hrefs = re.findall(r'href="#([^"]+)"', src)
check(all(h in ids for h in hrefs), f"all {len(hrefs)} in-page links resolve")
kit = re.findall(r'data-path="rag_learning/([^"]+)"', src)
missing = [k for k in kit if not (WS / k).exists()]
check(not missing, f"every data-path target exists on disk ({len(kit)} links; missing {missing})")
check(all((WS / "study" / "lessons" / f).exists() for f in re.findall(r'url\("(fonts/[^"]+)"\)', src)), "bundled fonts exist")

# ---------------------------------------------------------------- 4. banned phrases, network
BANNED = ["a guide says", "well above zero", "narrow positive band", "who is right", "sixth", "add a pdf", "adding a document",
          "new document", "another pdf", "tenant", "300 pdf"]
low = H.unescape(re.sub(r"<[^>]+>", " ", src)).lower()
check(not [b for b in BANNED if b in low], f"none of the {len(BANNED)} coach-banned phrases appears")
net = re.findall(r'(?:src|href)="(https?://[^"]+)"', src) + re.findall(r"fetch\(|XMLHttpRequest|import\(", src)
check(not net, f"the page loads nothing from the network ({net})")

# ---------------------------------------------------------------- 5. honesty labels
for phrase in ("hand-written", "made-up order", "not re-opened", "assumed", "No LLM has written propositions"):
    check(phrase in src, f"label present: {phrase!r}")

print(f"\n{n - fails}/{n} checks passed")
sys.exit(0 if fails == 0 else 1)
