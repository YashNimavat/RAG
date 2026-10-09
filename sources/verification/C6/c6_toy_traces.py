"""C6: build the TOY traces for the lab's "which stage failed?" task, and check that the planted failures are what
the diagnosis ladder finds. Everything here is MADE UP (a toy "Harbour Lighthouse Manual"); nothing is a real run.

Usage (from rag_learning/):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C6/c6_toy_traces.py
Writes sources/verification/C6/toy_traces.json (the lab embeds the same JSON) and prints the planted labels,
the reference ladder's labels, and the fingerprints the lab's CHECK cells use.

The ladder (first failing stage, walking the trace from upstream to downstream):
  1 parse              the gold quote (what a human reads on the page) is not in the PARSED page text
  2 chunk              the quote is in the page text, but no chunk in the index holds it whole
  3 retrieve           some chunk holds it whole, but no CONTEXT chunk does
  4 generate:citation  the answer cites a (doc, page) that no context chunk comes from
  5 generate:abstain   the evidence is in the context, but the answer is the fixed refusal sentence
  6 generate:grounding a number in the answer does not appear in the text of the chunks it cites
  7 ok                 none of the above
Whitespace is normalised before every text comparison (06 sec. 2.4 tolerance: whitespace-only).
"""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ABSTAIN = "I cannot answer this from the provided documents."

PAGES = [  # parsed page text of the toy PDF (the "snapshot"); page 2 carries a hyphenation artifact
    "Harbour Lighthouse Manual\nLamp care\nReplace the main lamp every 2,000 hours of use.\n"
    "Clean the lens every week with a dry cloth.\n",
    "Power\nThe backup gen-\nerator must be tested every 30 days.\nKeep the fuel log next to the generator.\n",
    "Fuel\nThe two fuel tanks hold 400 litres in total and are refilled each May by the harbour office.\n",
    "Safety\nThe foghorn sounds twice every 20 seconds in fog.\nVisitors may climb the tower only with a keeper.\n",
    "Keepers\nEach keeper works a 12-hour shift.\nShift changes happen at 06:00 and 18:00.\n",
]
DOC = "toy"
SNAP = "toysnap00001"     # made-up snapshot id
PH = "toyparams001"       # made-up params hash
MAXLEN = 60               # the toy chunker: one chunk per line; a line longer than 60 chars is cut, no overlap


def build_chunks():
    doc_text = "\n".join(PAGES)
    chunks, pos = [], 0
    for p, page in enumerate(PAGES, 1):
        i = 0
        for line in page.split("\n"):
            j = 0
            while j < len(line):
                piece = line[j:j + MAXLEN]
                a = pos + i + j
                chunks.append({"chunk_id": f"{DOC}:{SNAP}:{PH}:{len(chunks):05d}", "doc_id": DOC, "page": p,
                               "char_start": a, "char_end": a + len(piece), "text": piece})
                j += MAXLEN
            i += len(line) + 1
        pos += len(page) + 1
    for c in chunks:
        assert doc_text[c["char_start"]:c["char_end"]] == c["text"]
    return doc_text, chunks


DOC_TEXT, CHUNKS = build_chunks()
BYTEXT = {c["text"]: c for c in CHUNKS}


def ids(*texts):
    return [BYTEXT[t]["chunk_id"] for t in texts]


# planted cases: (qid, planted label, question, gold page, gold quote, context chunk texts in rank order, answer)
CASES = [
    ("TOY-1", "ok", "How often should the main lamp be replaced?", 1,
     "Replace the main lamp every 2,000 hours of use.",
     ["Replace the main lamp every 2,000 hours of use.", "Lamp care"],
     "Replace the main lamp every 2,000 hours of use [toy:1]."),
    ("TOY-2", "parse", "How often must the backup generator be tested?", 2,
     "The backup generator must be tested every 30 days.",
     ["Keep the fuel log next to the generator.", "The backup gen-"],
     ABSTAIN),
    ("TOY-3", "chunk", "How much fuel do the tanks hold, and when are they refilled?", 3,
     "The two fuel tanks hold 400 litres in total and are refilled each May by the harbour office.",
     ["The two fuel tanks hold 400 litres in total and are refilled", "Fuel"],
     "The two fuel tanks hold 400 litres in total [toy:3]."),
    ("TOY-4", "retrieve", "How often does the foghorn sound in fog?", 4,
     "The foghorn sounds twice every 20 seconds in fog.",
     ["Clean the lens every week with a dry cloth.", "Visitors may climb the tower only with a keeper."],
     ABSTAIN),
    ("TOY-5", "generate:citation", "When do shift changes happen?", 5,
     "Shift changes happen at 06:00 and 18:00.",
     ["Shift changes happen at 06:00 and 18:00.", "Each keeper works a 12-hour shift."],
     "Shift changes happen at 06:00 and 18:00 [toy:4]."),
    ("TOY-6", "generate:grounding", "How long is a keeper's shift?", 5,
     "Each keeper works a 12-hour shift.",
     ["Each keeper works a 12-hour shift.", "Keepers"],
     "Each keeper works an 8-hour shift [toy:5]."),
    ("TOY-7", "retrieve", "How often should the lens be cleaned?", 1,
     "Clean the lens every week with a dry cloth.",
     ["The foghorn sounds twice every 20 seconds in fog.", "Each keeper works a 12-hour shift."],
     "Clean the lens every week with a dry cloth [toy:1]."),
]
TOY_SCORES = [0.71, 0.64]   # made-up scores for ranks 1-2 (toy k = 2)


def make_trace(qid, question, gold_page, quote, ctx_texts, answer):
    ctx = [BYTEXT[t] for t in ctx_texts]
    cits = [{"marker": m.group(0), "doc_id": m.group(1), "page": int(m.group(2)),
             "resolved_chunk_ids": [c["chunk_id"] for c in ctx if c["doc_id"] == m.group(1) and c["page"] == int(m.group(2))]}
            for m in re.finditer(r"\[([A-Za-z0-9_\-]+):(\d+)\]", answer)]
    return {
        "label": "TOY: made-up trace for the C6 lab; not a real run",
        "qid": qid, "snapshot_id": SNAP,
        "query": {"original": question},
        "gold": {"doc_id": DOC, "page": gold_page, "quote": quote},
        "candidates": {"dense": [{"rank": r, "chunk_id": c["chunk_id"], "doc_id": c["doc_id"], "page": c["page"],
                                  "char_start": c["char_start"], "char_end": c["char_end"], "score": s}
                                 for r, (c, s) in enumerate(zip(ctx, TOY_SCORES), 1)]},
        "context": {"chunk_ids": [c["chunk_id"] for c in ctx]},
        "answer": {"text": answer, "abstained": " ".join(answer.split()).strip('"').rstrip(".").lower() == ABSTAIN.rstrip(".").lower(),
                   "citations": cits},
    }


# ------------------------------------------------------------------ the reference ladder (a SOLUTION; not in the lab)
def norm(s):
    return " ".join(s.split())


def numbers(s):
    """Numbers in an answer, AFTER removing [doc:page] markers (else the page number counts as a claim)."""
    s = re.sub(r"\[[A-Za-z0-9_\-]+:\d+\]", "", s)
    return [n.rstrip(".,") for n in re.findall(r"\d[\d,:.]*", s)]


def first_failing_stage(trace, pages, chunks):
    by_id = {c["chunk_id"]: c for c in chunks}
    q = norm(trace["gold"]["quote"])
    if q not in norm(pages[trace["gold"]["page"] - 1]):
        return "parse"
    if not any(q in norm(c["text"]) for c in chunks):
        return "chunk"
    ctx = [by_id[i] for i in trace["context"]["chunk_ids"]]
    if not any(q in norm(c["text"]) for c in ctx):
        return "retrieve"
    pages_in_ctx = {(c["doc_id"], c["page"]) for c in ctx}
    cits = trace["answer"]["citations"]
    if any((x["doc_id"], x["page"]) not in pages_in_ctx for x in cits):
        return "generate:citation"
    if trace["answer"]["abstained"]:
        return "generate:abstain"
    cited_text = " ".join(c["text"] for c in ctx if (c["doc_id"], c["page"]) in {(x["doc_id"], x["page"]) for x in cits})
    if any(n not in cited_text for n in numbers(trace["answer"]["text"])):
        return "generate:grounding"
    return "ok"


def fp(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


def main():
    traces = [make_trace(qid, qu, gp, quote, ctx, ans) for qid, _, qu, gp, quote, ctx, ans in CASES]
    data = {"label": "TOY data for labs/C6_v0_pipeline.ipynb: a made-up 5-page manual, a naive toy chunker "
                     "(one chunk per line, lines cut at 60 chars, no overlap), toy k = 2, made-up scores and hand-written answers",
            "doc_id": DOC, "snapshot_id": SNAP, "pages": PAGES, "chunks": CHUNKS, "traces": traces}
    out = HERE / "toy_traces.json"
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"toy doc: {len(PAGES)} pages, {len(DOC_TEXT)} chars, {len(CHUNKS)} chunks; written {out.name} ({out.stat().st_size} bytes)")
    print(f"page 2 parsed text holds the hyphenation artifact: {'gen-' in PAGES[1]!r}")
    labels = {}
    for (qid, planted, *_), t in zip(CASES, traces):
        got = first_failing_stage(t, PAGES, CHUNKS)
        labels[qid] = got
        print(f"{qid}: planted {planted:20s} ladder {got:20s} {'OK' if got == planted else 'MISMATCH'}  | answer: {t['answer']['text']}")
        assert got == planted, qid
    print("expected labels fingerprint (lab CHECK):", fp(labels))
    # extra unit cases used by the lab CHECK
    t1 = json.loads(json.dumps(traces[0]))
    t1["answer"] = {"text": ABSTAIN, "abstained": True, "citations": []}
    print("TOY-1 with the refusal sentence ->", first_failing_stage(t1, PAGES, CHUNKS))
    t6 = json.loads(json.dumps(traces[5]))
    t6["answer"]["text"] = "Each keeper works a 12-hour shift [toy:5]."
    print("TOY-6 with the right number ->", first_failing_stage(t6, PAGES, CHUNKS))
    # broken ladders (wrong order) must disagree with the planted labels
    def gen_first(trace, pages, chunks):
        by_id = {c["chunk_id"]: c for c in chunks}
        pages_in_ctx = {(by_id[i]["doc_id"], by_id[i]["page"]) for i in trace["context"]["chunk_ids"]}
        if any((x["doc_id"], x["page"]) not in pages_in_ctx for x in trace["answer"]["citations"]):
            return "generate:citation"
        return first_failing_stage(trace, pages, chunks)
    wrong = {qid: gen_first(t, PAGES, CHUNKS) for (qid, *_), t in zip(CASES, traces)}
    print("generation-first ladder disagrees on:", {k: v for k, v in wrong.items() if v != labels[k]})


if __name__ == "__main__":
    main()
