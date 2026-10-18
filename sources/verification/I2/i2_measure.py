"""I2 facts: structure-aware chunking on Corpus D. Prints sections S1-S15 and writes i2_lesson_data.json.

Usage (from rag_learning/):
  uv run python sources/verification/I2/i2_measure.py <climate.pdf> [<minilm_onnx_dir>]
With the optional ONNX directory (needs onnxruntime: `uv run --with onnxruntime ...`), S14 adds MiniLM retrieval.
No API call. Deterministic: two runs give byte-identical stdout.
"""
import hashlib
import json
import random
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i2_structure as S  # noqa: E402

ROOT = HERE.parents[2]
SEEDS = ROOT / "study" / "tools" / "examples" / "climate_seed_spans.jsonl"
CAP, MIN_CHARS = 1000, 400
LEVEL_NAME = {2: "chapter", 3: "section", 4: "sub-section"}
DATA = {}


def sec(t):
    print(f"\n=== {t} ===")


def stats(ch):
    ln = [c["b"] - c["a"] for c in ch]
    return {"n": len(ch), "min": min(ln), "median": st.median(ln), "max": max(ln), "mean": round(sum(ln) / len(ln), 1),
            "multi_page": sum(1 for c in ch if len({p for p, _, _ in c["page_segments"]}) > 1) if "page_segments" in ch[0] else None}


def hist(ch, width=100, top=1000):
    bins = [0] * (top // width)
    for c in ch:
        bins[min((c["b"] - c["a"] - 1) // width, len(bins) - 1)] += 1
    return bins


def main(pdf, onnx_dir=None):
    raw = Path(pdf).read_bytes()
    doc = fitz.open(pdf)
    pages = S.page_texts(doc)
    starts = S.page_starts(pages)
    T = "\n".join(pages)

    sec("S1 Environment and snapshot")
    tsha = hashlib.sha256(T.encode()).hexdigest()
    parts = ["snapshot-v1", f"parser=pymupdf@{fitz.VersionBind}", "options=" + json.dumps({}, sort_keys=True),
             "cleaning=none", "page_join=\\n", f"climate:{tsha}"]
    snap = hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]
    print(f"python {sys.version.split()[0]} · pymupdf {fitz.VersionBind}")
    print(f"pdf sha256 {hashlib.sha256(raw).hexdigest()} bytes {len(raw)} pages {len(doc)}")
    print(f"doc_text chars {len(T)} sha256 {tsha[:12]} snapshot_id {snap}")
    cat = doc.pdf_catalog()
    print(f"get_toc() = {doc.get_toc()}")
    print(f"catalog StructTreeRoot: {doc.xref_get_key(cat, 'StructTreeRoot')[0]} · MarkInfo: {doc.xref_get_key(cat, 'MarkInfo')}")
    print(f"metadata creator: {doc.metadata.get('creator')!r}")
    DATA["snapshot"] = {"id": snap, "chars": len(T), "pages": len(doc)}

    sec("S2 One real span dict (page 1, first 3 lines)")
    blocks = doc[0].get_text("dict")["blocks"]
    shown = 0
    for b in blocks:
        for line in b.get("lines", []):
            for s in line["spans"]:
                if shown < 3:
                    keys = sorted(k for k in s if k != "text")
                    print(f"text={s['text']!r} size={s['size']:.2f} flags={s['flags']} (bold bit {s['flags'] & 16}) "
                          f"char_flags={s.get('char_flags')} font={s['font']} bbox=({', '.join(f'{v:.1f}' for v in s['bbox'])})")
                    if shown == 0:
                        print("keys:", ", ".join(keys))
                    shown += 1
    print("flags bits: 1 superscript, 2 italic, 4 serif, 8 monospaced, 16 bold")

    sec("S3 Font sizes, character-weighted")
    h = S.size_histogram(doc)
    total = sum(h.values())
    rows = []
    for (size, bold), n in sorted(h.items(), key=lambda kv: (-kv[0][0], not kv[0][1])):
        print(f"size {size:5.2f} bold={str(bold):5} chars {n:6d} ({100 * n / total:.1f}%)")
        rows.append({"size": size, "bold": bold, "chars": n})
    spans_by_size = Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line["spans"]:
                    if s["text"].strip():
                        spans_by_size[round(s["size"], 2)] += 1
    print(f"body size (most characters): {S.body_size(doc)} · spans per size: {dict(sorted(spans_by_size.items()))}")
    DATA["sizes"] = rows

    sec("S4 Heading detection: size only vs size + bold")
    lines = S.line_records(doc)
    bold_lines = [r for r in lines if r["bold"]]
    print(f"text lines {len(lines)} · all-bold lines {len(bold_lines)} · bold lines with > 1 span: {sum(r['spans'] > 1 for r in bold_lines)}")
    det = {}
    for rule in ("size", "size+bold"):
        hs = S.detect_headings(doc, rule)
        det[rule] = hs
        c = Counter(x["level"] for x in hs)
        print(f"{rule:9}: {len(hs)} headings · per level {dict(sorted(c.items()))}")
    missed = len(det["size+bold"]) - len(det["size"])
    print(f"size-only misses {missed} of {len(det['size+bold'])} ({100 * missed / len(det['size+bold']):.1f}%)")
    wrapped = [x for x in det["size+bold"] if len(x["lines"]) > 1]
    print("joined (wrapped) headings:", [(x["page"], x["title"]) for x in wrapped])
    print(f"level-2 lines before joining: {sum(1 for r in bold_lines if r['size'] == 18.0)}")
    hy = [x for x in det["size+bold"] if "-" in x["title"]]
    print("headings with a hyphen (one span each?):", [(x["title"], x["page"]) for x in hy])
    long_bold = [r["raw"].strip() for r in bold_lines if len(r["raw"].split()) > S.MAX_WORDS or r["raw"].strip()[-1] in S.END_PUNCT]
    print(f"bold lines removed by the filters (> {S.MAX_WORDS} words or final . ! ?): {len(long_bold)}")
    reps = Counter()
    for r in lines:
        reps[r["raw"].strip()] += 1
    print(f"lines repeated on >= 3 pages: {[t for t in reps if len({x['page'] for x in lines if x['raw'].strip() == t}) >= 3][:5]}")
    DATA["levels"] = {rule: dict(sorted(Counter(x["level"] for x in hs).items())) for rule, hs in det.items()}

    sec("S5 Same text, same order: dict lines vs page.get_text()")
    same = 0
    diffs = []
    for pno, page in enumerate(doc):
        built = ""
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                built += "".join(s["text"] for s in line["spans"]) + "\n"
        if built == pages[pno]:
            same += 1
        else:
            diffs.append(pno + 1)
    print(f"pages where the dict lines + '\\n' rebuild get_text() exactly: {same} of {len(doc)} · differ: {diffs[:10]}")

    sec("S6 Align every heading to the snapshot (cursor + find)")
    H = S.add_paths(S.align(T, S.detect_headings(doc, "size+bold")))
    print(f"aligned {len(H)} of {len(H)} headings; all inside their page: "
          f"{all(S.page_of(starts, x['start']) == x['page'] for x in H)}")
    coal = next(x for x in H if x["title"] == "Coal")
    print(f"'Coal': level {coal['level']} page {coal['page']} doc [{coal['start']}, {coal['end']}) · page 1 ends at {starts[1] - 1} "
          f"· text after it: {T[coal['end']:coal['end'] + 40]!r}")
    print("first 6 headings:", [(x["level"], x["title"], x["start"]) for x in H[:6]])

    sec("S7 Section tree and repeated titles")
    titles = Counter(x["title"] for x in H)
    rep = sorted(t for t, n in titles.items() if n > 1)
    print(f"repeated titles: {len(rep)}")
    reprows = []
    for t in rep:
        for x in H:
            if x["title"] == t:
                print(f"  {t!r} p.{x['page']} L{x['level']}: {' > '.join(x['path'][1:])}")
                reprows.append({"title": t, "page": x["page"], "level": x["level"], "path": x["path"][1:]})
    DATA["repeated"] = reprows
    ch6 = [x for x in H if x["path"][1:2] == ["Chapter 6: Global and Local Climate Action"]]
    tree = []
    for i, x in enumerate(H):
        if x in ch6:
            nxt = next((g["start"] for g in H[i + 1:] if g["level"] <= x["level"]), len(T))
            tree.append({"level": x["level"], "title": x["title"], "chars": nxt - x["start"], "page": x["page"]})
            print(f"  {'  ' * (x['level'] - 2)}L{x['level']} {x['title']} ({nxt - x['start']} chars, p.{x['page']})")
    DATA["tree_ch6"] = tree
    for lv in (2, 3, 4):
        ln = [b - a for a, b, _ in S.section_ranges(H, len(T), lv)]
        print(f"level {lv} sections: {len(ln)} · length min/median/max {min(ln)}/{st.median(ln)}/{max(ln)} · mean {sum(ln) / len(ln):.1f}")

    sec("S8 The page-break failures on PyMuPDF text (re-measures 07 D.8)")
    orphan, cut = [], []
    for p in range(len(pages) - 1):
        tail = pages[p].rstrip()
        last_line = tail.split("\n")[-1].strip()
        if any(x["page"] == p + 1 and x["title"].endswith(last_line) and T[x["end"]:starts[p + 1]].strip() == "" for x in H):
            orphan.append(f"{p + 1}->{p + 2}")
        nxt = pages[p + 1].lstrip()
        if tail and tail[-1] not in '.!?:"' and nxt[:1].islower():
            cut.append(f"{p + 1}->{p + 2}")
    print(f"orphaned headings: {len(orphan)}: {orphan}")
    print(f"mid-sentence cuts: {len(cut)}: {cut}")
    nonterm = sum(1 for p in range(len(pages) - 1) if pages[p].rstrip()[-1:] not in '.!?:"')
    print(f"page breaks not ending in . ! ? : or quote: {nonterm} of {len(pages) - 1}")
    DATA["page_failures"] = {"orphans": orphan, "cuts": cut}

    sec("S9 Chunking: v0, the cross-page control, and structure at three split levels")
    v0 = S.v0_chunks(pages, starts)
    for c in v0:
        c["page_segments"] = S.page_segments(starts, len(T), c["a"], c["b"])
    xp = S.recursive_doc_chunks(T)
    for c in xp:
        c["page_segments"] = S.page_segments(starts, len(T), c["a"], c["b"])
    arms = {"v0 per-page 1000/200": v0, "cross-page recursive 1000/200": xp}
    for lv in (2, 3, 4):
        arms[f"structure L{lv} ({LEVEL_NAME[lv]})"] = S.structure_chunks(T, H, starts, lv, CAP, 0)
    arms[f"structure L4 + merge<{MIN_CHARS}"] = S.structure_chunks(T, H, starts, 4, CAP, MIN_CHARS)
    Hsize = S.add_paths(S.align(T, S.detect_headings(doc, "size")))
    arms["structure L3, size-only headings"] = S.structure_chunks(T, Hsize, starts, 3, CAP, 0)
    DATA["arms"] = {}
    for name, ch in arms.items():
        s_ = stats(ch)
        print(f"{name:36} n={s_['n']:3d} len min/median/max {s_['min']}/{s_['median']}/{s_['max']} mean {s_['mean']} "
              f"multi-page {s_['multi_page']} · hist(100s) {hist(ch)}")
        DATA["arms"][name] = {**s_, "hist": hist(ch)}
    l3 = arms["structure L3 (section)"]
    print(f"L3 chunks by pieces per section: {dict(sorted(Counter(c['pieces'] for c in l3).items()))}")
    print(f"L4 merge: merged chunks {sum(c['merged'] for c in arms[f'structure L4 + merge<{MIN_CHARS}'])}")
    true_sub = {x["start"] for x in H if x["level"] == 4}
    ends_in_sub = sum(1 for c in arms["structure L3, size-only headings"]
                      if any(c["a"] < s < c["b"] and not T[s:c["b"]].replace(next(x for x in H if x['start'] == s)['lines'][0], "", 1).strip()
                             for s in true_sub))
    print(f"size-only L3 chunks that end on a sub-heading (orphan re-created): {ends_in_sub}")
    same_l3 = [(c["a"], c["b"]) for c in arms["structure L3, size-only headings"]] == [(c["a"], c["b"]) for c in l3]
    print(f"size-only L3 chunks identical to size+bold L3: {same_l3}")
    DATA["size_only_orphans"] = ends_in_sub

    sec("S10 Balanced split: a worked case")
    units3 = S.units(T, H, 3)
    long_u = sorted([u for u in units3 if CAP < u["b"] - u["a"] <= 2 * CAP], key=lambda u: u["b"] - u["a"])
    ex = long_u[0]
    guard = S.heading_guard(T, H)
    pcs = S.balanced_split(T, ex["a"], ex["b"], CAP, guard)
    ell = ex["b"] - ex["a"]
    print(f"shortest L3 section over the cap: {' > '.join(ex['path'][1:])} · {ell} chars · n = ceil({ell}/{CAP}) = {-(-ell // CAP)} "
          f"· ideal {ell / 2:.1f} each · pieces {[b - a for a, b in pcs]} · naive {CAP} + {ell - CAP}")
    big = max(units3, key=lambda u: u["b"] - u["a"])
    bp = S.balanced_split(T, big["a"], big["b"], CAP, guard)
    print(f"longest L3 section: {' > '.join(big['path'][1:])} · {big['b'] - big['a']} chars · pieces {[b - a for a, b in bp]}")
    print(f"L3 sections over the cap: {sum(1 for u in units3 if u['b'] - u['a'] > CAP)} of {len(units3)}")
    DATA["balanced"] = {"path": ex["path"][1:], "len": ell, "pieces": [b - a for a, b in pcs]}

    sec("S11 Invariants (offset round trip, cap, no gaps, no crossing, page segments)")
    for name, ch in arms.items():
        if name.startswith("structure"):
            lv = int(name.split("L")[1][0])
            bad = S.check_invariants(T, ch, H, lv, CAP)
            print(f"{name:36} " + " ".join(f"{k}={len(v)}" for k, v in bad.items()))
    tiles = all(x["b"] == y["a"] or not T[x["b"]:y["a"]].strip() for x, y in zip(l3, l3[1:]))
    print(f"L3 chunks tile the document (no overlap, gaps only whitespace): {tiles} · overlap pairs: "
          f"{sum(1 for x, y in zip(l3, l3[1:]) if y['a'] < x['b'])}")

    sec("S12 Containment demos")
    def holder(ch, a, b):
        return [i for i, c in enumerate(ch) if c["a"] <= a and b <= c["b"]]
    body = T.find("Coal is the most carbon-intensive", coal["end"])
    for name in ("v0 per-page 1000/200", "structure L3 (section)"):
        hh = holder(arms[name], coal["start"], body + 30)
        print(f"{name}: one chunk holds 'Coal' + its first body line: {bool(hh)}"
              + (f" (chunk {hh[0]}, pages {[p for p, _, _ in arms[name][hh[0]]['page_segments']]})" if hh else ""))
    ppp_a = T.find("Public-\nprivate partnerships (PPPs) can leverage")
    ppp_b = T.find("climate solutions.", ppp_a) + len("climate solutions.")
    print(f"PPP sentence doc [{ppp_a}, {ppp_b}) pages {S.page_of(starts, ppp_a)}->{S.page_of(starts, ppp_b)}: {T[ppp_a:ppp_b]!r}")
    for name, ch in arms.items():
        hh = holder(ch, ppp_a, ppp_b)
        print(f"  {name:36} whole PPP sentence in one chunk: {bool(hh)}" + (f" (path {' > '.join(ch[hh[0]].get('path', [])[1:]) or '-'})" if hh else ""))
    DATA["ppp"] = {"a": ppp_a, "b": ppp_b}

    sec("S13 Eye inspection: 10 random L3 chunks, seed 0")
    idx = sorted(random.Random(0).sample(range(len(l3)), 10))
    for i in idx:
        c = l3[i]
        first = c["text"].lstrip()[:60].replace("\n", " ")
        last = c["text"].rstrip()[-40:].replace("\n", " ")
        starts_head = any(x["start"] == c["a"] for x in H)
        ends_sentence = c["text"].rstrip()[-1:] in '.!?:'
        print(f"chunk {i:3d} [{c['a']},{c['b']}) {c['b'] - c['a']} chars pages {[p for p, _, _ in c['page_segments']]} "
              f"head-start={starts_head} sentence-end={ends_sentence} piece {c['piece'] + 1}/{c['pieces']}")
        print(f"     path: {' > '.join(c['path'][1:])}")
        print(f"     starts {first!r} … ends {last!r}")
    DATA["inspection"] = idx

    sec("S14 Seeds: buckets and retrieval")
    seeds = [json.loads(x) for x in SEEDS.read_text(encoding="utf-8").splitlines() if x.strip()]
    ans = [s for s in seeds if s.get("answerable")]
    ok = single = 0
    groups = {}
    for s in ans:
        gs = []
        for g in s["evidence_groups"]:
            alts = []
            for alt in g["alternatives"]:
                segs = [S.to_doc(starts, sg["page"], sg["char_start"], sg["char_end"]) for sg in alt["segments"]]
                if len(segs) == 1:
                    single += 1
                    ok += all(" ".join(T[a:b].split()) == " ".join(alt["quote"].split()) for a, b in segs)
                alts.append(segs)
            gs.append(alts)
        groups[s["qid"]] = gs
    print(f"seeds {len(seeds)} · answerable {len(ans)} · single-segment quotes that match the snapshot exactly: {ok} of {single}")
    v0_ranges = [(c["a"], c["b"]) for c in v0]

    def in_one(segs, ranges):              # research §5: the whole alternative inside one chunk
        lo, hi = min(x for x, _ in segs), max(y for _, y in segs)
        return any(a <= lo and hi <= b for a, b in ranges)

    for s in ans:
        straddle = not all(any(in_one(alt, v0_ranges) for alt in g) for g in groups[s["qid"]])
        pages_ = sorted({S.page_of(starts, x) for g in groups[s["qid"]] for alt in g for x, _ in alt})
        crosses = any(len({S.page_of(starts, x) for x, _ in alt} | {S.page_of(starts, y - 1) for _, y in alt}) > 1
                      for g in groups[s["qid"]] for alt in g)
        print(f"{s['qid']} {s['category']:22} groups {len(groups[s['qid']])} pages {pages_} straddles_v0={straddle} crosses_page={crosses}")

    if not onnx_dir:
        print("retrieval: SKIPPED (no MiniLM directory given)")
    else:
        sys.path.insert(0, str(HERE))
        from i2_onnx_embed import Embedder
        em = Embedder(onnx_dir)
        Q = em.encode([s["question"] for s in ans])
        res = {}
        budget = 4 * stats(v0)["mean"]
        print(f"MiniLM-L6 ONNX export; equal budget = 4 x v0 mean chunk length = {budget:.0f} characters")
        for name, ch in arms.items():
            C = em.encode([c["text"] for c in ch])
            ntok = em.n_tokens([c["text"] for c in ch])
            Sm = Q @ C.T
            ce4, ceb, ranks, hits = [], [], [], []
            for qi, s in enumerate(ans):
                order = list((-Sm[qi]).argsort(kind="stable"))
                def ce_at(k):
                    rng = [(ch[j]["a"], ch[j]["b"]) for j in order[:k]]
                    return all(any(_cov(alt, rng) for alt in g) for g in groups[s["qid"]])
                ce4.append(int(ce_at(4)))
                used, k = 0, 0
                while k < len(order) and used + (ch[order[k]]["b"] - ch[order[k]]["a"]) <= budget:
                    used += ch[order[k]]["b"] - ch[order[k]]["a"]
                    k += 1
                ceb.append(int(ce_at(k)))
                r = next((k for k in range(1, 11) if ce_at(k)), None)
                ranks.append(r)
                hit = next((k + 1 for k, j in enumerate(order[:10])
                            if any(_cov(alt, [(ch[j]["a"], ch[j]["b"])]) for g in groups[s["qid"]] for alt in g)), None)
                hits.append(hit)
            mrr = sum(1 / r for r in ranks if r) / len(ranks)
            hmrr = sum(1 / r for r in hits if r) / len(hits)
            res[name] = {"hit_rank": hits, "hit_mrr10": round(hmrr, 3), "ce4": ce4, "ce_budget": ceb, "ce_rank": ranks, "mrr10": round(mrr, 3),
                         "max_wordpiece": max(ntok), "over256": sum(t > 256 for t in ntok)}
            print(f"{name:36} CE@4 {sum(ce4)}/{len(ans)} {ce4} · CE@budget {sum(ceb)}/{len(ans)} · CE-rank {ranks} "
                  f"· MRR@10(CE) {mrr:.3f} · first-hit ranks {hits} MRR@10 {hmrr:.3f} · WordPiece max {max(ntok)}, > 256: {sum(t > 256 for t in ntok)}")
        DATA["retrieval"] = res
        d002 = Q[1] @ em.encode([c["text"] for c in v0]).T
        print(f"check vs P4 K3: v0 D-002 top-5 {list((-d002).argsort(kind='stable')[:5])} "
              f"cos {[round(float(d002[j]), 4) for j in (-d002).argsort(kind='stable')[:5]]}")

    sec("S15 Data file")
    out = HERE / "i2_lesson_data.json"
    out.write_text(json.dumps(DATA, indent=1, default=str), encoding="utf-8")
    print(f"wrote {out.name} sha256 {hashlib.sha256(out.read_bytes()).hexdigest()[:12]}")


def _cov(segs, ranges):
    return all(any(a <= x and y <= b for a, b in ranges) for x, y in segs)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
