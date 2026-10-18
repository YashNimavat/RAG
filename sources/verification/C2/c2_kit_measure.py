"""C2 study-kit measurements (K1-K14): the numbers the C2 HTML lesson adds on top of the C2 lab facts.

The lab (sources/verification/C2lab, C2LAB_FACTS.md) already fixed the v0 chunker, its 97 records and their
sha256. This script re-runs that reference chunker (never re-typed: it is executed from c2_solution_ref.py through
c2_common.run_reference) and measures what the lesson needs and the lab did not: units (characters vs tokens),
token-length distributions and truncation at four sizes, the page-break census and the PPP sentence on PyMuPDF
text, a find()-based start_index (the mechanism of LangChain issue #29884), a LangChain-style split/merge port
checked against 07's three verified LangChain outputs, and the toy dilution cosines.

Local only: no Groq, Cohere or Claude call, no .env read. Models and tokenizers load from the local caches
(HF_HUB_OFFLINE=1; tiktoken's cached encoding files). Nothing is installed.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C2/c2_kit_measure.py
Saved output: sources/verification/C2/out_c2_kit_measure.txt (sections K1..K14 for C2_FACTS.md)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import logging
import math
import re
import statistics as st
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
sys.path.insert(0, str(WS / "sources" / "verification" / "C2lab"))
from c2_common import run_reference          # noqa: E402

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
L6 = "sentence-transformers/all-MiniLM-L6-v2"
L6_REV = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
SNAPDIR = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots" / L6_REV


def head(t):
    print(f"\n=== {t}")


def mmm(xs):
    return f"{min(xs)} / {int(st.median(xs)) if float(st.median(xs)).is_integer() else st.median(xs)} / {max(xs)}"


# ---------------------------------------------------------------- the lab reference, executed (not re-typed)
ns = run_reference(str(WS / "sources" / "verification" / "C2lab" / "c2_solution_ref.py"))
pages, doc_text, page_starts = ns["pages"], ns["doc_text"], ns["page_starts"]
records, PARAMS = ns["records"], ns["PARAMS"]
recursive_chunks, fixed_window_chunks, chunk_pages = ns["recursive_chunks"], ns["fixed_window_chunks"], ns["chunk_pages"]
params_hash, make_records = ns["params_hash"], ns["make_records"]
p_formula, p_brute, chunks_containing = ns["p_formula"], ns["p_brute"], ns["chunks_containing"]
SHA_JL = hashlib.sha256("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records).encode("utf-8")).hexdigest()

# ---------------------------------------------------------------- tokenizers
import tiktoken                               # noqa: E402
from tokenizers import Tokenizer              # noqa: E402

wp = Tokenizer.from_file(str(SNAPDIR / "tokenizer.json"))
wp_trunc_in_file = wp.truncation
wp.no_truncation()
wp.no_padding()
cl = tiktoken.get_encoding("cl100k_base")
g2 = tiktoken.get_encoding("gpt2")


def n_wp(t):           # MiniLM WordPiece, [CLS]/[SEP] included (the post-processor adds them)
    return len(wp.encode(t).ids)


def n_cl(t):
    return len(cl.encode(t, disallowed_special=()))


def n_g2(t):
    return len(g2.encode(t, disallowed_special=()))


head("K1 environment and objects")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "tiktoken", "tokenizers", "sentence-transformers", "transformers", "torch", "numpy")})
print(f"pages {len(pages)} | characters {len(doc_text):,} | snapshot {ns['SNAPSHOT_ID']} | PARAMS {json.dumps(PARAMS, sort_keys=True)}")
print(f"params_hash {params_hash(PARAMS)} | records {len(records)} | chunks.jsonl sha256 {SHA_JL}")
print(f"MiniLM snapshot {L6_REV[:8]}; truncation stored in its tokenizer.json: {wp_trunc_in_file}")
other = [p.name for p in SNAPDIR.parent.iterdir() if p.name != L6_REV]
print(f"other MiniLM snapshots in the cache: {[o[:8] for o in other]}")
print("LangChain installed:", any(d.metadata["Name"] == "langchain-text-splitters" for d in md.distributions()))

# ---------------------------------------------------------------- K2 units
head("K2 units: one corpus, three tokenizers")
n_words = len(re.findall(r"\S+", doc_text))
tot = {"WordPiece (MiniLM, no specials)": len(wp.encode(doc_text, add_special_tokens=False).ids),
       "cl100k_base": n_cl(doc_text), "gpt2": n_g2(doc_text)}
for k, v in tot.items():
    print(f"{k}: {v:,} tokens, {len(doc_text) / v:.2f} characters per token")
print(f"whitespace words {n_words:,}; characters per word {len(doc_text) / n_words:.2f}")
ch = [len(r["text"]) for r in records]
wpl = [n_wp(r["text"]) for r in records]
cll = [n_cl(r["text"]) for r in records]
g2l = [n_g2(r["text"]) for r in records]
print(f"97 v0 chunks: characters {mmm(ch)}; WordPiece (+specials) {mmm(wpl)}; cl100k {mmm(cll)}; gpt2 {mmm(g2l)}")
print(f"mean characters {st.mean(ch):.1f}; mean WordPiece {st.mean(wpl):.1f}; mean cl100k {st.mean(cll):.1f}")
full = [i for i, r in enumerate(records) if len(r["text"]) == 1000]
print(f"chunks exactly 1,000 characters: {len(full)}; first seq {full[0]}")
r0 = records[full[0]]
print(f"ruler example seq {full[0]} (page {r0['page_segments'][0]['page']}): characters {len(r0['text'])}, "
      f"WordPiece {n_wp(r0['text'])} (+specials), cl100k {n_cl(r0['text'])}, gpt2 {n_g2(r0['text'])}; "
      f"starts {r0['text'][:60]!r}")
print(f"'1000 tokens' as text on this corpus: cl100k {1000 * len(doc_text) / tot['cl100k_base']:,.0f} characters; "
      f"WordPiece {1000 * len(doc_text) / tot['WordPiece (MiniLM, no specials)']:,.0f}; gpt2 {1000 * len(doc_text) / tot['gpt2']:,.0f}")
print(f"ratio 1000 chars vs belief '1000 tokens' (median chunk {int(st.median(wpl))} WordPiece): {1000 / st.median(wpl):.1f}x")

# ---------------------------------------------------------------- K3 fixed windows
head("K3 fixed windows")
T = ns["T"]
for S, O in ((10, 3), (8, 4), (10, 0)):
    print(f"fixed_window_chunks(T, {S}, {O}) -> {[(c.char_start, c.char_end, c.text) for c in fixed_window_chunks(T, S, O)]}")
mism = 0
for S, O in ((10, 3), (8, 4), (300, 60), (1000, 200)):
    for L in range(S + 1, 20 * S):
        n = len(fixed_window_chunks("x" * L, S, O))
        mism += n != math.ceil((L - O) / (S - O))
print(f"count formula vs code, L = S+1 .. 20S-1 at (10,3) (8,4) (300,60) (1000,200): {mism} mismatches")
fw = fixed_window_chunks(doc_text, 1000, 200)
print(f"doc_text fixed 1000/200: {len(fw)} chunks (formula ceil(({len(doc_text)} - 200)/800) = {math.ceil((len(doc_text) - 200) / 800)}); "
      f"stored characters / L = {sum(len(c.text) for c in fw) / len(doc_text):.4f} (limit S/(S-O) = 1.25)")
for S, O in ((1000, 0), (1000, 200), (1000, 400), (1000, 500)):
    print(f"  S/(S-O) at {S}/{O}: {S / (S - O):.3f}; windows on doc_text: {len(fixed_window_chunks(doc_text, S, O))}")
cut_mid_word = sum(1 for c in fw[:-1] if doc_text[c.char_end - 1].isalnum() and doc_text[c.char_end].isalnum())
print(f"fixed windows that end inside a word: {cut_mid_word} of {len(fw) - 1} inner boundaries")
rc_doc = recursive_chunks(doc_text, 1000, 200)
cut_mid_word_r = sum(1 for c in rc_doc[:-1] if doc_text[c.char_end - 1].isalnum() and doc_text[c.char_end].isalnum())
print(f"recursive 1000/200 on doc_text: {cut_mid_word_r} of {len(rc_doc) - 1} inner boundaries inside a word")

# ---------------------------------------------------------------- K4 containment
head("K4 containment probability (formula and brute force)")
for O in (0, 200, 400):
    print(f"S=1000 O={O} F=500: formula {p_formula(1000, O, 500):.4f}; brute L=20000 {p_brute(20000, 1000, O, 500):.4f}")
for F in (100, 200, 201, 202, 250, 500, 800, 1000):
    print(f"S=1000 O=200 F={F}: {p_formula(1000, 200, F):.5f}")
print(f"PARA 300/60 FACT F={ns['FACT_SPAN'][1] - ns['FACT_SPAN'][0]}: P = {p_formula(300, 60, 71):.4f}; "
      f"fixed 300/0 contains: {chunks_containing(fixed_window_chunks(ns['PARA'], 300, 0), *ns['FACT_SPAN'])}; "
      f"300/60: {chunks_containing(fixed_window_chunks(ns['PARA'], 300, 60), *ns['FACT_SPAN'])}")
print(f"PARA fixed 300/60 spans {[(c.char_start, c.char_end) for c in fixed_window_chunks(ns['PARA'], 300, 60)]}")


# ---------------------------------------------------------------- K5 a LangChain-style port (checked against 07's verified outputs)
def lc_split(text, size, overlap, separators=("\n\n", "\n", " ", ""), length=len, keep="start", strip=True):
    """Port of RecursiveCharacterTextSplitter._split_text + TextSplitter._merge_splits (langchain-text-splitters,
    read at source level for the C2 research). Not the library: checked below against 07's verified LangChain runs."""
    def split_regex(t, sep):
        if not sep:
            return [c for c in t]
        parts = re.split(f"({re.escape(sep)})", t)
        if keep == "start":       # re.split with a group always returns an odd-length list
            out = [parts[0]] + [parts[i] + parts[i + 1] for i in range(1, len(parts), 2)]
        elif keep == "end":
            out = [parts[i] + parts[i + 1] for i in range(0, len(parts) - 1, 2)] + [parts[-1]]
        else:
            out = parts[::2]
        return [s for s in out if s != ""]

    def join(docs, sep):
        t = sep.join(docs)
        t = t.strip() if strip else t
        return t or None

    def merge(splits, sep):
        sl = length(sep)
        docs, cur, total = [], [], 0
        for d in splits:
            n = length(d)
            if total + n + (sl if cur else 0) > size:
                if cur:
                    j = join(cur, sep)
                    if j is not None:
                        docs.append(j)
                    while total > overlap or (total + n + (sl if cur else 0) > size and total > 0):
                        total -= length(cur[0]) + (sl if len(cur) > 1 else 0)
                        cur = cur[1:]
            cur.append(d)
            total += n + (sl if len(cur) > 1 else 0)
        j = join(cur, sep)
        if j is not None:
            docs.append(j)
        return docs

    def rec(t, seps):
        final, sep, new = [], seps[-1], []
        for i, s in enumerate(seps):
            if s == "":
                sep = s
                break
            if re.search(re.escape(s), t):
                sep, new = s, list(seps[i + 1:])
                break
        good, merge_sep = [], ("" if keep else sep)
        for s in split_regex(t, sep):
            if length(s) < size:
                good.append(s)
            else:
                if good:
                    final.extend(merge(good, merge_sep))
                    good = []
                final.extend([s] if not new else rec(s, new))
        if good:
            final.extend(merge(good, merge_sep))
        return final

    return rec(text, list(separators))


def find_start_index(text, chunks, overlap):
    """LangChain create_documents(add_start_index=True): a search from a guessed position, not a record."""
    out, index, prev = [], 0, 0
    for c in chunks:
        offset = index + prev - overlap
        index = text.find(c, max(0, offset))
        out.append(index)
        prev = len(c)
    return out


head("K5 recursive splitter: ours vs a LangChain-style port")
W, PARA = ns["W"], ns["PARA"]
print(f"ours recursive_chunks(W,10,4): {[(c.char_start, c.char_end, c.text) for c in recursive_chunks(W, 10, 4)]}")
print(f"ours split pieces W: {ns['split_spans'](W, 0, len(W), ns['SEPARATORS'], 10)}")
port_w = lc_split(W, 10, 4)
port_x = lc_split("short " + "x" * 25 + " tail", 10, 0)
port_x_ns = lc_split("short " + "x" * 25 + " tail", 10, 0, strip=False)
port_p = lc_split(PARA, 300, 60)
port_p_spans = list(zip(find_start_index(PARA, port_p, 60), [find_start_index(PARA, port_p, 60)[i] + len(c) for i, c in enumerate(port_p)]))
chk = {"W 10/4 (07 C2-A-03)": (port_w, ["the cat", "cat sat", "sat on", "on the", "the mat"]),
       "short+x*25+tail 10/0 (07 D.4)": (port_x, ["short", "xxxxxxxxx", "xxxxxxxxxx", "xxxxxx", "tail"]),
       "same, strip_whitespace=False (07 D.4)": (port_x_ns, ["short", " xxxxxxxxx", "xxxxxxxxxx", "xxxxxx", " tail"]),
       "PARA 300/60 spans (07 Part F)": (port_p_spans, [(0, 293), (238, 533), (478, 772), (714, 785)])}
for k, (got, want) in chk.items():
    print(f"port {k}: {got} -> {'MATCHES 07' if got == want else 'DIFFERS from 07 ' + str(want)}")
print(f"ours PARA 300/60: {[(c.char_start, c.char_end) for c in recursive_chunks(PARA, 300, 60)]}")
custom = lc_split("a" * 25 + " bb", 10, 0, separators=(" ",))
print(f"port, separators [' '] only (no ''): {custom} -> longest {max(map(len, custom))} > 10")
print(f"port, overlap == size accepted: 60 words at 40/40 -> {len(lc_split(' '.join(['word%02d' % i for i in range(60)]), 40, 40))} chunks")
dup = lc_split(" ".join(f"w{i:02d}" for i in range(60)), 40, 40)
print(f"  (words 'w00'..'w59', 3 letters each) -> {len(dup)} chunks; first three {dup[:3]}")
# corpus, per page, as encode_pdf (port on PyMuPDF pages)
lc_pp = [(i + 1, c) for i, p in enumerate(pages) for c in lc_split(p, 1000, 200)]
print(f"port per page 1000/200 on PyMuPDF pages: {len(lc_pp)} chunks; lengths {mmm([len(c) for _, c in lc_pp])} "
      f"(07 PyPDFLoader + LangChain: 97, 391 / 933 / 999)")
lc_ov = []
for (pa, a), (pb, b) in zip(lc_pp, lc_pp[1:]):
    if pa == pb:
        pg = pages[pa - 1]
        sa = find_start_index(pg, [a], 0)[0]
        sb = pg.find(b, sa + 1)
        lc_ov.append(sa + len(a) - sb)
print(f"port real overlaps, same-page pairs: {len(lc_ov)}; min/median/max {mmm(lc_ov)}; first four {lc_ov[:4]} (07 H.2: 180, 140, 197, 177)")

# ---------------------------------------------------------------- K6 scope
head("K6 scope: per page vs cross page (ours, 1000/200)")
pp = chunk_pages(pages, 1000, 200)
cross = recursive_chunks(doc_text, 1000, 200)
page_of = lambda off: max(i for i, s in enumerate(page_starts) if s <= off)      # the joining "\n" counts with the page before
crossing = [c for c in cross if page_of(c.char_start) != page_of(c.char_end - 1)]
both_text = [c for c in cross if len({page_of(i) for i in range(c.char_start, c.char_end) if not doc_text[i].isspace()}) > 1]
print(f"per page {len(pp)} chunks, lengths {mmm([b - a for a, b, _ in pp])}; cross page {len(cross)} chunks, "
      f"{len(crossing)} start and end on different pages (the lab's count), {len(both_text)} hold non-space text from two pages; "
      f"lengths {mmm([c.char_end - c.char_start for c in cross])}")
per_page_count = [sum(1 for *_, p in pp if p == i + 1) for i in range(len(pages))]
print(f"chunks per page: {per_page_count}; page lengths {mmm([len(p) for p in pages])}")
print(f"per-page chunks touching 2 pages: {sum(1 for r in records if len(r['page_segments']) != 1)}")

# ---------------------------------------------------------------- K7 real overlap
head("K7 real overlap, ours, per page 1000/200")
ao = ns["achieved_overlaps"](records)
print(f"same-page pairs {len(ao)}; min/median/max {mmm(ao)}; exactly 200: {ao.count(200)}; first four {ao[:4]}")
hist = [sum(1 for x in ao if lo <= x < lo + 20) for lo in range(100, 201, 20)]
print(f"histogram 100-119,120-139,...,200-219: {hist}")
print(f"page-end pairs (no overlap possible): {len(records) - 1 - len(ao)}")
zero = sum(1 for x in ao if x == 0)
print(f"pairs with 0 overlap: {zero}")

# ---------------------------------------------------------------- K8 lengths and truncation by size
head("K8 token lengths and the embedder cap, per page, four sizes")
hist_rows = {}
for S, O in ((500, 100), (1000, 200), (1500, 300), (2000, 400)):
    sp = chunk_pages(pages, S, O)
    tx = [doc_text[a:b] for a, b, _ in sp]
    w = [n_wp(t) for t in tx]
    c = [n_cl(t) for t in tx]
    over256 = [i for i, x in enumerate(w) if x > 256]
    lost = sum(len(tx[i]) - len(tx[i][:wp.encode(tx[i]).offsets[254][1]]) for i in over256) if over256 else 0
    tiny = sum(1 for t in tx if len(t) < S / 4)
    print(f"{S}/{O}: {len(sp)} chunks; chars {mmm([len(t) for t in tx])}; WordPiece {mmm(w)}; over 256: {len(over256)}; "
          f"over 512: {sum(1 for x in w if x > 512)}; cl100k over 256: {sum(1 for x in c if x > 256)}; "
          f"tail chunks < 25% of size: {tiny}; characters past the 256 cap: {lost:,} of {sum(map(len, tx)):,}")
    hist_rows[S] = [sum(1 for x in w if lo <= x < lo + 25) for lo in range(0, 400, 25)]
for S, h in hist_rows.items():
    print(f"WordPiece histogram {S} (bins of 25 from 0 to 400): {h}")
p95 = sorted(wpl)[int(0.95 * (len(wpl) - 1))]
print(f"v0 chunks WordPiece p95 (nearest rank, index {int(0.95 * 96)}): {p95}; over 128 (MiniLM training length): {sum(1 for x in wpl if x > 128)}")
print(f"v0 embedding tokens for the corpus (sum of WordPiece incl. specials over 97 chunks): {sum(wpl):,}; cl100k sum {sum(cll):,}")

# ---------------------------------------------------------------- K9 runtime truncation (MiniLM)
head("K9 runtime truncation check (sentence-transformers, MiniLM)")
from sentence_transformers import SentenceTransformer   # noqa: E402

model = SentenceTransformer(L6, revision=L6_REV, device="cpu")
print(f"max_seq_length {model.max_seq_length}; tokenizer.model_max_length {model.tokenizer.model_max_length}")
long_text = doc_text[:2600]
n_long = n_wp(long_text)
enc = wp.encode(long_text)
cut = enc.offsets[254][1]          # end of the 254th content token: [CLS] + 254 + [SEP] = 256
prefix = long_text[:cut]
ids_in = model.tokenize([long_text])["input_ids"]
v_long, v_pref = model.encode([long_text, prefix], normalize_embeddings=True)
print(f"text of {len(long_text):,} characters = {n_long} WordPiece tokens incl. specials; model.tokenize length {ids_in.shape[1]}; "
      f"first id {int(ids_in[0, 0])} last id {int(ids_in[0, -1])} (CLS 101, SEP 102)")
print(f"prefix of {len(prefix):,} characters = {n_wp(prefix)} tokens; cos(full, prefix) = {float(v_long @ v_pref):.6f}")
tail_cut = long_text[:cut] + " Completely unrelated words about chocolate cake recipes."
v_tail = model.encode([long_text[:cut] + long_text[cut:] + " chocolate cake"], normalize_embeddings=True)[0]
print(f"adding text after the cap changes nothing: cos = {float(v_long @ v_tail):.6f}")

# ---------------------------------------------------------------- K10 page breaks and the PPP sentence
head("K10 page-break census (PyMuPDF text) and the PPP sentence")
TERM = ".!?:;\"'”)]"
not_term, mid, other = [], [], []
for i in range(len(pages) - 1):
    end = pages[i].rstrip()
    nxt = pages[i + 1].lstrip()
    if not end or end[-1] in TERM:
        continue
    not_term.append(i + 1)
    (mid if nxt[:1].islower() else other).append(i + 1)
print(f"page breaks {len(pages) - 1}; page N not ending in terminal punctuation: {len(not_term)}")
print(f"  next page starts lowercase (mid-sentence cut): {len(mid)} at {[f'{p}->{p + 1}' for p in mid]}")
print(f"  the rest (heading or label at the page end): {len(other)}")
for p in other[:4]:
    print(f"    page {p} ends {pages[p - 1].rstrip().splitlines()[-1]!r}; page {p + 1} starts {pages[p].lstrip().splitlines()[0][:40]!r}")
a = doc_text.index("Public-\nprivate partnerships (PPPs) can leverage")
b = doc_text.index("large-scale climate solutions.", a) + len("large-scale climate solutions.")
pg = lambda off: max(i for i, s in enumerate(page_starts) if s <= off) + 1
print(f"PPP sentence: span [{a}, {b}) F = {b - a}; pages {pg(a)}->{pg(b - 1)}; page break at {page_starts[pg(b - 1) - 1] - 1}")
print(f"  per-page v0 chunks containing it: {[r['seq'] for r in records if r['char_start'] <= a and b <= r['char_end']]}")
print(f"  per-page chunks touching it: {[r['seq'] for r in records if r['char_start'] < b and a < r['char_end']]}")
print(f"  cross-page chunks containing it: {[i for i, c in enumerate(cross) if c.char_start <= a and b <= c.char_end]}")
for s in (35, 36):
    r_ = records[s]
    print(f"  seq {s}: page {r_['page_segments'][0]['page']}, [{r_['char_start']}, {r_['char_end']}), {len(r_['text'])} chars, "
          f"starts {r_['text'][:30]!r}, ends {r_['text'][-30:]!r}")
c34 = cross[34]
print(f"  cross-page chunk 34: [{c34.char_start}, {c34.char_end}), {c34.char_end - c34.char_start} chars, pages {page_of(c34.char_start) + 1}-{page_of(c34.char_end - 1) + 1}")
print(f"  page-1 chunk seq 0: {len(records[0]['text'])} chars, ends {records[0]['text'][-35:]!r}")
for O in (0, 200, 400, 600):
    hit = [r for r in make_records("climate", ns["SNAPSHOT_ID"], pages, {**PARAMS, "chunk_overlap": O}) if r["char_start"] <= a and b <= r["char_end"]]
    print(f"  per page 1000/{O}: chunks containing it {len(hit)}")
q = "Public-private partnerships"
print(f"  exact string {q!r} found in doc_text: {doc_text.count(q)}; with the PDF's line break 'Public-\\nprivate': {doc_text.count('Public-' + chr(10) + 'private')}")
mid_ids = []
for p in mid:
    off = page_starts[p] - 1
    s0 = max(doc_text.rfind(". ", 0, off), doc_text.rfind(".\n", 0, off)) + 2
    e0 = min(x for x in (doc_text.find(". ", off), doc_text.find(".\n", off)) if x != -1) + 1
    inside = [i for i, c in enumerate(cross) if c.char_start <= s0 and e0 <= c.char_end]
    mid_ids.append((p, e0 - s0, bool(inside)))
print(f"  the {len(mid)} cut sentences (page, length, whole in some cross-page chunk): {mid_ids}")
lines = {}
for i, p in enumerate(pages):
    for ln in set(x.strip() for x in p.splitlines() if x.strip()):
        lines.setdefault(ln, set()).add(i)
rep = sorted((len(v), k) for k, v in lines.items() if len(v) >= 3)
print(f"lines repeated on >= 3 pages: {len(rep)} {rep[:5]}")
print(f"tabs in doc_text: {doc_text.count(chr(9))}")

# ---------------------------------------------------------------- K11 identity
head("K11 offsets and identity")
rt = all(doc_text[r["char_start"]:r["char_end"]] == r["text"] for r in records)
seg = all(pages[r["page_segments"][0]["page"] - 1][r["page_segments"][0]["char_start"]:r["page_segments"][0]["char_end"]] == r["text"] for r in records)
print(f"round trip doc_text[a:b] == text: {rt} (97/97); page_segments round trip: {seg}")
print(f"first ids {records[0]['chunk_id']}, last {records[-1]['chunk_id']}")
p199 = {**PARAMS, "chunk_overlap": 199}
r199 = make_records("climate", ns["SNAPSHOT_ID"], pages, p199)
same_ids = len({r["chunk_id"] for r in records} & {r["chunk_id"] for r in r199})
same_spans = len({(r["char_start"], r["char_end"]) for r in records} & {(r["char_start"], r["char_end"]) for r in r199})
print(f"overlap 199: params_hash {params_hash(p199)}; {len(r199)} chunks; ids shared with v0 {same_ids}; spans shared {same_spans}")
for k, v in (("unit", "tokens"), ("scope", "cross_page"), ("separators", ["\n\n", "\n", " "]), ("chunk_size", 1001)):
    print(f"change {k}: params_hash {params_hash({**PARAMS, k: v})}")
print(f"python hash() is salted per process (PYTHONHASHSEED), so it is never used: hash('climate') differs between runs")
ph_dict_order = hashlib.sha256(json.dumps(dict(reversed(list(PARAMS.items())))).encode()).hexdigest()[:12]
print(f"without sort_keys, reversed key order gives {ph_dict_order} (not {params_hash(PARAMS)})")
again = make_records("climate", ns["SNAPSHOT_ID"], pages, PARAMS)
print(f"two builds identical: {again == records}")
print(f"chars covered: union of spans == every non-separator character of the doc: "
      f"{sum(1 for i in range(len(doc_text)) if any(r['char_start'] <= i < r['char_end'] for r in records))} of {len(doc_text)} "
      f"(the {len(pages) - 1} joining newlines are outside every per-page chunk)")

# ---------------------------------------------------------------- K12 start_index by search
head("K12 start_index found by text.find (LangChain create_documents), three cases")
# (a) characters: our recursive spans, per page, find with overlap 200
ok_a = tot_a = 0
for i, p in enumerate(pages):
    cs = recursive_chunks(p, 1000, 200)
    got = find_start_index(p, [c.text for c in cs], 200)
    ok_a += sum(g == c.char_start for g, c in zip(got, cs))
    tot_a += len(cs)
print(f"(a) characters, ours per page 1000/200: {ok_a} of {tot_a} start_index values right")
# (b) TokenTextSplitter-style windows: gpt2 tokens 200/50, each window decoded separately
neg = wrong = right = tot_b = 0
ex = None
for i, p in enumerate(pages):
    ids = g2.encode(p)
    wins, st0 = [], 0
    while st0 < len(ids):
        wins.append((st0, ids[st0:st0 + 200]))
        if st0 + 200 >= len(ids):
            break
        st0 += 150
    texts = [g2.decode(w) for _, w in wins]
    got = find_start_index(p, texts, 50)
    for (s, _), t, g in zip(wins, texts, got):
        true = len(g2.decode(ids[:s]))
        tot_b += 1
        if g == -1:
            neg += 1
            ex = ex or (i + 1, true)
        elif g == true:
            right += 1
        else:
            wrong += 1
print(f"(b) token windows (gpt2 200/50, decoded): {tot_b} windows; start_index right {right}, -1 {neg}, wrong {wrong}; first -1 on page {ex}")
# (c) from_tiktoken_encoder: the port with a gpt2 length function, 200/50, per page, strip on
neg = wrong = right = tot_c = 0
for p in pages:
    cs = lc_split(p, 200, 50, length=n_g2)
    got = find_start_index(p, cs, 50)
    pos, truth = 0, []
    for c in cs:              # true start: the first occurrence at or after the previous true start that keeps order
        j = p.find(c, pos)
        truth.append(j)
        pos = j + 1
    for g, t in zip(got, truth):
        tot_c += 1
        right += g == t
        neg += g == -1
        wrong += g not in (t, -1)
print(f"(c) character splitter measured in gpt2 tokens (port), 200/50: {tot_c} chunks; right {right}, -1 {neg}, wrong {wrong}")
# (d) repeated text: a toy where a sentence appears twice
toy = "Intro. The footer line. Body text here. The footer line. End."
print(f"(d) toy repeat: text.find('The footer line.') = {toy.find('The footer line.')}, second copy at {toy.find('The footer line.', 10)}")

# ---------------------------------------------------------------- K13 toy dilution
head("K13 toy dilution (2-D, formula 1/sqrt(1+n^2)); competitor cos 0.600")
q = np.array([1.0, 0.0])
for n in range(5):
    v = np.mean(np.vstack([q] + [np.array([0.0, 1.0])] * n), axis=0)
    c = float(q @ v / np.linalg.norm(v))
    print(f"n={n}: chunk {np.round(v, 3).tolist()} cos {c:.3f} formula {1 / math.sqrt(1 + n * n):.3f} beats 0.600: {c > 0.6}")

# ---------------------------------------------------------------- K14 formula arithmetic used on the page
head("K14 formula arithmetic")
for S, O in ((1000, 200), (1000, 400), (500, 100), (300, 60), (10, 3)):
    print(f"S={S} O={O}: stride {S - O}, guaranteed F <= {O + 1}, storage limit {S / (S - O):.3f}")
print(f"PPP F = {b - a}: P(contained) at S=1000, O=200 in one text: {p_formula(1000, 200, b - a):.4f}; O=400: {p_formula(1000, 400, b - a):.4f}")
print(f"1000/400 on doc_text: ceil(({len(doc_text)} - 400)/600) = {math.ceil((len(doc_text) - 400) / 600)}")
print("done")
