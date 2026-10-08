"""Executable acceptance check for the Codex P0/P1 corrections (M-01, M-02, M-04, M-05, M-06, M-07) and the
round-2 re-review corrections (R-01/B-01, R-02, R-03, R-04, R-05, R-06, R-07; reviews/CORRECTIONS_SPEC_R2_2026-10-08.md).

A self-contained reference implementation of the contracts AS WRITTEN in the edited plan documents:
  06 §2.3, §2.4, §5.3, §6.1, §6.4, §6.7, §7.2, §7.3, §8.4, §9.2, §9.3, §9.6; 07 H.1/H.3; 03 §2.1; 05 §6.1;
  02 concept cards; 08 Part 4 and Part 7; BACKBONE §3.
Round 2: the reference loader is validate_binding() (fail closed, 06 §5.3 rule 4) using the EXACT 06 §5.3 snapshot_id
recipe (executed from the document); gold_to_doc / chunk_segment_to_doc are the two public decoders (06 §2.3/§6.4).
It reads those documents, extracts their JSON / JSONL / Python blocks and registry table, and tests them
against the real Corpus D text (PyMuPDF page.get_text(), pages joined with "\\n").

Usage (stdlib + PyMuPDF; numpy optional, only to execute 06 §9.3's numpy sketch as well):
    python -I contracts_check.py <path-to-Understanding_Climate_Change.pdf> [--root <rag_learning dir>]
Exit code 0 iff every check passes. Nothing here modifies any file.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import random
import re
import sys
import types
from pathlib import Path

# ----------------------------------------------------------------------------------------------------
# result bookkeeping
# ----------------------------------------------------------------------------------------------------
RESULTS: list[tuple[str, str, bool, str]] = []
INFO: list[str] = []


def check(fid: str, name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((fid, name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {fid} {name}" + (f" -- {detail}" if detail else ""))
    return bool(ok)


def info(msg: str) -> None:
    INFO.append(msg)
    print(f"[INFO] {msg}")


def raises(exc, fn, *a, **k) -> bool:
    """True iff fn raises `exc`; any other exception (or none) is False, so a broken guard records a FAIL."""
    try:
        fn(*a, **k)
    except exc:
        return True
    except Exception:
        return False
    return False


def holds(fn) -> bool:
    """Evaluate a check expression; an unexpected exception counts as a FAIL instead of aborting the run."""
    try:
        return bool(fn())
    except Exception as e:
        print(f"[INFO]   (check raised {type(e).__name__}: {e})")
        return False


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------------------------------
# markdown helpers (fence-aware, so '# comment' lines inside code blocks are never taken as headings)
# ----------------------------------------------------------------------------------------------------
def section(md: str, heading_prefix: str) -> str:
    lines = md.splitlines()
    fence = False
    start = level = None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#+)\s+(.*)$", ln)
        if not m:
            continue
        if start is None and m.group(2).startswith(heading_prefix):
            start, level = i, len(m.group(1))
        elif start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    if start is None:
        raise KeyError(f"heading not found: {heading_prefix!r}")
    return "\n".join(lines[start:])


def code_blocks(md: str, lang: str) -> list[str]:
    return re.findall(r"^```" + re.escape(lang) + r"[ \t]*\n(.*?)^```", md, flags=re.S | re.M)


def ast_functions(src: str, names: set[str]) -> str:
    """Return the source of selected top-level functions from a code block that may import absent modules."""
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            node.decorator_list = []
            out.append(ast.unparse(node))
    return "\n\n".join(out)


def norm_ws(s: str) -> str:
    return " ".join(s.split())


# ====================================================================================================
# M-01 — frozen-text snapshot, page_table, one coordinate system, fail closed (06 §2.3, §5.3, §6.1, §6.4)
# ====================================================================================================
class SnapshotMismatch(Exception):
    pass


class BindingError(SnapshotMismatch):
    """R-02: the dataset/manifest/snapshot binding failed validation; raised BEFORE any gold label is translated."""


PARSER = {"backend": "pymupdf", "version": None, "call": "page.get_text()", "options": {}}
CLEANING_NONE = {"version": "none", "steps": []}
CREATED_UTC_FIXTURE = "2026-10-08T00:00:00Z"   # fixture value; created_utc is not an input of snapshot_id
HEADER_REQUIRED = ("snapshot_id", "snapshot_manifest_sha256", "scorer_version", "evidence_logic_version")
MANIFEST_REQUIRED = ("snapshot_id", "corpus", "corpus_version", "created_utc", "parser", "cleaning", "encoding",
                     "newline", "page_join", "docs")
DOC_REQUIRED = ("doc_id", "pdf_sha256", "bytes", "pages", "doc_text_sha256", "page_table")
ROW_REQUIRED = ("page", "doc_char_start", "doc_char_end", "text_sha256")
PARSER_REQUIRED = ("backend", "version", "call", "options")
CLEANING_REQUIRED = ("version", "steps")   # R2-01: every nested cleaning field in the 06 §5.3 manifest is required

RECIPE_06: str | None = None   # the 06 §5.3 "Exact snapshot_id formula" code block, loaded from the document in main()


def snapshot_id_06(parser: dict, cleaning: dict, doc_hashes: dict[str, str]) -> str:
    """R-02 item 6: execute the 06 §5.3 snapshot_id recipe EXACTLY as written in the document (no private
    serialization). Inputs are the names the recipe uses."""
    ns = {"json": json, "hashlib": hashlib, "backend": parser["backend"], "version": parser["version"],
          "options": parser["options"], "cleaning_version": cleaning["version"], "doc_text_sha256": dict(doc_hashes)}
    exec(compile(RECIPE_06, "06_5.3_snapshot_id", "exec"), ns)
    return ns["snapshot_id"]


def snapshot_id_transcribed(parser: dict, cleaning: dict, doc_hashes: dict[str, str]) -> str:
    """Independent hand transcription of the same recipe; a check asserts it equals snapshot_id_06, so a silent
    edit of the 06 formula is detected. Note: the recipe's "page_join=\\\\n" is a literal backslash + 'n'."""
    parts = ["snapshot-v1", f"parser={parser['backend']}@{parser['version']}",
             "options=" + json.dumps(parser["options"], sort_keys=True), f"cleaning={cleaning['version']}",
             "page_join=\\n"]
    parts += [f"{d}:{doc_hashes[d]}" for d in sorted(doc_hashes)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


# backwards-compatible name used by the M-04 checks: now the 06 §5.3 recipe
def compute_snapshot_id(doc_hashes: dict[str, str], parser: dict, cleaning: dict) -> str:
    return snapshot_id_06(parser, cleaning, doc_hashes)


def build_manifest(doc_id: str, pages: list[str], pdf_bytes: bytes, parser: dict, cleaning: dict,
                   corpus: str = "D") -> dict:
    page_table, pos = [], 0
    for i, t in enumerate(pages, 1):
        page_table.append({"page": i, "doc_char_start": pos, "doc_char_end": pos + len(t),
                           "text_sha256": sha256_hex(t)})
        pos += len(t) + 1                                  # page_join = "\n"
    doc_text = "\n".join(pages)
    d = {"doc_id": doc_id, "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(), "bytes": len(pdf_bytes),
         "pages": len(pages), "doc_text_sha256": sha256_hex(doc_text), "page_table": page_table}
    return {"snapshot_id": snapshot_id_06(parser, cleaning, {doc_id: d["doc_text_sha256"]}),
            "corpus": corpus, "corpus_version": "1.0", "created_utc": CREATED_UTC_FIXTURE,
            "parser": parser, "cleaning": cleaning,
            "encoding": "utf-8", "newline": "\n", "page_join": "\n", "docs": [d]}


def manifest_bytes(manifest: dict) -> bytes:
    """The manifest file 'as written' (UTF-8). The validator only ever sees these bytes."""
    return json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")


def make_header(mbytes: bytes, snapshot_id: str, **extra) -> dict:
    return {"dataset_version": "fixture", "snapshot_id": snapshot_id,
            "snapshot_manifest_sha256": hashlib.sha256(mbytes).hexdigest(), "scorer_version": "s1",
            "evidence_logic_version": "e1", **extra}


def validate_binding(dataset_header: dict, mbytes: bytes, snapshot_texts: dict[str, list[str]]) -> "Snapshot":
    """R-02 reference loader binding check (06 §5.3 rule 4, §6.1). Fails closed with BindingError; returns a
    validated Snapshot only when every condition holds. snapshot_texts = {doc_id: [page_text, ...]}."""
    # 1. required binding fields (dataset header)
    miss = [k for k in HEADER_REQUIRED if k not in dataset_header or dataset_header[k] in (None, "")]
    if miss:
        raise BindingError(f"dataset header missing {miss}")
    # 2. digest of the exact manifest bytes
    got = hashlib.sha256(mbytes).hexdigest()
    if dataset_header["snapshot_manifest_sha256"] != got:
        raise BindingError(f"snapshot_manifest_sha256 {dataset_header['snapshot_manifest_sha256'][:16]} != "
                           f"sha256(manifest bytes) {got[:16]}")
    try:
        man = json.loads(mbytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise BindingError(f"manifest is not UTF-8 JSON: {e}") from None
    # 1. required binding fields (manifest)
    miss = [k for k in MANIFEST_REQUIRED if k not in man]
    miss += [f"parser.{k}" for k in PARSER_REQUIRED if k not in man.get("parser", {})]
    miss += [f"cleaning.{k}" for k in CLEANING_REQUIRED if k not in man.get("cleaning", {})]   # R2-01
    for d in man.get("docs", []):
        miss += [f"{d.get('doc_id')}.{k}" for k in DOC_REQUIRED if k not in d]
        for r in d.get("page_table", []):
            miss += [f"{d.get('doc_id')}.page_table.{k}" for k in ROW_REQUIRED if k not in r]
    if miss:
        raise BindingError(f"manifest missing {sorted(set(miss))}")
    if man["encoding"] != "utf-8" or man["newline"] != "\n" or man["page_join"] != "\n":
        raise BindingError("snapshot-v1 recipe fixes encoding utf-8, newline and page_join '\\n'")
    if not man["docs"] or set(snapshot_texts) != {d["doc_id"] for d in man["docs"]}:
        raise BindingError("snapshot texts and manifest docs differ")
    # 3. page-table structural integrity, per document
    join = man["page_join"]
    doc_hashes = {}
    for d in man["docs"]:
        doc_id, rows, texts = d["doc_id"], d["page_table"], snapshot_texts[d["doc_id"]]
        if not rows or [r["page"] for r in rows] != list(range(1, len(rows) + 1)):
            raise BindingError(f"{doc_id}: pages not numbered 1..n in order")
        if d["pages"] != len(rows) or len(texts) != len(rows):
            raise BindingError(f"{doc_id}: page count manifest={d['pages']} table={len(rows)} texts={len(texts)}")
        if rows[0]["doc_char_start"] != 0:
            raise BindingError(f"{doc_id}: page_table[0].doc_char_start != 0")
        for i, (r, t) in enumerate(zip(rows, texts)):
            if r["doc_char_end"] - r["doc_char_start"] != len(t):
                raise BindingError(f"{doc_id} p.{r['page']}: end - start != len(page_text)")
            if i + 1 < len(rows) and rows[i + 1]["doc_char_start"] != r["doc_char_end"] + len(join):
                raise BindingError(f"{doc_id} p.{rows[i + 1]['page']}: start != previous end + len(page_join)")
            if sha256_hex(t) != r["text_sha256"]:
                raise BindingError(f"{doc_id} p.{r['page']}: text_sha256 differs from manifest")
        doc_text = join.join(texts)
        if rows[-1]["doc_char_end"] != len(doc_text):
            raise BindingError(f"{doc_id}: last doc_char_end {rows[-1]['doc_char_end']} != len(doc_text) {len(doc_text)}")
        if sha256_hex(doc_text) != d["doc_text_sha256"]:
            raise BindingError(f"{doc_id}: doc_text_sha256 differs from the join of the pages")
        doc_hashes[doc_id] = d["doc_text_sha256"]
    # 4. snapshot_id recomputed with the exact 06 §5.3 recipe
    sid = snapshot_id_06(man["parser"], man["cleaning"], doc_hashes)
    if not (sid == man["snapshot_id"] == dataset_header["snapshot_id"]):
        raise BindingError(f"snapshot_id recomputed {sid} / manifest {man['snapshot_id']} / "
                           f"dataset {dataset_header['snapshot_id']}")
    return Snapshot(man, snapshot_texts, _validated=True)


def legacy_verify_r1(manifest: dict, snapshot_texts: dict[str, list[str]]) -> None:
    """The ROUND-1 checker's verify() (page text hash + page length only), kept ONLY as a negative control that
    reproduces the Codex R-02 probe: it accepts a page table whose page 2 is shifted by +1."""
    for d in manifest["docs"]:
        for r, t in zip(d["page_table"], snapshot_texts[d["doc_id"]]):
            if sha256_hex(t) != r["text_sha256"] or r["doc_char_end"] - r["doc_char_start"] != len(t):
                raise SnapshotMismatch("legacy check failed")


class Snapshot:
    """The stored snapshot text (one list of page texts per doc) bound to a manifest. Construct it through
    validate_binding(); the two public decoders below are the only page -> document conversions (R-05)."""

    def __init__(self, manifest: dict, pages_by_doc: dict[str, list[str]], _validated: bool = False):
        if not _validated:
            raise BindingError("construct Snapshot through validate_binding()")
        self.manifest = manifest
        self.snapshot_id = manifest["snapshot_id"]
        self.pages = pages_by_doc
        self.join = manifest["page_join"]
        self.table = {d["doc_id"]: d["page_table"] for d in manifest["docs"]}

    def doc_text(self, doc_id: str) -> str:
        return self.join.join(self.pages[doc_id])

    def page_text(self, doc_id: str, page: int) -> str:
        return self.pages[doc_id][page - 1]

    def _row(self, doc_id: str, page: int) -> dict:
        rows = self.table[doc_id]
        if not 1 <= page <= len(rows):
            raise ValueError(f"page {page} outside 1..{len(rows)}")
        return rows[page - 1]

    def gold_to_doc(self, doc_id: str, page: int, a: int, b: int) -> tuple[int, int]:
        """R-05 gold decoder: authored segments lie inside the PHYSICAL page text, 0 <= a < b <= len(page_text)."""
        row = self._row(doc_id, page)
        if not 0 <= a < b <= len(self.page_text(doc_id, page)):
            raise ValueError(f"gold segment [{a},{b}) outside physical text of page {page}")
        return row["doc_char_start"] + a, row["doc_char_start"] + b

    def chunk_segment_to_doc(self, doc_id: str, page: int, a: int, b: int) -> tuple[int, int]:
        """R-05 chunk decoder: a chunk-derived page segment may also include the virtual page-join character,
        assigned to the preceding page, so on every page but the last b may reach len(page_text) + len(join)."""
        row = self._row(doc_id, page)
        extra = len(self.join) if page < len(self.table[doc_id]) else 0
        if not 0 <= a < b <= len(self.page_text(doc_id, page)) + extra:
            raise ValueError(f"chunk segment [{a},{b}) outside page {page} (+ join)")
        return row["doc_char_start"] + a, row["doc_char_start"] + b

    to_doc = gold_to_doc   # the §9.6 sketch's snapshot.to_doc is the gold decoder (06 §6.4)

    def to_page_segments(self, doc_id: str, a: int, b: int) -> list[tuple[int, int, int]]:
        """Document range -> page-relative segments. Page p owns its text plus the joining '\\n' after it
        (same rule as 07 H.3 to_page_segments), so segments tile [a, b) exactly."""
        rows = self.table[doc_id]
        doc_len = rows[-1]["doc_char_end"]
        out = []
        for i, row in enumerate(rows):
            lo = row["doc_char_start"]
            hi = rows[i + 1]["doc_char_start"] if i + 1 < len(rows) else doc_len
            if a < hi and b > lo:
                out.append((row["page"], max(a, lo) - lo, min(b, hi) - lo))
        return out


def load_dataset(items: list[dict], header: dict, mbytes: bytes, snapshot_texts: dict[str, list[str]],
                 index_snapshot_id: str, scored: bool = True) -> list[dict]:
    """Loader contract (06 §5.3 rule 4, §6.1, §6.4): validate the binding FIRST (validate_binding, fail closed),
    refuse an index bound to another snapshot_id, reject unassigned splits in scored runs, and only then convert
    page-relative gold segments to doc offsets through the public gold decoder."""
    snapshot = validate_binding(header, mbytes, snapshot_texts)
    if index_snapshot_id != snapshot.snapshot_id:
        raise SnapshotMismatch(f"index {index_snapshot_id} != snapshot {snapshot.snapshot_id}")
    out = []
    for it in items:
        if scored and it.get("split") == "unassigned":
            raise ValueError(f"{it['qid']}: split 'unassigned' is rejected in scored runs (06 §6.1)")
        groups = []
        for g in it["evidence_groups"]:
            alts = []
            for alt in g["alternatives"]:
                segs = [(s["doc_id"], *snapshot.gold_to_doc(s["doc_id"], s["page"], s["char_start"], s["char_end"]))
                        for s in alt["segments"]]
                alts.append(segs)
            groups.append(alts)
        out.append({**it, "_groups_doc": groups})
    return out


# ====================================================================================================
# M-02 — evidence groups (AND) of alternatives (OR); CE@k primary; Group-Recall / Span-Coverage diagnostics
# ====================================================================================================
def _merge(ranges):
    out = []
    for a, b in sorted(ranges):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _covered_fraction(segments, chunks, texts) -> float:
    """segments/chunks: (doc_id, a, b) in DOCUMENT offsets. tolerance = whitespace-only: only non-whitespace
    characters of the segments are counted, so the page-join '\\n' or a cut on a space never matters."""
    total = hit = 0
    for doc, a, b in segments:
        union = _merge([(x, y) for d, x, y in chunks if d == doc])
        t = texts[doc]
        for i in range(a, b):
            if t[i].isspace():
                continue
            total += 1
            if any(x <= i < y for x, y in union):
                hit += 1
    return 1.0 if total == 0 else hit / total


def group_scores(groups, chunks, texts):
    best = [max(_covered_fraction(alt, chunks, texts) for alt in g) for g in groups]
    sat = [b == 1.0 for b in best]
    return sat, best


def ce(groups, chunks, texts) -> int:
    sat, _ = group_scores(groups, chunks, texts)
    return int(all(sat))


def group_recall(groups, chunks, texts) -> float:
    sat, _ = group_scores(groups, chunks, texts)
    return sum(sat) / len(sat)


def span_coverage(groups, chunks, texts) -> float:
    _, best = group_scores(groups, chunks, texts)
    return sum(best) / len(best)


def rel(chunk, groups, texts) -> int:
    """chunk_relevance = any_overlap: overlaps >= 1 non-whitespace char of any segment of any alternative."""
    d, x, y = chunk
    t = texts[d]
    for g in groups:
        for alt in g:
            for doc, a, b in alt:
                if doc == d and any(not t[i].isspace() for i in range(max(a, x), min(b, y))):
                    return 1
    return 0


def complete_evidence(groups, chunk_ranges, doc_text) -> int:
    """Signature used by the 06 §9.6 sketch: single document; groups = AND list of OR lists of [(a, b), ...]."""
    G = [[[("d", a, b) for a, b in alt] for alt in g] for g in groups]
    return ce(G, [("d", a, b) for a, b in chunk_ranges], {"d": doc_text})


# ====================================================================================================
# M-04 — chunk ids for joins/traces; content-addressed embedding cache key
# ====================================================================================================
def ref_embedding_cache_key(text, *, provider, model_id, model_revision, input_type, preprocessing_version):
    """sha256(provider|model_id|model_revision|input_type|preprocessing_version|text) (06 §2.4, 07 H.3)."""
    return sha256_hex("|".join([provider, model_id, model_revision, input_type, preprocessing_version, text]))


def load_07_modules(md07: str):
    """Execute 07 H.1 (as ragkit._core) and 07 H.3 (as ragkit.chunking) exactly as written."""
    h1 = code_blocks(section(md07, "H.1 Minimal implementation"), "python")[0]
    h3_blocks = code_blocks(section(md07, "H.3 Reusable design"), "python")
    pkg = types.ModuleType("ragkit")
    pkg.__path__ = []
    sys.modules["ragkit"] = pkg
    core = types.ModuleType("ragkit._core")
    sys.modules["ragkit._core"] = core
    exec(compile(h1, "07_H1", "exec"), core.__dict__)
    chunking = types.ModuleType("ragkit.chunking")
    sys.modules["ragkit.chunking"] = chunking
    exec(compile(h3_blocks[0], "07_H3", "exec"), chunking.__dict__)
    return core, chunking, h3_blocks[1]


# ====================================================================================================
# M-05 — paired comparison aligned by qid; group-level splits; cluster bootstrap
# ====================================================================================================
def ref_paired_bootstrap(a: dict, b: dict, groups: dict | None = None, n_boot: int = 2000, seed: int = 0,
                         _trace: list | None = None):
    if set(a) != set(b):
        raise ValueError(f"qid sets differ: {sorted(set(a) ^ set(b))[:5]}")
    qids = sorted(a)
    d = {q: b[q] - a[q] for q in qids}
    gmap = groups or {q: q for q in qids}
    labels = sorted({gmap[q] for q in qids})
    members = {g: [q for q in qids if gmap[q] == g] for g in labels}
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        pick = [labels[rng.randrange(len(labels))] for _ in labels]   # resample whole groups
        qs = [q for g in pick for q in members[g]]
        if _trace is not None:
            _trace.append(qs)
        means.append(sum(d[q] for q in qs) / len(qs))
    means.sort()
    lo, hi = means[int(0.025 * (n_boot - 1))], means[int(0.975 * (n_boot - 1))]
    return sum(d.values()) / len(d), (lo, hi)


COMPARISON_KEYS = ("dataset_sha256", "snapshot_id", "qids", "labels_sha256", "split", "scorer_version")


def make_comparison_meta(*, qids, **keys) -> dict:
    """R-07: comparison metadata stores qids as a CANONICAL SORTED list, enforced at construction."""
    q = list(qids)
    if len(set(q)) != len(q):
        raise ValueError("duplicate qids in comparison metadata")
    meta = {**keys, "qids": sorted(q)}
    missing = [k for k in COMPARISON_KEYS if k not in meta]
    if missing:
        raise ValueError(f"comparison metadata missing {missing}")
    return meta


def comparison_keys_match(ra: dict, rb: dict) -> bool:
    """R-07: qids are compared as SETS (order never causes a rejection); every other key must be identical."""
    for k in COMPARISON_KEYS:
        same = set(ra[k]) == set(rb[k]) if k == "qids" else ra[k] == rb[k]
        if not same:
            raise ValueError(f"comparison key differs: {k}")
    return True


def assign_splits(items: list[dict], fractions=(("dev", 0.3), ("test", 0.35), ("holdout", 0.35)), seed=0):
    """Group-level, category-stratified assignment (06 §6.3 item 6). Fractions are the 06 Assumption/[P]."""
    by_group: dict[str, list[dict]] = {}
    for it in items:
        by_group.setdefault(it["group"], []).append(it)
    strata: dict[str, list[str]] = {}
    for g, its in by_group.items():
        base = next((i for i in its if i["qid"] == g), its[0])
        strata.setdefault(base["category"], []).append(g)
    rng = random.Random(seed)
    out = {}
    for cat in sorted(strata):
        gs = sorted(strata[cat])
        rng.shuffle(gs)
        n, cum, k = len(gs), 0.0, 0
        for name, f in fractions:
            cum += f
            upto = round(cum * n)
            for g in gs[k:upto]:
                for it in by_group[g]:
                    out[it["qid"]] = name
            k = upto
    return out


# ====================================================================================================
# M-06 — Wilson interval and exact Clopper-Pearson bound
# ====================================================================================================
def wilson(x: int, n: int, z: float = 1.959963984540054):
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def binom_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def clopper_pearson_lower(x: int, n: int, alpha: float = 0.05) -> float:
    """Exact two-sided (1-alpha) lower bound: p such that P(X >= x | p) = alpha/2 (bisection)."""
    if x == 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 1 - binom_cdf(x - 1, n, mid) < alpha / 2:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# R-03 — Cohen's kappa is not a proportion: paired (cluster) bootstrap over labelled units
def cohens_kappa(r1: list, r2: list) -> float | None:
    """kappa = (p_o - p_e) / (1 - p_e); None when undefined (p_e == 1, i.e. both raters constant and equal)."""
    n = len(r1)
    cats = sorted(set(r1) | set(r2))
    po = sum(a == b for a, b in zip(r1, r2)) / n
    pe = sum((r1.count(c) / n) * (r2.count(c) / n) for c in cats)
    return None if pe == 1 else (po - pe) / (1 - pe)


def kappa_bootstrap(r1: list, r2: list, clusters: list | None = None, n_boot: int = 2000, seed: int = 0,
                    _trace: list | None = None):
    """Paired bootstrap: each (rater1, rater2) label pair is resampled together; with clusters (answers), whole
    clusters are resampled. Returns (kappa, (lo, hi) 95% percentile interval, n_undefined_resamples)."""
    units = list(range(len(r1)))
    cl = clusters or units
    labels = sorted(set(cl), key=str)
    members = {g: [u for u in units if cl[u] == g] for g in labels}
    rng = random.Random(seed)
    ks, undefined = [], 0
    for _ in range(n_boot):
        us = [u for g in (labels[rng.randrange(len(labels))] for _ in labels) for u in members[g]]
        if _trace is not None:
            _trace.append(us)
        k = cohens_kappa([r1[u] for u in us], [r2[u] for u in us])
        if k is None:
            undefined += 1
        else:
            ks.append(k)
    point = cohens_kappa(r1, r2)
    if point is None or not ks:   # R2-02: kappa undefined (e.g. constant identical labels) -> no interval, no certification
        return point, None, undefined
    ks.sort()
    return point, (ks[int(0.025 * (len(ks) - 1))], ks[int(0.975 * (len(ks) - 1))]), undefined


# ====================================================================================================
# M-07 — typed prerequisite registry (03 §2.1) vs 02 concept-card Pre lines
# ====================================================================================================
ID_RE = r"(?:I-CMP|[OPCMIRQXVDASK]\d)"
PHASE = {"O": 0, "P": 1, "C": 2, "M": 3, "I": 4, "R": 5, "Q": 6, "X": 7, "V": 8, "D": 9, "A": 10, "S": 11, "K": 12}


def phase_of(cid: str) -> int:
    return PHASE[cid[0]]


def ids_in(s: str) -> list[str]:
    s = s.replace("\\|", "|")
    out = []
    for a, b in re.findall(r"\b(" + ID_RE + r")\s*[–-]\s*(" + ID_RE + r")\b", s):   # ranges like C1–C5
        if a[0] == b[0] and a[1:].isdigit() and b[1:].isdigit():
            out += [f"{a[0]}{i}" for i in range(int(a[1:]), int(b[1:]) + 1)]
    s = re.sub(r"\b(" + ID_RE + r")\s*[–-]\s*(" + ID_RE + r")\b", " ", s)
    return out + re.findall(r"(?<![\w-])" + ID_RE + r"(?![\w])", s)


def parse_registry(md03: str) -> dict:
    sec = section(md03, "2.1 Edge list")
    rows = [ln for ln in sec.splitlines() if ln.startswith("| ") and not ln.startswith("| ID ")
            and not ln.startswith("|---")]
    reg = {}
    for ln in rows:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", ln.strip())[1:-1]]
        cid, tier, r_all, r_any, r_gate, r_exp, adv, unl = cells
        groups = [ids_in(g) for g in re.findall(r"\[([^\]]*)\]", r_any)]
        reg[cid] = {"tier": tier.split()[0] if tier != "S/U (drawn as S)" else "S",
                    "all": ids_in(r_all), "any": groups,
                    "gate": set(re.findall(r"Gate\s*(\d+→\d+)", r_gate)),
                    "exposure": ids_in(r_exp), "advice": ids_in(adv), "unlocks": ids_in(unl)}
    return reg


def parse_02_pre(md02: str) -> dict:
    out = {}
    cur = None
    for ln in md02.splitlines():
        m = re.match(r"^#### (" + ID_RE + r") — ", ln)
        if m:
            cur = m.group(1)
            continue
        if cur and ln.startswith("- **Pre:**"):
            body = ln[len("- **Pre:**"):].split(" · **Failure")[0]
            typed = re.search(r"`([^`]*)`", body)
            rec = {"all": [], "any": [], "gate": set(), "exposure": [], "advice": [], "raw": body.strip()}
            if typed:
                t = typed.group(1)
                for kind, inner in re.findall(r"(all|any|gate|exposure)\{([^}]*)\}", t):
                    if kind == "gate":
                        rec["gate"] |= set(re.findall(r"\d+→\d+", inner))
                    elif kind == "any":
                        rec["any"].append(ids_in(inner))
                    else:
                        rec[kind] += ids_in(inner)
            else:
                b = body
                for adv in re.findall(r"pairs with (" + ID_RE + r")", b):
                    rec["advice"].append(adv)
                b = re.sub(r"pairs with " + ID_RE, " ", b)
                for adv in re.findall(r"(" + ID_RE + r") \(concurrent\)", b):
                    rec["advice"].append(adv)
                b = re.sub(ID_RE + r" \(concurrent\)", " ", b)
                rec["all"] = ids_in(b)
            out[cur] = rec
            cur = None
    return out


def closure(reg: dict, cid: str, kinds=("all", "any", "exposure")) -> set:
    seen, stack = set(), [cid]
    while stack:
        c = stack.pop()
        r = reg[c]
        nxt = []
        if "all" in kinds:
            nxt += r["all"]
        if "any" in kinds:
            nxt += [m for g in r["any"] for m in g]
        if "exposure" in kinds:
            nxt += r["exposure"]
        for p in nxt:
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


def can_unlock(reg: dict, cid: str, mastered: set, exposed: set, gates: set) -> bool:
    """R-04 (03 §2.1 unlock rule): requires_all and every any-group are checked against `mastered`;
    requires_exposure against `exposed | mastered`; requires_gate against passed gates. Exposure never
    substitutes for mastery of an all/any prerequisite."""
    r = reg[cid]
    seen = set(exposed) | set(mastered)
    return (all(p in mastered for p in r["all"]) and all(any(m in mastered for m in g) for g in r["any"])
            and r["gate"] <= gates and all(e in seen for e in r["exposure"]))


def reachable(reg: dict, target: str, mastered_goal: set, exposed: set, gates: set) -> tuple[bool, set]:
    """Master concepts of `mastered_goal` one at a time, each only once can_unlock() holds; True iff every goal
    concept gets mastered and `target` then unlocks."""
    m: set = set()
    progress = True
    while progress:
        progress = False
        for c in sorted(mastered_goal - m):
            if can_unlock(reg, c, m, exposed, gates):
                m.add(c)
                progress = True
    return (m == mastered_goal and can_unlock(reg, target, m, exposed, gates)), m


# ====================================================================================================
# B-01 / R-01 — 08 Part 7 approval gates and Part 4 decision rows
# ====================================================================================================
GATE_ID_RE = r"(?:DEC-\d[a-z]?|MX-\d+|BL-\d+|[SCVPRE]-\d+)"


def expand_gate_ids(s: str) -> list[str]:
    """'S-1…S-6; DEC-1a, V-3' -> ['S-1', ..., 'S-6', 'DEC-1a', 'V-3'] (ranges written with … or – or ...)."""
    out = []
    rng = r"\b(" + GATE_ID_RE + r")\s*(?:…|\.\.\.|–)\s*(" + GATE_ID_RE + r")\b"
    for a, b in re.findall(rng, s):
        pa, na = a.rsplit("-", 1)
        pb, nb = b.rsplit("-", 1)
        if pa != pb or not (na.isdigit() and nb.isdigit()):
            raise ValueError(f"bad range {a}…{b}")
        out += [f"{pa}-{i}" for i in range(int(na), int(nb) + 1)]
    s = re.sub(rng, " ", s)
    return out + re.findall(r"(?<![\w-])" + GATE_ID_RE + r"(?![\w])", s)


def parse_gate_sections(md08: str) -> dict[str, dict[str, dict]]:
    """{'A': {item_id: {'ticked': bool, 'text': line}}, 'B': ..., 'C': ...} from the 08 Part 7 checklists."""
    out = {}
    for g in "ABC":
        sec = section(md08, f"Approval gate {g}")
        items: dict[str, dict] = {}
        dup = []
        for ln in sec.splitlines():
            m = re.match(r"^- \[( |x)\] (" + GATE_ID_RE + r")\.", ln)
            if m:
                if m.group(2) in items:
                    dup.append(m.group(2))
                items[m.group(2)] = {"ticked": m.group(1) == "x", "text": ln}
        if dup:
            raise ValueError(f"gate {g}: duplicate items {dup}")
        out[g] = items
    return out


def parse_gate_table(sec: str) -> dict[str, list[str]]:
    """Gate -> item IDs from a '| **A — …** | items | …' table (08 Part 7 or BACKBONE §3). IDs with a leading zero
    (e.g. 'R-02' = a review finding, not a checklist item) are not gate items and are dropped."""
    out = {}
    for ln in sec.splitlines():
        m = re.match(r"^\| \*\*([ABC]) — [^|]*\| ([^|]*)\|", ln)
        if m:
            out[m.group(1)] = [i for i in expand_gate_ids(m.group(2)) if not re.search(r"-0\d", i)]
    return out


def part4_rows(md08: str) -> dict[str, str]:
    sec = section(md08, "Part 4")
    return {m.group(1): ln for ln in sec.splitlines() for m in [re.match(r"^\| (D-\d\d) \|", ln)] if m}


# ====================================================================================================
# main
# ====================================================================================================
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root)
    md02 = (root / "02_RAG_MASTER_LEARNING_PLAN.md").read_text(encoding="utf-8")
    md03 = (root / "03_RAG_CONCEPT_DEPENDENCY_MAP.md").read_text(encoding="utf-8")
    md06 = (root / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
    md07 = (root / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
    md05 = (root / "05_LEARNING_AND_RETENTION_SYSTEM.md").read_text(encoding="utf-8")
    md08 = (root / "08_GAP_ANALYSIS_AND_DECISIONS.md").read_text(encoding="utf-8")
    mdbb = (root / "curriculum" / "CURRICULUM_BACKBONE.md").read_text(encoding="utf-8")
    global RECIPE_06
    RECIPE_06 = code_blocks(section(md06, "5.3 Corpus freezing"), "python")[0]

    import fitz  # PyMuPDF
    pdf_bytes = Path(args.pdf).read_bytes()
    pages = [p.get_text() for p in fitz.open(args.pdf)]
    parser = {**PARSER, "version": fitz.VersionBind}
    print(f"python {sys.version.split()[0]} | PyMuPDF {fitz.VersionBind} | root {root}")
    print(f"pdf {args.pdf}\n")

    # ------------------------------------------------------------------ M-01
    print("== M-01 snapshot contract ==")
    man = build_manifest("climate", pages, pdf_bytes, parser, CLEANING_NONE)
    mb = manifest_bytes(man)
    header = make_header(mb, man["snapshot_id"])
    snap = validate_binding(header, mb, {"climate": pages})
    d = man["docs"][0]
    doc_text = snap.doc_text("climate")
    texts = {"climate": doc_text}
    s53 = section(md06, "5.3 Corpus freezing")
    j = [json.loads(b) for b in code_blocks(s53, "json")]
    lock, docman = j[0], j[1]
    dm = docman["docs"][0]
    check("M-01", "06 §5.3 lock: pdf sha256/bytes/pages match the PDF",
          (lock["files"][0]["sha256"], lock["files"][0]["bytes"], lock["files"][0]["pages"])
          == (d["pdf_sha256"], d["bytes"], d["pages"]), f"{d['pdf_sha256'][:12]} {d['bytes']} B {d['pages']} pp")
    check("M-01", "06 §5.3 manifest has every required field",
          all(k in docman for k in ("snapshot_id", "corpus", "corpus_version", "created_utc", "parser", "cleaning",
                                    "encoding", "newline", "page_join", "docs"))
          and all(k in dm for k in ("doc_id", "pdf_sha256", "bytes", "pages", "doc_text_sha256", "page_table"))
          and docman["parser"]["call"] == "page.get_text()" and docman["page_join"] == "\n"
          and docman["cleaning"]["version"] == "none")
    check("M-01", "06 §5.3 manifest doc_text_sha256 / pdf_sha256 match recomputation",
          dm["doc_text_sha256"] == d["doc_text_sha256"] and dm["pdf_sha256"] == d["pdf_sha256"]
          and docman["parser"]["version"] == fitz.VersionBind, d["doc_text_sha256"][:16])
    check("M-01", "06 §5.3 page_table rows 1-3 match recomputation",
          dm["page_table"] == d["page_table"][:3],
          "; ".join(f"p{r['page']} [{r['doc_char_start']},{r['doc_char_end']})" for r in d["page_table"][:3]))
    m_total = re.search(r"whole document text is ([\d,]+) characters", s53)
    starts_txt = dict((int(p), int(v.replace(",", ""))) for p, v in re.findall(r"p\.(\d+) = ([\d,]+)", s53))
    check("M-01", "06 §5.3 doc_chars and p.8/10/23/29 starts match",
          m_total and int(m_total.group(1).replace(",", "")) == len(doc_text)
          and all(d["page_table"][p - 1]["doc_char_start"] == v for p, v in starts_txt.items()) and len(starts_txt) == 4,
          f"doc_chars={len(doc_text)} starts={starts_txt}")
    check("M-01", "real Corpus D manifest passes validate_binding (06 §5.3 recipe, exact-bytes digest)",
          isinstance(snap, Snapshot) and snap.snapshot_id == man["snapshot_id"],
          f"snapshot_id={snap.snapshot_id} (06 §5.3 recipe); manifest sha256={header['snapshot_manifest_sha256'][:16]}…")

    # ------------------------------------------------------------------ R-02 fail-closed binding
    print("\n== R-02 fail-closed binding and page-table integrity (06 §5.3 rule 4, §6.1) ==")
    check("R-02", "checker's required-field lists equal the 06 §5.3 manifest JSON keys",
          tuple(docman) == MANIFEST_REQUIRED and tuple(dm) == DOC_REQUIRED
          and all(tuple(r) == ROW_REQUIRED for r in dm["page_table"]) and tuple(docman["parser"]) == PARSER_REQUIRED,
          f"top={len(MANIFEST_REQUIRED)} doc={len(DOC_REQUIRED)} row={len(ROW_REQUIRED)}")
    check("R-02", "06 §5.3 recipe executed from the document == independent transcription (Corpus D + 2 toy inputs)",
          snapshot_id_06(parser, CLEANING_NONE, {"climate": d["doc_text_sha256"]})
          == snapshot_id_transcribed(parser, CLEANING_NONE, {"climate": d["doc_text_sha256"]})
          and snapshot_id_06(PARSER | {"version": "x"}, {"version": "c1"}, {"b": "2", "a": "1"})
          == snapshot_id_transcribed(PARSER | {"version": "x"}, {"version": "c1"}, {"a": "1", "b": "2"}),
          "recipe: " + " ".join(RECIPE_06.split())[:90] + "…")
    base_sid = snapshot_id_06(parser, CLEANING_NONE, {"climate": d["doc_text_sha256"]})
    variants = {"parser version": snapshot_id_06({**parser, "version": "0.0.0"}, CLEANING_NONE, {"climate": d["doc_text_sha256"]}),
                "options": snapshot_id_06({**parser, "options": {"sort": True}}, CLEANING_NONE, {"climate": d["doc_text_sha256"]}),
                "cleaning": snapshot_id_06(parser, {"version": "c1"}, {"climate": d["doc_text_sha256"]}),
                "doc text": snapshot_id_06(parser, CLEANING_NONE, {"climate": sha256_hex("x")})}
    check("R-02", "06 §5.3: parser version, options, cleaning version or doc text change => new snapshot_id",
          all(v != base_sid for v in variants.values()) and len(set(variants.values())) == 4,
          f"Corpus D snapshot_id = {base_sid}")
    check("R-02", "checker no longer uses a private snapshot serialization (old recipe id differs; M-04 sid() uses 06)",
          compute_snapshot_id({"climate": d["doc_text_sha256"]}, parser, CLEANING_NONE) == base_sid
          and sha256_hex("|".join([f"climate={d['doc_text_sha256']}", "parser=" + json.dumps(parser, sort_keys=True),
                                   "cleaning=" + json.dumps(CLEANING_NONE, sort_keys=True)]))[:12] != base_sid)

    # an item whose gold segment is INVALID on page 2: if a binding error is raised instead of ValueError,
    # the binding was validated before any gold label was translated
    bad_gold = {"qid": "FX-BAD", "split": "dev", "evidence_groups": [{"group_id": "g1", "fact": "fixture",
                "alternatives": [{"alt_id": "g1a", "segments": [{"doc_id": "climate", "page": 2, "char_start": 0,
                                                                "char_end": 10 ** 6}]}]}]}
    check("R-02", "control: with a valid binding the invalid gold segment raises ValueError (decoder bound)",
          raises(ValueError, load_dataset, [bad_gold], header, mb, {"climate": pages}, snap.snapshot_id)
          and not issubclass(BindingError, ValueError))
    wrong_digest = [dict(header, snapshot_manifest_sha256="deliberately-wrong"),
                    dict(header, snapshot_manifest_sha256=hashlib.sha256(mb + b" ").hexdigest()),
                    dict(header, snapshot_manifest_sha256=hashlib.sha256(manifest_bytes(man).replace(b"\n", b"\r\n")).hexdigest())]
    check("R-02", "wrong snapshot_manifest_sha256 rejected before gold translation (3 variants incl. CRLF re-save)",
          all(raises(BindingError, load_dataset, [bad_gold], h, mb, {"climate": pages}, snap.snapshot_id)
              for h in wrong_digest))
    reserialized = json.dumps(man, sort_keys=True).encode("utf-8")     # same JSON content, different bytes
    check("R-02", "digest is over the exact stored bytes: semantically equal re-serialized manifest is rejected",
          json.loads(reserialized) == man and raises(BindingError, validate_binding, header, reserialized, {"climate": pages}))
    miss_hdr = [k for k in HEADER_REQUIRED
                if not raises(BindingError, load_dataset, [bad_gold], {x: v for x, v in header.items() if x != k},
                              mb, {"climate": pages}, snap.snapshot_id)]
    check("R-02", "each missing dataset binding field rejected (snapshot_id, manifest sha256, scorer, evidence logic)",
          not miss_hdr, str(miss_hdr))
    miss_man = []
    for k in MANIFEST_REQUIRED:
        m2 = {x: v for x, v in man.items() if x != k}
        b2 = manifest_bytes(m2)
        if not raises(BindingError, validate_binding, make_header(b2, man["snapshot_id"]), b2, {"climate": pages}):
            miss_man.append(k)
    for k in DOC_REQUIRED + tuple("page_table." + r for r in ROW_REQUIRED):
        m2 = json.loads(mb)
        if k.startswith("page_table."):
            del m2["docs"][0]["page_table"][5][k.split(".", 1)[1]]
        else:
            del m2["docs"][0][k]
        b2 = manifest_bytes(m2)
        if not raises(BindingError, validate_binding, make_header(b2, man["snapshot_id"]), b2, {"climate": pages}):
            miss_man.append(k)
    for grp, keys in (("parser", PARSER_REQUIRED), ("cleaning", CLEANING_REQUIRED)):   # R2-01: nested fields
        for k in keys:
            m2 = json.loads(mb)
            del m2[grp][k]
            b2 = manifest_bytes(m2)                       # digest recomputed over the mutated bytes
            if not raises(BindingError, validate_binding, make_header(b2, man["snapshot_id"]), b2, {"climate": pages}):
                miss_man.append(f"{grp}.{k}")
    n_fields = len(MANIFEST_REQUIRED) + len(DOC_REQUIRED) + len(ROW_REQUIRED) + len(PARSER_REQUIRED) + len(CLEANING_REQUIRED)
    check("R-02", f"each missing manifest field rejected, nested parser/cleaning fields included ({n_fields} fields)",
          not miss_man, str(miss_man))
    m_steps = json.loads(mb); del m_steps["cleaning"]["steps"]; b_steps = manifest_bytes(m_steps)
    check("R2-01", "manifest without cleaning.steps (digest recomputed) raises BindingError before translation",
          raises(BindingError, load_dataset, [bad_gold], make_header(b_steps, man["snapshot_id"]), b_steps,
                 {"climate": pages}, snap.snapshot_id))
    check("R2-01", "valid manifest with cleaning {version: none, steps: []} still passes",
          man["cleaning"] == {"version": "none", "steps": []} and validate_binding(header, mb, {"climate": pages}) is not None)

    # toy ["abc","def"]: valid page-2 [0,1) -> doc [4,5) = "d"; page 2 shifted by +1 must be rejected
    toy_pages = ["abc", "def"]
    toy = build_manifest("toy", toy_pages, b"toy-pdf", parser, CLEANING_NONE, corpus="toy")
    toy_b = manifest_bytes(toy)
    toy_snap = validate_binding(make_header(toy_b, toy["snapshot_id"]), toy_b, {"toy": toy_pages})
    tg = toy_snap.gold_to_doc("toy", 2, 0, 1)
    check("R-02", 'valid ["abc","def"] page-2 [0,1) -> doc [4,5) = "d"',
          tg == (4, 5) and toy_snap.doc_text("toy")[4:5] == "d"
          and [(r["doc_char_start"], r["doc_char_end"]) for r in toy["docs"][0]["page_table"]] == [(0, 3), (4, 7)],
          f"doc {tg}")
    shifted = json.loads(toy_b)
    shifted["docs"][0]["page_table"][1]["doc_char_start"] += 1
    shifted["docs"][0]["page_table"][1]["doc_char_end"] += 1        # hash and length unchanged
    sh_b = manifest_bytes(shifted)
    sh_hdr = make_header(sh_b, toy["snapshot_id"])                  # digest matches the shifted bytes
    legacy_ok = not raises(SnapshotMismatch, legacy_verify_r1, shifted, {"toy": toy_pages})
    r2 = shifted["docs"][0]["page_table"][1]
    legacy_map = (r2["doc_char_start"] + 0, r2["doc_char_start"] + 1)
    check("R-02", "negative control: round-1 hash+length check accepts the shifted table and maps p2[0,1) to 'e'",
          legacy_ok and legacy_map == (5, 6) and "abc\ndef"[5:6] == "e", f"legacy map {legacy_map}")
    toy_item = {"qid": "T1", "split": "dev", "evidence_groups": [{"group_id": "g1", "fact": "d", "alternatives": [
        {"alt_id": "a", "segments": [{"doc_id": "toy", "page": 2, "char_start": 0, "char_end": 1}]}]}]}
    sh_err = ""
    try:
        load_dataset([toy_item], sh_hdr, sh_b, {"toy": toy_pages}, toy["snapshot_id"])
    except BindingError as e:
        sh_err = str(e)
    check("R-02", "page 2 start AND end shifted +1 (hash, length, digest consistent) is rejected by validate_binding",
          bool(sh_err), sh_err)
    ok_toy = load_dataset([toy_item], make_header(toy_b, toy["snapshot_id"]), toy_b, {"toy": toy_pages}, toy["snapshot_id"])
    check("R-02", "the same item on the valid table loads and maps to doc [4,5) = 'd'",
          ok_toy[0]["_groups_doc"] == [[[("toy", 4, 5)]]])

    def mutated(fn):
        m2 = json.loads(toy_b)
        fn(m2)
        b2 = manifest_bytes(m2)
        return raises(BindingError, validate_binding, make_header(b2, m2.get("snapshot_id", toy["snapshot_id"])),
                      b2, {"toy": toy_pages})
    struct = {
        "page numbers 1,3 (gap)": lambda m: m["docs"][0]["page_table"][1].update(page=3),
        "page order 2,1": lambda m: m["docs"][0]["page_table"].reverse(),
        "page_table[0].start = 1 (whole table shifted)": lambda m: [r.update(doc_char_start=r["doc_char_start"] + 1,
                                                                              doc_char_end=r["doc_char_end"] + 1)
                                                                     for r in m["docs"][0]["page_table"]],
        "page 2 end only +1 (length)": lambda m: m["docs"][0]["page_table"][1].update(doc_char_end=8),
        "page 1 text_sha256 wrong": lambda m: m["docs"][0]["page_table"][0].update(text_sha256=sha256_hex("abd")),
        "doc_text_sha256 wrong": lambda m: m["docs"][0].update(doc_text_sha256=sha256_hex("abcdef")),
        "manifest snapshot_id wrong": lambda m: m.update(snapshot_id="000000000000"),
        "pages field 3": lambda m: m["docs"][0].update(pages=3),
        "page_join ' ' (recipe fixes '\\n')": lambda m: m.update(page_join=" "),
    }
    not_rej = [k for k, fn in struct.items() if not mutated(fn)]
    check("R-02", f"structural / hash / id mutations rejected ({len(struct)} variants)", not not_rej, str(not_rej))
    check("R-02", "dataset snapshot_id != recomputed/manifest snapshot_id rejected",
          raises(BindingError, validate_binding, dict(make_header(toy_b, toy["snapshot_id"]), snapshot_id="000000000000"),
                 toy_b, {"toy": toy_pages}))
    check("R-02", "page texts that differ from the manifest (one page dropped) rejected",
          raises(BindingError, validate_binding, make_header(toy_b, toy["snapshot_id"]), toy_b, {"toy": ["abc"]}))
    check("R-02", "a Snapshot cannot be built without validate_binding",
          raises(BindingError, Snapshot, toy, {"toy": toy_pages}))

    # ------------------------------------------------------------------ R-05 two public decoders
    print("\n== R-05 gold_to_doc vs chunk_segment_to_doc (06 §2.3, §6.4; 07 H.3) ==")
    core, chunking, h3_tests = load_07_modules(md07)
    whole = chunking.chunk_document("toy", toy["snapshot_id"], toy_pages,
                                    chunking.ChunkerConfig(name="fixed", size=10, overlap=0, scope="cross_page"))
    wsegs = [(s.page, s.char_start, s.char_end) for s in whole[0].page_segments] if len(whole) == 1 else []
    check("R-05", '07 H.3 whole-document chunk of ["abc","def"] has page segments p1 [0,4), p2 [0,3)',
          wsegs == [(1, 0, 4), (2, 0, 3)], str(wsegs))
    check("R-05", "chunk_segment_to_doc accepts p1 [0,4) -> doc [0,4) and p2 [0,3) -> doc [4,7)",
          holds(lambda: toy_snap.chunk_segment_to_doc("toy", 1, 0, 4) == (0, 4)
                and toy_snap.chunk_segment_to_doc("toy", 2, 0, 3) == (4, 7)))
    check("R-05", "gold_to_doc rejects p1 [0,4) (virtual join) and accepts p1 [0,3) -> doc [0,3)",
          raises(ValueError, toy_snap.gold_to_doc, "toy", 1, 0, 4) and holds(lambda: toy_snap.gold_to_doc("toy", 1, 0, 3) == (0, 3)))
    check("R-05", "chunk decoder allows exactly one extra position, never on the last page; empty/negative rejected",
          raises(ValueError, toy_snap.chunk_segment_to_doc, "toy", 1, 0, 5)
          and raises(ValueError, toy_snap.chunk_segment_to_doc, "toy", 2, 0, 4)
          and raises(ValueError, toy_snap.gold_to_doc, "toy", 2, 1, 1)
          and raises(ValueError, toy_snap.gold_to_doc, "toy", 1, -1, 2)
          and raises(ValueError, toy_snap.gold_to_doc, "toy", 3, 0, 1)
          and holds(lambda: toy_snap.chunk_segment_to_doc("toy", 1, 3, 4) == (3, 4)))
    a, b = snap.gold_to_doc("climate", 10, 438, 537)
    check("M-01", "06 §9.6 D-002 p.10 [438,537) -> doc [20993,21092), same text (via gold_to_doc)",
          (a, b) == (20993, 21092) and doc_text[a:b] == pages[9][438:537], f"doc [{a},{b})")
    full, starts = core.join_pages(pages)
    check("R-05", "07 H.1 join_pages equals the validated snapshot (doc text and page starts)",
          full == doc_text and starts == [r["doc_char_start"] for r in snap.table["climate"]])
    rng = random.Random(0)
    ok, n_join, n_gold_ok = True, 0, 0
    for _ in range(2000):
        x = rng.randrange(0, len(doc_text) - 1)
        y = rng.randrange(x + 1, min(len(doc_text), x + 6000) + 1)
        segs = chunking.to_page_segments(x, y, starts, len(doc_text))      # 07 H.3 producer, as written
        try:
            back = [snap.chunk_segment_to_doc("climate", s.page, s.char_start, s.char_end) for s in segs]
        except ValueError:
            ok = False
            continue
        ok &= back[0][0] == x and back[-1][1] == y and all(p[1] == q[0] for p, q in zip(back, back[1:]))
        ok &= "".join(doc_text[p:q] for p, q in back) == doc_text[x:y]
        for s in segs:
            try:
                ok &= snap.gold_to_doc("climate", s.page, s.char_start, s.char_end) == \
                    snap.chunk_segment_to_doc("climate", s.page, s.char_start, s.char_end)
                n_gold_ok += 1
            except ValueError:
                n_join += 1
                ok &= s.char_end == len(pages[s.page - 1]) + 1           # only the virtual join is refused
    check("R-05", "2000 random doc spans -> 07 to_page_segments -> chunk_segment_to_doc round-trip exactly; gold "
          "decoder agrees wherever it applies and refuses only segments ending on the virtual join",
          ok, f"{n_gold_ok} segments accepted by both; {n_join} include the join (gold refuses)")
    ok_real, n_real = True, 0
    for scope in ("per_page", "cross_page"):
        for c in chunking.chunk_document("climate", snap.snapshot_id, pages,
                                         chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope=scope)):
            try:
                back = [snap.chunk_segment_to_doc("climate", s.page, s.char_start, s.char_end) for s in c.page_segments]
            except ValueError:
                ok_real = False
                continue
            ok_real &= back[0][0] == c.char_start and back[-1][1] == c.char_end and \
                all(p[1] == q[0] for p, q in zip(back, back[1:]))
            n_real += 1
    check("R-05", "every real Corpus D chunk (recursive 1000/200, both scopes) decodes back through chunk_segment_to_doc",
          ok_real, f"{n_real} chunks")
    r05_txt = [("06 §2.3", section(md06, "2.3 Provider-agnostic")), ("06 §6.4", section(md06, "6.4 Span-level")),
               ("07 H.3", section(md07, "H.3 Reusable design"))]
    r05_bad = [n for n, t in r05_txt if not all(k in t for k in ("gold_to_doc", "chunk_segment_to_doc"))]
    r05_bad += [n for n, t in r05_txt[:1] + r05_txt[2:] if "[0,4)" not in t or "[0,3)" not in t]
    check("R-05", "rule stated in 06 §2.3, §6.4 and 07 H.3 (both decoders named; [0,4)/[0,3) example in §2.3 and H.3)",
          not r05_bad, str(r05_bad))

    # 07 H.3 chunker exactly as written
    t06 = ast.parse(code_blocks(section(md06, "2.3 Provider-agnostic"), "python")[0])
    t07 = ast.parse(code_blocks(section(md07, "H.3 Reusable design"), "python")[0])

    def fields(tree, cls):
        for n in tree.body:
            if isinstance(n, ast.ClassDef) and n.name == cls:
                return [s.target.id for s in n.body if isinstance(s, ast.AnnAssign)]
    f06, f07 = fields(t06, "Chunk"), fields(t07, "DocChunk")
    check("M-01", "06 §2.3 Chunk fields == 07 H.3 DocChunk fields (+ meta in 06)",
          [f for f in f06 if f != "meta"] == f07, ",".join(f07))
    check("M-01", "06 §2.3 PageSegment == 07 H.3 PageSegment",
          fields(t06, "PageSegment") == fields(t07, "PageSegment"))

    # fixtures: page-2 span; cross-page pp.12-13 span (two consecutive segments forming ONE alternative)
    e12 = len(pages[11].rstrip())
    s13 = len(pages[12]) - len(pages[12].lstrip())
    p2_item = {"qid": "FX-P2", "split": "dev", "evidence_groups": [{"group_id": "g1", "fact": "fixture",
               "alternatives": [{"alt_id": "g1a", "segments": [{"doc_id": "climate", "page": 2, "char_start": 746, "char_end": 836}]}]}]}
    x_item = {"qid": "FX-P12-13", "split": "dev", "evidence_groups": [{"group_id": "g1", "fact": "fixture",
              "alternatives": [{"alt_id": "g1a", "segments": [
                  {"doc_id": "climate", "page": 12, "char_start": e12 - 80, "char_end": e12},
                  {"doc_id": "climate", "page": 13, "char_start": s13, "char_end": s13 + 60}]}]}]}
    fx = load_dataset([p2_item, x_item], header, mb, {"climate": pages}, snap.snapshot_id)
    same = True
    detail = []
    for name in ("recursive", "fixed"):
        runs = {}
        for scope in ("per_page", "cross_page"):
            cfg = chunking.ChunkerConfig(name=name, size=1000, overlap=200, scope=scope)
            chs = chunking.chunk_document("climate", snap.snapshot_id, pages, cfg)
            assert all(doc_text[c.char_start:c.char_end] == c.text for c in chs)
            runs[scope] = [("climate", c.char_start, c.char_end) for c in chs]
        for it in fx:
            G = it["_groups_doc"]
            sc = {}
            for scope, chs in runs.items():
                retrieved = [c for c in chs if rel(c, G, texts)]            # oracle retrieval of the evidence
                sc[scope] = (ce(G, retrieved, texts), group_recall(G, retrieved, texts),
                             round(span_coverage(G, retrieved, texts), 6), int(bool(retrieved)),
                             ce(G, [], texts))
            same &= sc["per_page"] == sc["cross_page"] and sc["per_page"][0] == 1
            detail.append(f"{name}/{it['qid']}: per_page={sc['per_page'][:3]} cross_page={sc['cross_page'][:3]}")
    check("M-01", "page-2 and pp.12-13 spans score identically under per-page and cross-page chunks",
          same, " | ".join(detail))
    # negative control: skipping the conversion (page offsets used as document offsets) changes the score
    naive = [[[("climate", 746, 836)]]]
    per_page = [("climate", c.char_start, c.char_end) for c in chunking.chunk_document(
        "climate", snap.snapshot_id, pages, chunking.ChunkerConfig(name="recursive", size=1000, overlap=200))]
    ret = [c for c in per_page if rel(c, fx[0]["_groups_doc"], texts)]
    check("M-01", "negative control: unconverted page offsets give a different CE (conversion matters)",
          ce(naive, ret, texts) != ce(fx[0]["_groups_doc"], ret, texts))
    # fail closed
    tampered = list(pages)
    tampered[4] = tampered[4].replace("the", "teh", 1)
    check("M-01", "tampered page-5 text hash stops scoring (SnapshotMismatch)",
          raises(SnapshotMismatch, load_dataset, [p2_item], header, mb, {"climate": tampered}, snap.snapshot_id))
    cleaned = [norm_ws(p) for p in pages]
    man2 = build_manifest("climate", cleaned, pdf_bytes, parser, {"version": "c1", "steps": ["collapse_whitespace"]})
    mb2 = manifest_bytes(man2)
    # dataset labelled against snapshot 1; the stored manifest/text are now snapshot 2 (extraction change):
    # refused whether the header keeps its old digest or (mis)copies the new digest with the old snapshot_id
    check("M-01", "dataset bound to another snapshot_id is refused (extraction change cannot reuse gold)",
          man2["snapshot_id"] != man["snapshot_id"]
          and raises(SnapshotMismatch, load_dataset, [p2_item], header, mb2, {"climate": cleaned}, man2["snapshot_id"])
          and raises(SnapshotMismatch, load_dataset, [p2_item], dict(header, snapshot_manifest_sha256=hashlib.sha256(mb2).hexdigest()),
                     mb2, {"climate": cleaned}, man2["snapshot_id"])
          and raises(SnapshotMismatch, load_dataset, [p2_item], header, mb, {"climate": pages}, "000000000000"),
          f"{man['snapshot_id']} vs {man2['snapshot_id']}")
    s61 = section(md06, "6.1 Schema")
    check("M-01", "06 §6.1 dataset header names snapshot_id, snapshot_manifest_sha256, scorer_version",
          all(k in s61 for k in ("`snapshot_id`", "`snapshot_manifest_sha256`", "`scorer_version`",
                                  "`evidence_logic_version`")))

    # ------------------------------------------------------------------ M-02 / M-03 seeds
    print("\n== M-02 evidence groups / CE@k (seed items from 06 §6.7) ==")
    s67 = section(md06, "6.7 Draft seed items")
    seeds = [json.loads(ln) for ln in code_blocks(s67, "jsonl")[0].splitlines() if ln.strip()]
    check("M-02", "06 §6.7 JSONL parses: 10 seeds D-001..D-010", [s["qid"] for s in seeds]
          == [f"D-{i:03d}" for i in range(1, 11)])
    req = ("qid", "question", "category", "answerable", "gold_answer", "evidence_groups", "difficulty",
           "created_by", "split", "group", "notes")
    bad = [s["qid"] for s in seeds if any(k not in s for k in req) or "gold_evidence" in s or "evidence_mode" in s]
    check("M-02", "every seed has the required fields and no gold_evidence/evidence_mode", not bad, str(bad))
    shape = {s["qid"]: [len(g["alternatives"]) for g in s["evidence_groups"]] for s in seeds}
    want = {"D-001": [1], "D-002": [1], "D-003": [1], "D-004": [2], "D-005": [1, 1], "D-006": [1, 1],
            "D-007": [1, 1], "D-008": [1], "D-009": [], "D-010": []}
    check("M-02", "group/alternative shapes match the M-03 conversion", shape == want, str(shape))
    check("M-02", "unanswerables have evidence_groups [] and answerables do not",
          all((s["evidence_groups"] == []) == (not s["answerable"]) for s in seeds))
    check("M-03", "all seeds llm-draft, split 'unassigned', group == qid",
          all(s["created_by"] == "llm-draft" and s["split"] == "unassigned" and s["group"] == s["qid"] for s in seeds))
    qbad = []
    for s in seeds:
        for g in s["evidence_groups"]:
            for alt in g["alternatives"]:
                seg = alt["segments"][0]
                pt = pages[seg["page"] - 1]
                span = norm_ws(pt[seg["char_start"]:seg["char_end"]])
                q = norm_ws(alt["quote"])
                n_on_page = norm_ws(pt).count(q)
                other = [i + 1 for i, p in enumerate(pages) if i + 1 != seg["page"] and q in norm_ws(p)]
                if not (span.startswith(q) and len(q.split()) <= 25 and n_on_page == 1 and not other):
                    qbad.append((s["qid"], alt["alt_id"], span[:40], n_on_page, other))
    check("M-02", "every quote is a prefix of/equal to its normalized span, <= 25 words, once on its page, "
          "on no other page", not qbad, str(qbad))
    spans = {(s["qid"], alt["alt_id"]): (alt["segments"][0]["page"], alt["segments"][0]["char_start"],
                                         alt["segments"][0]["char_end"])
             for s in seeds for g in s["evidence_groups"] for alt in g["alternatives"]}
    check("M-03", "D-004 p.23 [1437,1566); D-007 p.10 [137,339) and p.29 [963,1106)",
          spans[("D-004", "g1b")] == (23, 1437, 1566) and spans[("D-007", "g1a")] == (10, 137, 339)
          and spans[("D-007", "g2a")] == (29, 963, 1106)
          and norm_ws(pages[22][1437:1566]).startswith("Direct Air Capture (DAC)")
          and norm_ws(pages[9][137:339]).startswith("The UNFCCC is")
          and norm_ws(pages[28][963:1106]).endswith("on Climate Change (UNFCCC)."))
    tbl_bad = []
    for s in seeds:
        row = next(ln for ln in s67.splitlines() if ln.startswith(f"| {s['qid']} "))
        for g in s["evidence_groups"]:
            for alt in g["alternatives"]:
                if norm_ws(alt["quote"]) not in norm_ws(row.replace('\\"', '"')):
                    tbl_bad.append((s["qid"], alt["alt_id"]))
    check("M-02", "06 §6.7 table quotes equal the JSONL quotes", not tbl_bad, str(tbl_bad))
    ex = json.loads(code_blocks(s61, "json")[0])
    d002 = next(s for s in seeds if s["qid"] == "D-002")
    check("M-02", "06 §6.1 D-002 example uses evidence_groups identical to the seed",
          ex["evidence_groups"] == d002["evidence_groups"])

    loaded = {it["qid"]: it for it in load_dataset(seeds, header, mb, {"climate": pages}, snap.snapshot_id, scored=False)}
    check("M-01", "scored run rejects the seeds' split 'unassigned'",
          raises(ValueError, load_dataset, seeds, header, mb, {"climate": pages}, snap.snapshot_id, scored=True))
    P2, P8, P23 = (snap.table["climate"][p - 1]["doc_char_start"] for p in (2, 8, 23))
    check("M-02", "06 §9.6 constants P2, P8, P23 equal the page_table", (P2, P8, P23) == (2425, 16074, 49209))
    G5 = loaded["D-005"]["_groups_doc"]
    frag = [("climate", P2 + 0, P2 + 23), ("climate", P2 + 746, P2 + 791)]
    check("M-02", "fragment texts are the Codex counterexample",
          doc_text[P2:P2 + 23] == "Coal is the most carbon"
          and doc_text[P2 + 746:P2 + 791] == "Natural gas is the least carbon-intensive fos")
    check("M-02", "D-005 half-span fragments => CE 0", ce(G5, frag, texts) == 0,
          f"CE={ce(G5, frag, texts)} GR={group_recall(G5, frag, texts)} SC={span_coverage(G5, frag, texts):.3f} "
          f"Hit={max(rel(c, G5, texts) for c in frag)}")
    one = [("climate", P2 + 0, P2 + 45)]
    check("M-02", "D-005 with only one of two groups => CE 0 (Group-Recall 0.5)",
          ce(G5, one, texts) == 0 and group_recall(G5, one, texts) == 0.5)
    G4 = loaded["D-004"]["_groups_doc"]
    check("M-02", "D-004 with either alternative => CE 1",
          ce(G4, [("climate", P8 + 1900, P8 + 2100)], texts) == 1
          and ce(G4, [("climate", P23 + 1400, P23 + 1600)], texts) == 1
          and ce(G4, [("climate", P23 + 1463, P23 + 1600)], texts) == 0)   # the old, insufficient p.23 start
    a5, b5 = P2 + 746, P2 + 836
    joint = [("climate", a5 - 10, a5 + 40), ("climate", a5 + 40, b5 + 5)]
    check("M-02", "span covered jointly by two chunks => CE 1",
          ce([G5[1]], joint, texts) == 1 and ce([G5[1]], joint[:1], texts) == 0)
    G7 = loaded["D-007"]["_groups_doc"]
    check("M-02", "D-007 multi-hop: both pages => CE 1; p.29 alone => CE 0",
          ce(G7, [("climate", g[0][0][1], g[0][0][2]) for g in G7], texts) == 1
          and ce(G7, [G7[1][0][0]], texts) == 0)
    # execute the 06 §9.6 sketch's own test functions against this reference implementation
    s96 = code_blocks(section(md06, "9.6 Regression set"), "python")[0]

    class NText(str):
        def count_normalized(self, q):
            return norm_ws(self).count(norm_ws(q))

    class SnapShim:
        def page_text(self, doc_id, page):
            return NText(snap.page_text(doc_id, page))

        def to_doc(self, *a):
            return snap.gold_to_doc(*a)          # 06 §6.4: the sketch's to_doc is the gold decoder

        def doc_text(self, doc_id):
            return snap.doc_text(doc_id)

    ns = {"complete_evidence": complete_evidence, "P2": P2, "P8": P8, "P23": P23}
    exec(compile(ast_functions(s96, {"test_sufficiency_contract", "test_page_to_doc_conversion",
                                     "test_gold_quotes_resolve"}), "06_96", "exec"), ns)
    for fn, argv in (("test_sufficiency_contract", (doc_text,)), ("test_page_to_doc_conversion", (SnapShim(),)),
                     ("test_gold_quotes_resolve", (seeds, SnapShim()))):
        try:
            ns[fn](*argv)
            check("M-02", f"06 §9.6 sketch {fn}() passes on the reference implementation", True)
        except AssertionError as e:
            check("M-02", f"06 §9.6 sketch {fn}() passes on the reference implementation", False, repr(e))
    # 06 §7.3 toy example: G1 inside c3, G2 inside c7; ranking [c5, c3, c9, c7, c1]
    toyt = {"t": "x" * 1000}
    C = {i: ("t", (i - 1) * 100, i * 100) for i in range(1, 10)}
    TG = [[[("t", 210, 260)]], [[("t", 620, 680)]]]
    R = [C[5], C[3], C[9], C[7], C[1]]
    rels = [rel(c, TG, toyt) for c in R]
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels))
    idcg = 1 + 1 / math.log2(3)
    gdcg = (2 ** 2 - 1) / math.log2(3) + (2 ** 1 - 1) / math.log2(5)
    gidcg = 3 + 1 / math.log2(3)
    cp5 = sum(sum(rels[:i + 1]) / (i + 1) * rels[i] for i in range(5)) / sum(rels)
    toy = (ce(TG, R[:3], toyt), ce(TG, R[:5], toyt), group_recall(TG, R[:3], toyt), group_recall(TG, R[:5], toyt),
           span_coverage(TG, R[:3], toyt), span_coverage(TG, R[:5], toyt), max(rels[:1]), max(rels[:3]),
           round(sum(rels[:3]) / 3, 3), round(sum(rels[:5]) / 5, 3), 1 / (rels.index(1) + 1),
           round(dcg / idcg, 3), round(gdcg / gidcg, 3), cp5)
    check("M-02", "06 §7.3 toy: CE@3/5=0/1, GR 0.5/1.0, SC 0.5/1.0, Hit@1/3=0/1, P 0.333/0.4, RR 0.5, "
          "nDCG 0.651/0.640, CP@5 0.5", toy == (0, 1, 0.5, 1.0, 0.5, 1.0, 0, 1, 0.333, 0.4, 0.5, 0.651, 0.64, 0.5),
          str(toy))
    s72 = section(md06, "7.2 Relevance from spans")
    s24 = section(md06, "2.4 Configuration")
    cfg_line = 'scoring: {scorer_version: "s1", chunk_relevance: "any_overlap", sufficiency: "complete_evidence", tolerance: "whitespace-only"}'
    y24 = code_blocks(s24, "yaml")[0]
    check("M-02", "06 §2.4 YAML and §7.2 carry the same scoring config; no min_span_coverage/relevance_rule in the YAML",
          cfg_line in y24 and cfg_line in s72 and "relevance_rule" not in y24 and "min_span_coverage" not in y24)

    # ------------------------------------------------------------------ M-04
    print("\n== M-04 content identity / cache keys (07 H.3 code as written) ==")
    EMB = dict(provider="cohere", model_id="embed-model", model_revision="r1", input_type="search_document",
               preprocessing_version="p1")
    k_doc = chunking.embedding_cache_key("hello|world", **EMB)
    check("M-04", "07 embedding_cache_key == reference sha256(provider|model_id|revision|input_type|preproc|text)",
          k_doc == ref_embedding_cache_key("hello|world", **EMB))
    cfg = chunking.ChunkerConfig(name="fixed", size=40, overlap=10)
    check("M-04", "params_hash of fixed 40/10 is the Codex counterexample's c5c8dfd3d707",
          cfg.params_hash() == "c5c8dfd3d707")

    def sid(pgs):
        return compute_snapshot_id({"doc1": sha256_hex("\n".join(pgs))}, parser, CLEANING_NONE)
    A = chunking.chunk_document("doc1", sid(["AAAA"]), ["AAAA"], cfg)[0]
    A2 = chunking.chunk_document("doc1", sid(["AAAA"]), ["AAAA"], cfg)[0]
    B = chunking.chunk_document("doc1", sid(["BBBB"]), ["BBBB"], cfg)[0]
    check("M-04", "same content + config => same chunk_id and same cache key",
          A.chunk_id == A2.chunk_id and chunking.embedding_cache_key(A.text, **EMB)
          == chunking.embedding_cache_key(A2.text, **EMB))
    check("M-04", "changed text => different snapshot_id, chunk_id, text_sha256 and cache key",
          A.snapshot_id != B.snapshot_id and A.chunk_id != B.chunk_id and A.text_sha256 != B.text_sha256
          and chunking.embedding_cache_key(A.text, **EMB) != chunking.embedding_cache_key(B.text, **EMB),
          f"{A.chunk_id} vs {B.chunk_id}")
    stale = chunking.chunk_document("doc1", A.snapshot_id, ["BBBB"], cfg)[0]
    check("M-04", "stale snapshot_id reused: id collides but cache key still follows the text",
          stale.chunk_id == A.chunk_id and chunking.embedding_cache_key(stale.text, **EMB)
          != chunking.embedding_cache_key(A.text, **EMB))
    check("M-04", "query vs document input_type => different keys",
          chunking.embedding_cache_key("q", **EMB) != chunking.embedding_cache_key("q", **{**EMB, "input_type": "search_query"}))
    real = chunking.chunk_document("climate", snap.snapshot_id, pages, chunking.ChunkerConfig(name="recursive", size=1000, overlap=200))
    tam = chunking.chunk_document("climate", "tampered0000", tampered, chunking.ChunkerConfig(name="recursive", size=1000, overlap=200))
    fmt = re.compile(r"^climate:[0-9a-f]{12}:[0-9a-f]{12}:\d{5}$")
    check("M-04", "real-PDF chunk ids follow doc_id:snapshot_id:params_hash:seq and differ across snapshots",
          all(fmt.match(c.chunk_id) for c in real) and {c.chunk_id for c in real}.isdisjoint({c.chunk_id for c in tam}),
          f"{len(real)} chunks, e.g. {real[0].chunk_id}")
    snapfn = ast_functions(h3_tests, {"snap"})
    ns7 = {"sha256_hex": sha256_hex}
    exec(snapfn, ns7)
    claimed = ("doc1:65232ca1fd98:c5c8dfd3d707:00000", "doc1:656cee243439:c5c8dfd3d707:00000")
    got = (chunking.chunk_document("doc1", ns7["snap"](["AAAA"]), ["AAAA"], cfg)[0].chunk_id,
           chunking.chunk_document("doc1", ns7["snap"](["BBBB"]), ["BBBB"], cfg)[0].chunk_id)
    check("M-04", "07 H.3 quoted ids (with its stand-in snap()) reproduce", got == claimed, str(got))
    s23 = section(md06, "2.3 Provider-agnostic")
    check("M-04", "06 §2.3 chunk_id comment and §2.4 cache comment match the contract",
          'f"{doc_id}:{snapshot_id}:{params_hash}:{seq:05d}"' in s23 and "never a cache key" in s23
          and "sha256(provider|model_id|revision|input_type|preproc_version|text)" in s24)

    # ------------------------------------------------------------------ M-05
    print("\n== M-05 paired comparisons / splits ==")
    rngv = random.Random(1)
    qids = [f"Q{i:02d}" for i in range(40)]
    base = {q: float(rngv.random() < 0.6) for q in qids}
    cand = {q: float(rngv.random() < 0.7) for q in qids}
    shuffled = dict(sorted(cand.items(), key=lambda kv: rngv.random()))
    r1 = ref_paired_bootstrap(base, cand)
    r2 = ref_paired_bootstrap(base, shuffled)
    check("M-05", "reference: shuffled candidate order gives the identical result", r1 == r2, str(r1))
    missing = dict(cand)
    missing.pop("Q07")
    check("M-05", "reference: mismatched qid sets raise", raises(ValueError, ref_paired_bootstrap, base, missing))
    # cluster bootstrap: base (+1) and paraphrase (-1) share a group, all else 0 => every resample mean is 0
    a0 = {q: 0.0 for q in ("B1", "B1-P1", "B2", "B3", "B4")}
    b0 = {"B1": 1.0, "B1-P1": -1.0, "B2": 0.0, "B3": 0.0, "B4": 0.0}
    grp = {"B1": "B1", "B1-P1": "B1", "B2": "B2", "B3": "B3", "B4": "B4"}
    tr: list = []
    m, ci = ref_paired_bootstrap(a0, b0, grp, n_boot=500, _trace=tr)
    together = all(q.count("B1") == q.count("B1-P1") for q in tr)
    check("M-05", "reference cluster bootstrap resamples base+paraphrase together (CI exactly [0, 0])",
          together and ci == (0.0, 0.0))
    s93 = code_blocks(section(md06, "9.3 Paired comparison"), "python")[0]
    try:
        import numpy as np
        nsb: dict = {}
        exec(compile(s93, "06_93", "exec"), nsb)
        pb = nsb["paired_bootstrap"]
        d1, c1 = pb(base, cand)
        d2, c2 = pb(base, shuffled)
        check("M-05", "06 §9.3 sketch: shuffled order identical; mean equals reference",
              d1 == d2 and np.array_equal(c1, c2) and abs(d1 - r1[0]) < 1e-12, f"diff={d1:.4f} CI={np.round(c1, 3)}")
        check("M-05", "06 §9.3 sketch: mismatched qid sets raise", raises(ValueError, pb, base, missing))
        _, cz = pb(a0, b0, grp, n_boot=2000)
        _, cu = pb(a0, b0, None, n_boot=2000)
        check("M-05", "06 §9.3 sketch: group resampling keeps base+paraphrase together",
              float(cz[0]) == 0.0 == float(cz[1]) and (float(cu[0]) < 0 < float(cu[1])),
              f"grouped CI={cz.tolist()} ungrouped CI={np.round(cu, 3).tolist()}")
        info(f"numpy {np.__version__} used to execute the 06 §9.3 sketch")
    except ImportError:
        info("numpy not installed: 06 §9.3 numpy sketch not executed (reference version still checked)")
    items = [dict(s) for s in seeds] + [{"qid": "D-002-P1", "group": "D-002", "category": "factual-single-span"}]
    for i in range(30):                                   # synthetic extra groups so every split is populated
        items.append({"qid": f"S-{i:02d}", "group": f"S-{i:02d}", "category": ["factual-single-span", "multi-span"][i % 2]})
        if i % 3 == 0:
            items.append({"qid": f"S-{i:02d}-P1", "group": f"S-{i:02d}", "category": "factual-single-span"})
    okg = True
    for sd in range(50):
        sp = assign_splits(items, seed=sd)
        okg &= all(sp[it["qid"]] == sp[it["group"]] for it in items)
    check("M-05", "group-level split keeps base and paraphrase in the same split (50 seeds)", okg)
    s67p = re.search(r"`D-002-P1`.*?`paraphrase_of: \"D-002\"`, `group: \"D-002\"`", s67)
    check("M-05", "06 §6.7 paraphrase example shares its base item's group", bool(s67p))
    run_a = {"dataset_sha256": "h1", "snapshot_id": snap.snapshot_id, "qids": tuple(qids), "labels_sha256": "l",
             "split": "dev", "scorer_version": "s1"}
    check("M-05", "comparison keys: identical accepted; any differing key (hash, scorer) rejected",
          comparison_keys_match(run_a, dict(run_a))
          and raises(ValueError, comparison_keys_match, run_a, {**run_a, "dataset_sha256": "h2"})
          and raises(ValueError, comparison_keys_match, run_a, {**run_a, "scorer_version": "s2"}))

    # ------------------------------------------------------------------ R-07
    print("\n== R-07 order-insensitive qid metadata (06 §9.2/§9.3) ==")
    keys = dict(dataset_sha256="h1", snapshot_id=snap.snapshot_id, labels_sha256="l", split="dev", scorer_version="s1")
    shuffled_q = list(qids)
    random.Random(7).shuffle(shuffled_q)
    ma = make_comparison_meta(qids=qids, **keys)
    mb_ = make_comparison_meta(qids=shuffled_q, **keys)
    check("R-07", "construction stores qids as a canonical sorted list (shuffled input -> identical metadata)",
          shuffled_q != sorted(qids) and ma["qids"] == sorted(qids) and mb_ == ma)
    check("R-07", "identical metadata with qids in a different order is accepted (Codex probe q1,q2 vs q2,q1)",
          holds(lambda: comparison_keys_match(ma, mb_)
                and comparison_keys_match({**run_a, "qids": ("q1", "q2")}, {**run_a, "qids": ("q2", "q1")})))
    check("R-07", "different qid sets are rejected (one missing, one extra, one swapped)",
          raises(ValueError, comparison_keys_match, ma, make_comparison_meta(qids=qids[:-1], **keys))
          and raises(ValueError, comparison_keys_match, ma, make_comparison_meta(qids=qids + ["Q99"], **keys))
          and raises(ValueError, comparison_keys_match, ma, make_comparison_meta(qids=qids[:-1] + ["Q99"], **keys))
          and raises(ValueError, comparison_keys_match, ma, {**ma, "split": "test"}))
    check("R-07", "duplicate qids and missing comparison keys are rejected at construction",
          raises(ValueError, make_comparison_meta, qids=qids + [qids[0]], **keys)
          and raises(ValueError, make_comparison_meta, qids=qids, **{k: v for k, v in keys.items() if k != "split"}))
    s93t = section(md06, "9.3 Paired comparison")
    check("R-07", "06 §9.3 states canonical sorted qids, compared as sets",
          "canonical sorted list" in s93t and "as **sets**" in s93t and "qid set" in section(md06, "9.2 Controls"))

    # ------------------------------------------------------------------ M-06
    print("\n== M-06 interval numbers ==")
    wl, wh = wilson(8, 10)
    cp = clopper_pearson_lower(6, 6)
    print(f"Wilson 95% for 8/10: [{wl:.4f}, {wh:.4f}]   exact two-sided 95% lower bound for 6/6: {cp:.4f} "
          f"(closed form 0.025**(1/6) = {0.025 ** (1 / 6):.4f})")
    s84 = section(md06, "8.4 Calibration")
    mw = re.search(r"Wilson 95% CI is about (0\.\d+)–(0\.\d+)", s84)
    mc = re.search(r"lower bound of about (0\.\d+)", s84)
    check("M-06", "06 §8.4 Wilson 8/10 ~ 0.49–0.94", mw and (float(mw.group(1)), float(mw.group(2)))
          == (round(wl, 2), round(wh, 2)), mw.group(0) if mw else "not found")
    check("M-06", "06 §8.4 exact lower bound 6/6 ~ 0.54", mc and float(mc.group(1)) == round(cp, 2),
          mc.group(0) if mc else "not found")
    check("M-06", "06 §6.2 repeats 0.54", "lower bound of only about 0.54" in section(md06, "6.2 Categories"))

    # ------------------------------------------------------------------ R-03
    print("\n== R-03 interval methods by statistic (06 §8.4) ==")
    h_lab, j_lab = [1, 1, 0, 0], [0, 0, 1, 1]          # 4 balanced items, the two raters always disagree
    po = sum(a == b for a, b in zip(h_lab, j_lab)) / 4
    pe = 0.5 * 0.5 + 0.5 * 0.5
    kap = cohens_kappa(h_lab, j_lab)
    check("R-03", "κ example: p_o = 0, p_e = 0.5, κ = (0 − 0.5)/(1 − 0.5) = −1", po == 0 and pe == 0.5 and kap == -1.0,
          f"κ={kap}")
    k0, (klo, khi), k_undef = kappa_bootstrap(h_lab, j_lab, n_boot=2000, seed=0)
    check("R-03", "paired bootstrap (seed 0, 2000 resamples) gives a valid κ interval inside [−1, 1]",
          k0 == -1.0 and -1.0 <= klo <= khi <= 1.0, f"κ={k0} 95% CI [{klo:.3f}, {khi:.3f}], undefined resamples={k_undef}")
    wl0, wh0 = wilson(0, 4)                            # what a Wilson-on-κ misuse would report (agreements 0/4)
    check("R-03", "a Wilson interval cannot represent κ = −1 (it lives in [0, 1])",
          0.0 <= wl0 <= wh0 <= 1.0 and not (wl0 <= kap <= wh0), f"Wilson(0/4)=[{wl0:.3f}, {wh0:.3f}]")
    cl_h = [1, 0, 1, 1, 0, 0, 1, 0]
    cl_j = [1, 0, 0, 1, 0, 1, 1, 0]
    cl_a = ["a1", "a1", "a2", "a2", "a3", "a3", "a4", "a4"]   # claims of the same answer share a cluster
    trk: list = []
    kc, (clo, chi), _ = kappa_bootstrap(cl_h, cl_j, clusters=cl_a, n_boot=500, seed=1, _trace=trk)
    ku, ku_ci, ku_undef = kappa_bootstrap([1] * 60, [1] * 60, n_boot=2000, seed=0)   # R2-02 reproduction
    check("R2-02", "constant identical labels: kappa undefined -> explicit (None, None, n_undefined), no IndexError",
          ku is None and ku_ci is None and ku_undef == 2000, f"point={ku} ci={ku_ci} undefined={ku_undef}")
    check("R-03", "cluster bootstrap over answers resamples all units of an answer together",
          all(sum(1 for u in us if cl_a[u] == g) % 2 == 0 for us in trk for g in set(cl_a)) and -1 <= clo <= chi <= 1,
          f"κ={kc:.3f} CI [{clo:.3f}, {chi:.3f}]")
    body84 = "\n".join(ln for ln in s84.splitlines() if not ln.lstrip().startswith("> Revised"))
    cm_line = next((ln for ln in body84.splitlines() if "**Confusion matrix:**" in ln), "")
    k_line = next((ln for ln in body84.splitlines() if "**Cohen's κ**" in ln), "")
    rate_line = next((ln for ln in body84.splitlines() if "**Binomial rates**" in ln), "")
    check("R-03", "06 §8.4: confusion matrix reported as raw counts with no interval (no Wilson)",
          "counts" in cm_line and "no interval" in cm_line and "Wilson" not in cm_line, cm_line.strip()[:90])
    check("R-03", "06 §8.4: κ is not a proportion, Wilson does not apply; paired bootstrap or κ variance; −1 example",
          all(x in k_line for x in ("not** a proportion", "Wilson does not apply", "paired bootstrap", "cohens_kappa",
                                    "p_o = 0", "p_e = 0.5", "**−1**")))
    check("R-03", "06 §8.4: Wilson only for binomial rates; cluster bootstrap over answers for clustered units",
          "Wilson 95% interval" in rate_line and "cluster bootstrap over answers" in rate_line
          and "independent" in rate_line)
    m_rule = re.search(r"\*\*Decision rule \(Assumption[^)]*\)\.\*\*.*?\*\*lower 95% bound\*\* of failure-class recall "
                       r"is \*\*≥ (0\.\d+)\*\* and the \*\*lower 95% bound\*\* of κ is \*\*≥ (0\.\d+)\*\*", body84)
    check("R-03", "06 §8.4 states the lower-bound decision rule (Assumption): recall LB ≥ 0.70 and κ LB ≥ 0.40",
          bool(m_rule) and m_rule.groups() == ("0.70", "0.40") and "aspirational" in body84,
          m_rule.group(0)[-90:] if m_rule else "not found")

    def wilson_kappa_violations(text: str) -> list[str]:
        neg = re.compile(r"never Wilson|not Wilson|Wilson does not apply|meaningless|Wilson only for", re.I)
        out = []
        for ln in text.splitlines():
            if ln.lstrip().startswith("> Revised"):          # revision history describes the old rule
                continue
            for seg in re.split(r"[;—,]\s|\.\s", ln):
                if "Wilson" in seg and not neg.search(seg) and (re.search(r"κ|kappa", seg) or
                                                                 re.search(r"confusion matri", seg, re.I)):
                    out.append(seg.strip()[:80])
        return out
    synthetic = ["- the confusion matrix, Cohen's κ and failure-class recall should each have a denominator and a Wilson interval.",
                 "Report Wilson intervals for κ, the confusion matrix and recall."]
    check("R-03", "scanner control: the old blanket wordings are detected", all(wilson_kappa_violations(s) for s in synthetic))
    scan = {"06 §8.4": body84, "06 (whole)": md06, "08": md08, "BACKBONE": mdbb, "02": md02, "03": md03}
    viol = {k: v for k, t in scan.items() for v in [wilson_kappa_violations(t)] if v}
    check("R-03", "no clause in 06/08/BACKBONE/02/03 applies Wilson to κ or to the confusion matrix", not viol, str(viol))
    w_kept = re.search(r"Wilson 95% CI is about 0\.49–0\.94", rate_line)
    check("R-03", "8/10 Wilson example kept as a binomial-rate example", bool(w_kept))

    # ------------------------------------------------------------------ M-07
    print("\n== M-07 typed prerequisite registry (03 §2.1) ==")
    reg = parse_registry(md03)
    pre = parse_02_pre(md02)
    n_all = sum(len(r["all"]) for r in reg.values())
    n_grp = sum(len(r["any"]) for r in reg.values())
    n_mem = sum(len(g) for r in reg.values() for g in r["any"])
    n_exp = sum(len(r["exposure"]) for r in reg.values())
    n_adv = sum(len(r["advice"]) for r in reg.values())
    counts = (len(reg), n_all, n_grp, n_mem, n_exp, n_adv)
    m03c = re.search(r"(\d+) concepts; (\d+) `requires_all` edges; (\d+) any-groups with (\d+) member edges; "
                     r"(\d+) exposure edges; (\d+) advice edges", md03)
    check("M-07", "03 §2 claimed counts match the registry",
          m03c and tuple(int(x) for x in m03c.groups()) == counts, f"registry={counts}")
    unknown = {p for r in reg.values() for p in r["all"] + r["exposure"] + r["advice"] + [m for g in r["any"] for m in g]
               if p not in reg}
    check("M-07", "every referenced ID exists in the registry", not unknown, str(unknown))
    # acyclic over hard edges (all + any members + exposure), Kahn
    indeg = {c: 0 for c in reg}
    succ = {c: [] for c in reg}
    for c, r in reg.items():
        for p in set(r["all"] + r["exposure"] + [m for g in r["any"] for m in g]):
            succ[p].append(c)
            indeg[c] += 1
    q = [c for c, k in indeg.items() if k == 0]
    seen = 0
    while q:
        c = q.pop()
        seen += 1
        for s_ in succ[c]:
            indeg[s_] -= 1
            if indeg[s_] == 0:
                q.append(s_)
    check("M-07", "hard edges (requires_all + any-group members + exposure) are acyclic", seen == len(reg))
    back = [(p, c) for c, r in reg.items() for p in r["all"] + r["exposure"] + r["advice"] + [m for g in r["any"] for m in g]
            if phase_of(p) > phase_of(c)]
    check("M-07", "no edge points from a later phase to an earlier one", not back, str(back))
    small = [(c, g) for c, r in reg.items() for g in r["any"] if len(set(g)) < 2]
    check("M-07", "every any-group has >= 2 distinct members", not small, str(small))
    zero_ok = []
    for c, r in reg.items():
        for g in r["any"]:
            mastered = set(reg) - set(g) - {c}
            if can_unlock(reg, c, mastered, set(), {"3→4", "8→9", "9→10"}):
                zero_ok.append(c)
    check("M-07", "no any-group is satisfied by zero members", not zero_ok, str(zero_ok))
    nogate = [c for c in reg if 4 <= phase_of(c) <= 11 and "3→4" not in reg[c]["gate"]]
    check("M-07", "every Phase 4–11 concept requires Gate 3→4 (S2 included)", not nogate and "3→4" in reg["S2"]["gate"],
          str(nogate))
    order_bad = [c for c, r in reg.items() if r["gate"] & {"8→9", "9→10"} and "3→4" not in r["gate"]]
    check("M-07", "03 field note: a concept listing Gate 8→9/9→10 also lists Gate 3→4", not order_bad, str(order_bad))
    k_all = closure(reg, "K1", ("all",))
    k_full = closure(reg, "K1")
    check("M-07", "K1's requires_all closure (and full closure) contains no A*/S* concept",
          not {c for c in k_all | k_full if c[0] in "AS"}, f"|closure|={len(k_full)}")
    ms = set(reg) - {c for c in reg if c[0] in "AS"} - {"K1"}
    check("M-07", "K1 unlocks with no A*/S* mastered (v6 -> K1)", can_unlock(reg, "K1", ms, set(), {"3→4", "9→10"}))
    check("M-07", "K1: requires_all {I-CMP, V3, D2}, Gate 9→10, D3 advice only",
          set(reg["K1"]["all"]) == {"I-CMP", "V3", "D2"} and "9→10" in reg["K1"]["gate"]
          and reg["K1"]["advice"] == ["D3"] and "D3" not in k_full)
    check("M-07", "A5 any-group [A1|A2]; S3 any-group [S1|R5]; I-CMP exposure I2..I6",
          [sorted(g) for g in reg["A5"]["any"]] == [["A1", "A2"]] and [sorted(g) for g in reg["S3"]["any"]] == [["R5", "S1"]]
          and reg["I-CMP"]["exposure"] == ["I2", "I3", "I4", "I5", "I6"])
    allg = {"3→4", "8→9", "9→10"}
    m_a5 = closure(reg, "A5") - {"A1", "A2"}
    m_s3 = closure(reg, "S3") - {"S1", "R5"}
    check("M-07", "A5 cannot unlock without A1 or A2; unlocks with exactly one",
          not can_unlock(reg, "A5", m_a5, set(), allg) and can_unlock(reg, "A5", m_a5 | {"A1"}, set(), allg)
          and can_unlock(reg, "A5", m_a5 | {"A2"}, set(), allg))
    check("M-07", "S3 cannot unlock without S1 or R5; unlocks with exactly one",
          not can_unlock(reg, "S3", m_s3, set(), allg) and can_unlock(reg, "S3", m_s3 | {"S1"}, set(), allg)
          and can_unlock(reg, "S3", m_s3 | {"R5"}, set(), allg))

    # ------------------------------------------------------------------ R-04 exposure != mastery
    print("\n== R-04 exposure ≠ mastery (03 §2.1 unlock rule; 05 §6.1) ==")
    exp_ids = set(reg["I-CMP"]["exposure"])
    m_icmp = closure(reg, "I-CMP", ("all", "any"))          # I1 and its all/any ancestors, NOT I2–I6
    g34 = {"3→4"}
    check("R-04", "I1 mastered + I2–I6 exposed only (not mastered) => I-CMP unlocks",
          "I1" in m_icmp and not (m_icmp & exp_ids) and can_unlock(reg, "I-CMP", m_icmp, exp_ids, g34),
          f"|mastered|={len(m_icmp)} exposed={sorted(exp_ids)}")
    blocked = [e for e in sorted(exp_ids) if can_unlock(reg, "I-CMP", m_icmp, exp_ids - {e}, g34)]
    check("R-04", "any one of I2–I6 neither exposed nor mastered => I-CMP blocked (5 cases)", not blocked, str(blocked))
    check("R-04", "an exposure satisfied by mastery also counts (I2 mastered, I3–I6 exposed => unlocks)",
          can_unlock(reg, "I-CMP", m_icmp | {"I2"}, exp_ids - {"I2"}, g34))
    check("R-04", "round-1 helper behaviour reproduced as negative control (exposure looked up in mastered only)",
          not can_unlock(reg, "I-CMP", m_icmp, set(), g34))
    sub_all = not can_unlock(reg, "I-CMP", m_icmp - {"I1"}, exp_ids | {"I1"}, g34)
    sub_any = (not can_unlock(reg, "A5", m_a5, {"A1", "A2"}, allg) and not can_unlock(reg, "S3", m_s3, {"S1", "R5"}, allg)
               and not can_unlock(reg, "R3", closure(reg, "R3") - {"R1", "C4"}, {"R1", "C4"}, g34))
    all_cases = [c for c, r in reg.items() for p in r["all"]
                 if can_unlock(reg, c, set(reg) - {c, p}, {p}, {"3→4", "8→9", "9→10"})]
    check("R-04", "exposure alone never satisfies requires_all (I-CMP←I1 and all registry edges) or an any-group "
          "(A5 [A1|A2], S3 [S1|R5], R3 [R1|C4])", sub_all and sub_any and not all_cases, str(all_cases[:5]))
    k_goal = closure(reg, "K1", ("all", "any"))             # mastery needed for K1, without following exposure edges
    k_exp = {e for c in k_goal | {"K1"} for e in reg[c]["exposure"]} - k_goal
    ok_k1, _ = reachable(reg, "K1", k_goal, k_exp, {"3→4", "9→10"})
    ok_k1_noexp, _ = reachable(reg, "K1", k_goal, set(), {"3→4", "9→10"})
    check("R-04", "K1 reachable with I2–I6 exposed only and no A*/S* concept mastered or exposed (state built from "
          "the registry closure; each concept mastered only after it unlocks)",
          ok_k1 and k_exp == exp_ids and not {c for c in k_goal | k_exp if c[0] in "AS"} and not ok_k1_noexp,
          f"|mastered|={len(k_goal)}, exposed={sorted(k_exp)}; without exposure reachable={ok_k1_noexp}")
    f03 = section(md03, "2.1 Edge list")
    s61_05 = section(md05, "6.1 `progress/concept_tracker.csv`")
    check("R-04", "03 §2.1 states the two-set unlock rule (all/any vs mastered; exposure vs exposed ∪ mastered)",
          all(x in f03 for x in ("`mastered`", "`exposed`", "`exposed ∪ mastered`",
                                  "Exposure never substitutes for mastery")))
    csv_hdr = next((ln for ln in s61_05.splitlines() if ln.startswith("concept_id,")), "").split(",")
    csv_ex = next((ln for ln in code_blocks(s61_05, "csv")[-1].splitlines() if ln.startswith("C2,")), "").split(",")
    fld_rows = re.findall(r"^\| `([a-z_0-9]+)` \|", s61_05, flags=re.M)
    check("R-04", "05 §6.1 defines exposed_on (header, field table, example row width) and the mastered/exposed sets",
          "exposed_on" in csv_hdr and fld_rows == csv_hdr and len(csv_ex) == len(csv_hdr)
          and "exposed ∪ mastered" in s61_05 and "evidence_links" in s61_05,
          f"{len(csv_hdr)} columns; example row {len(csv_ex)} fields; field table == header: {fld_rows == csv_hdr}")
    derived ={c: sorted(x for x, r in reg.items() if c in r["all"] + r["exposure"] + [m for g in r["any"] for m in g])
               for c in reg}
    unl_bad = [(c, sorted(reg[c]["unlocks"]), derived[c]) for c in reg if sorted(reg[c]["unlocks"]) != derived[c]]
    check("M-07", "unlocks column equals the derived unlocks", not unl_bad, str(unl_bad))
    tier_bad = [(c, p) for c, r in reg.items() for p in r["all"] + [m for g in r["any"] for m in g]
                if (r["tier"] == "E" and reg[p]["tier"] in "US") or (r["tier"] == "U" and reg[p]["tier"] == "S")]
    check("M-07", "no E concept hard-requires U/S; no U concept hard-requires S", not tier_bad, str(tier_bad))
    # agreement with 02 Pre lines
    check("M-07", "02 has a Pre line for every registry concept", set(pre) == set(reg),
          f"missing={set(reg) - set(pre)} extra={set(pre) - set(reg)}")
    not_anc = []
    for c, p in pre.items():
        named = set(p["all"]) | set(p["exposure"]) | {m for g in p["any"] for m in g}
        miss = named - closure(reg, c)
        if miss:
            not_anc.append((c, sorted(miss)))
    check("M-07", "every concept named in a 02 Pre line is an ancestor in the 03 registry", not not_anc, str(not_anc))
    any_bad = [c for c, p in pre.items() if p["any"] and sorted(map(sorted, p["any"])) != sorted(map(sorted, reg[c]["any"]))]
    any_bad += [c for c, r in reg.items() if r["any"] and not pre[c]["any"]]
    check("M-07", "02 any{...} groups == 03 requires_any_groups", not any_bad, str(any_bad))
    exp_bad = [c for c in reg if sorted(pre[c]["exposure"]) != sorted(reg[c]["exposure"])]
    check("M-07", "02 exposure{...} == 03 requires_exposure", not exp_bad, str(exp_bad))
    gate_bad = []
    for c in reg:
        g02 = set(pre[c]["gate"]) | ({"3→4"} if 4 <= phase_of(c) <= 11 else set())   # 02 legend: implicit for 4–11
        if g02 != reg[c]["gate"]:
            gate_bad.append((c, sorted(g02), sorted(reg[c]["gate"])))
    check("M-07", "02 gate{...} (+ implicit 3→4 for Phases 4–11) == 03 requires_gate", not gate_bad, str(gate_bad))
    typed_cards = [c for c in ("A5", "S1", "S2", "S3", "K1", "I-CMP") if not pre[c]["raw"].startswith("`")]
    check("M-07", "02 cards A5, S1, S2, S3, K1, I-CMP use typed Pre notation", not typed_cards, str(typed_cards))
    diffs = []
    for c in reg:
        only03 = sorted(set(reg[c]["all"]) - set(pre[c]["all"]))
        only02 = sorted(set(pre[c]["all"]) - set(reg[c]["all"]))
        if only03 or only02:
            diffs.append(f"{c}: 03-only {only03} / 02-only {only02}")
    info(f"requires_all vs 02 Pre all-lists differ directly for {len(diffs)} concepts (02 names ancestors or "
         f"lab-baseline items; every 02 item is an 03 ancestor per the check above):")
    for x in diffs:
        info("   " + x)
    reg02 = {c: {"all": p["all"], "any": p["any"], "exposure": p["exposure"]} for c, p in pre.items()}
    stricter = []
    for c in reg:
        extra = sorted(x for x in set(reg[c]["all"]) - set(pre[c]["all"]) if x not in closure(reg02, c))
        if extra:
            stricter.append(f"{c} <- {extra}")
    info("03 requires_all items NOT implied even transitively by 02's Pre lines (03 is stricter; gates excluded): "
         + ("; ".join(stricter) if stricter else "none"))

    # ------------------------------------------------------------------ B-01 / R-01 (08 Part 7, Part 4)
    print("\n== B-01 / R-01 approval gates (08 Part 7) and decision rows (08 Part 4) ==")
    gates = parse_gate_sections(md08)
    table = parse_gate_table(section(md08, "Part 7"))
    all_ids = [i for g in "ABC" for i in gates[g]]
    multi = sorted({i for i in all_ids if all_ids.count(i) > 1})
    check("B-01", "every checklist item ID appears in exactly one approval gate section",
          not multi and all(gates[g] for g in "ABC"),
          "; ".join(f"{g}: {len(gates[g])}" for g in "ABC") + f"; total {len(all_ids)}")
    tbl_bad = {g: sorted(set(table.get(g, [])) ^ set(gates[g])) for g in "ABC"
               if sorted(table.get(g, [])) != sorted(gates[g])}
    check("B-01", "the 08 Part 7 gate table lists exactly the items of each gate section (ranges expanded)",
          not tbl_bad, str(tbl_bad))
    bb_table = parse_gate_table(section(mdbb, "3."))
    bb_bad = {g: sorted(set(bb_table.get(g, [])) ^ set(gates[g])) for g in "ABC"
              if sorted(bb_table.get(g, [])) != sorted(gates[g])}
    check("B-01", "BACKBONE §3 approval-gate table assigns the same items to each gate as 08 Part 7", not bb_bad,
          str(bb_bad))
    bad_a = [i for i in gates["A"] if re.match(r"(E|BL|MX)-", i) or i == "DEC-3"]
    check("B-01", "Gate A holds only design-time items (no E-*, BL-*, MX-*, DEC-3)", not bad_a,
          ", ".join(gates["A"]))
    check("B-01", "E-1…E-4, BL-1, DEC-1c, DEC-3 sit in Gate B; MX-1…MX-5 in Gate C",
          set(gates["B"]) == {"E-1", "E-2", "E-3", "E-4", "BL-1", "DEC-1c", "DEC-3"}
          and set(gates["C"]) == {f"MX-{i}" for i in range(1, 6)})
    dec1a = gates["A"].get("DEC-1a", {"text": "", "ticked": False})
    listed = re.search(r"\(([^)]*D-\d\d[^)]*)\)", dec1a["text"])
    dec1a_ids = re.findall(r"D-\d\d", listed.group(1)) if listed else []
    want_1a = ["D-03", "D-04", "D-05", "D-10", "D-14", "D-16", "D-19", "D-20"]
    check("R-01", "DEC-1a lists exactly D-03, D-04, D-05, D-10, D-14, D-16, D-19, D-20", dec1a_ids == want_1a,
          str(dec1a_ids))
    rows4 = part4_rows(md08)
    undecided = [i for i in want_1a if "Decided 2026-10-08" not in rows4.get(i, "")]
    learner_r2 = [i for i in ("D-14", "D-16", "D-19", "D-20") if "Decided 2026-10-08 — Learner" not in rows4.get(i, "")]
    check("R-01", "each DEC-1a decision's Part 4 row is marked Decided 2026-10-08 (D-14/16/19/20 '— Learner')",
          not undecided and not learner_r2, f"undecided={undecided} not-learner={learner_r2}")
    coach = [i for i in ("D-06", "D-07") if "Confirmed 2026-10-08 — Coach" not in rows4.get(i, "")]
    dec1b = gates["A"].get("DEC-1b", {"text": ""})["text"]
    check("R-01", "D-06/D-07 rows read 'Confirmed 2026-10-08 — Coach'; DEC-1b covers D-06, D-07, D-17",
          not coach and all(x in dec1b for x in ("D-06", "D-07", "D-17")), str(coach))
    p2 = gates["A"].get("P-2", {"text": "", "ticked": False})
    check("R-01", "DEC-1a and P-2 are ticked with the dated learner notes",
          dec1a["ticked"] and "(learner decisions recorded 2026-10-08)" in dec1a["text"]
          and p2["ticked"] and "(learner agreement 2026-10-08)" in p2["text"])
    p7 = section(md08, "Part 7")
    check("R-01", "08 Part 7 allows the decision-only preflight before Gate A; O2 implements DEC-1a, does not make it",
          "decision-only preflight" in section(md08, "Approval gate A") and "explicitly allowed **before** Gate A" in p7
          and "no Gate A item is produced by O2 or any later lab" in p7 and "**implements**" in p7)
    stale = {}
    for n, t in (("08", md08), ("02", md02), ("BACKBONE", mdbb)):
        hits = [ln.strip()[:90] for ln in t.splitlines() if not ln.lstrip().startswith("> Revised")
                and re.search(r"confirmed at the start of O2|Decide at O2|remain to confirm at O2", ln, re.I)]
        if hits:
            stale[n] = hits
    check("R-01", "no 'confirmed at the start of O2' / 'Decide at O2' wording left in 08, 02, BACKBONE", not stale,
          str(stale))
    bb3 = section(mdbb, "3.")
    check("R-01", "02 §4 and BACKBONE §3 say Gate A needs only design-time artifacts + preflight decisions",
          "decision-only preflight" in section(md02, "4. Mastery gates") and "decision-only preflight" in bb3)

    # ------------------------------------------------------------------ R-06 (Corpus H timing)
    print("\n== R-06 Corpus T/H timing ==")
    spec1 = (root / "reviews" / "CORRECTIONS_SPEC_2026-10-08.md").read_text(encoding="utf-8")
    th_new = "Corpus T chosen and frozen (with snapshot) before Phase 3; Corpus H chosen and frozen before K1"
    old_th = {n: len(re.findall(r"Corpus T/H chosen, frozen", t)) for n, t in (("BACKBONE", mdbb), ("08", md08))}
    check("R-06", "BACKBONE §3 Gate B row and 08 DEC-3 put T before Phase 3 and H before K1; no 'Corpus T/H chosen, "
          "frozen' left", th_new in bb3 and "Corpus H is chosen and frozen later, before K1"
          in gates["B"].get("DEC-3", {"text": ""})["text"] and not any(old_th.values()), str(old_th))
    spec_old = [ln for ln in spec1.splitlines() if "Corpus T/H chosen, frozen" in ln]
    check("R-06", "round-1 spec copy: every 'Corpus T/H chosen, frozen' line carries '[corrected in round 2, R-06: …]'",
          spec_old and all("[corrected in round 2, R-06: " + th_new in ln for ln in spec_old), f"{len(spec_old)} line(s)")

    # ------------------------------------------------------------------ summary
    n_fail = sum(1 for r in RESULTS if not r[2])
    by: dict[str, list[int]] = {}
    for fid, _, ok, _ in RESULTS:
        by.setdefault(fid, [0, 0])[0 if ok else 1] += 1
    print("\nBY FINDING: " + "; ".join(f"{k} {v[0]}/{v[0] + v[1]}" for k, v in by.items()))
    print(f"SUMMARY: {len(RESULTS) - n_fail} passed, {n_fail} failed, {len(RESULTS)} checks")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
