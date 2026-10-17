"""token_budget_check: with MY documents, chunk size and model choices, does each call fit, what will it cost, and how
long will a run take?

What this is: a command-line tool (also importable) that chunks your documents as the P1/P3 lessons do, counts tokens
with the right tokenizer for each job, builds the v0 prompt (06 §3.3) for each of your questions, and writes a Markdown
report:
  1 Corpus ratios      characters per token for each tokenizer, and the error of "characters ÷ 4"
  2 Content mix        digits, code-like lines, non-Latin letters (the costly kinds of text), special-token strings
  3 Chunks             tokens per chunk for each tokenizer; the embedder's truncation rate (MiniLM: 254 text tokens)
  4 Prompt budget      per question: system + question + k sources, + template overhead + output cap, vs the window
  5 Output cap         the cap, the effort, and (with --traces) recorded reasoning tokens, finish_reason, empty answers
  6 Cost               per call and per planned run, split input / output, for every model in the dated price sheet
  7 Run time           minimum minutes from tokens per minute (TPM), and the daily token quota
  8 Checklist          C1-C12 with a verdict (✓ fine, ✗ problem found, ? check by hand), the evidence, how to check
  9 Recommendation     first matching rule wins (see recommend())
What this is not: a bill. Local counts are a lower bound for what the provider bills (its chat template adds tokens),
and the output side is an upper bound (the cap). Replace estimates with recorded `usage` as soon as you have it.

Which tokenizer counts what (the lesson's 3-row rule):
  embedder tokenizer  -> truncation      (MiniLM WordPiece from the local Hugging Face cache, offline)
  generator tokenizer -> prompt budget   (gpt-oss: tiktoken o200k_harmony, resolved BY NAME; Claude: tiktoken is only a
                                          proxy, Claude's own count comes from its free count_tokens endpoint)
  provider `usage`    -> the bill        (read from --traces, a JSONL file of recorded responses)
Every count uses encode(..., disallowed_special=()): a document that contains "<|endoftext|>" or "<|start|>" makes
tiktoken's default encode() raise ValueError (lesson trap K3); this tool reports such strings (C4) and counts them as
ordinary text.

No API calls. This version makes no network call at all: --pilot, --claude-count and --embedder cohere need the shared
LLMOps cache package (study/llmops/), which is not built yet, so they only print a note and the dependent checks stay
"?". Standard library + tiktoken + tokenizers + pymupdf; MiniLM's tokenizer is read from the local Hugging Face cache
with HF_HUB_OFFLINE=1. tiktoken needs its encoding files in its local cache (downloaded once by earlier P1 scripts).

Chunking: as P3's bm25_fit_check: each document's pages are joined with "\n" (PyMuPDF page.get_text()), then cut into
windows of --chunk-size with --overlap, in --unit chars (default; P3's 91 windows) or tokens (generator tokens).
Prompt: 06 §3.3 v0 template (SYSTEM_V0 below, verbatim), sources as "[i] (doc_id:page)\\n<chunk>". Two prompt sizes per
question: "sample" = the first k chunks (as P1_FACTS S9; NOT a retrieval result) and "upper" = the k chunks with the
most generator tokens (the worst case any retriever could return).

Usage, from rag_learning/:
    uv run python study/tools/token_budget_check.py --docs my_docs/ --questions my_questions.txt --report report.md
    uv run python study/tools/token_budget_check.py --docs a.pdf --doc-ids a --generator anthropic:claude-haiku-5-5 --effort low
    uv run python study/tools/token_budget_check.py --docs a.pdf --traces results.jsonl --max-completion-tokens 1024
Questions: .txt (one per line; "ID | question" sets an id; blank lines and lines starting with # are skipped) or .jsonl
({"id": ..., "q": ...} or {"qid": ..., "question": ...}).
Traces: .jsonl, one recorded response per line, either OpenAI/Groq-shaped ({"usage": {"prompt_tokens",
"completion_tokens", "completion_tokens_details": {"reasoning_tokens"}}, "choices": [{"finish_reason", "message":
{"content"}}]}, optionally wrapped in "response") or flat ({"usage": ..., "finish_reason": ..., "answer": ...}).
Claude-shaped usage (input_tokens / output_tokens, stop_reason "max_tokens") is read too. Optional per line:
"messages" (the prompt as sent, to measure billed - counted overhead) or "counted_prompt_tokens".

Import:
    from token_budget_check import run_check, render_report
    result = run_check(["doc.pdf"], "questions.txt", doc_ids=["climate"])
    print(render_report(result))
"""
from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")             # never download the embedder's tokenizer
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import argparse
import bisect
import datetime as dt
import importlib.metadata as md
import json
import math
import re
import statistics as st
import sys
import unicodedata
from pathlib import Path

import tiktoken

OK, BAD, ASK = "✓", "✗", "?"
EXTS = (".pdf", ".txt", ".md")
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
LLMOPS_NOTE = ("needs the shared LLMOps cache package (study/llmops/), which is not built yet; nothing was called")

# 06 §3.3 prompts/answer_v1.txt, SYSTEM part, verbatim (same string as sources/verification/P1/p1_measure.py S9)
SYSTEM_V0 = (
    "You answer questions using ONLY the numbered sources below.\n"
    "Rules:\n"
    "1. Every factual sentence must end with one or more citations in the form [doc_id:page],\n"
    "   copied exactly from the source headers, e.g. [climate:10].\n"
    "2. If the sources do not contain the answer, reply exactly:\n"
    "   \"I cannot answer this from the provided documents.\"\n"
    "   Do not use outside knowledge.\n"
    "3. Do not cite a source that does not support the sentence.\n"
    "4. Be concise: at most 5 sentences.\n")

# Dated price sheet (per 1M tokens), LLMOPS_FOUNDATION §6.2 and research P1 sources [P1-1], [P1-16], read 2026-10-17.
# The same content ships as study/tools/examples/prices_2026-10-17.json; pass your own with --prices.
DEFAULT_PRICES = {
    "price_table_version": "2026-10-17",
    "unit": "USD per 1M tokens",
    "source": "LLMOPS_FOUNDATION §6.2; Groq model page openai/gpt-oss-20b [P1-1]; claude-api skill table [P1-16]",
    "models": {
        "groq:openai/gpt-oss-20b": {
            "input": 0.075, "output": 0.30, "cached_input": 0.037, "context_window": 131072, "max_output": 65536,
            "note": "Groq model page, read 2026-10-17"},
        "anthropic:claude-haiku-5-5": {
            "input": 0.10, "output": 0.50, "cached_input": None, "context_window": 1000000, "max_output": None,
            "note": "prices for prompts up to 100K tokens ($0.50 / $2.50 beyond); max output not recorded"},
    },
    "rate_limits": {
        "groq:openai/gpt-oss-20b": {"tpm": 8000, "tpd": 200000, "note": "plan row UNVERIFIED, foundation §2.5"},
    },
}

# Generator -> tiktoken encoding, BY NAME. Never tiktoken.encoding_for_model("openai/gpt-oss-20b"): the provider
# prefix makes it raise KeyError (lesson trap K2).
KNOWN_ENCODINGS = {"gpt-oss-20b": "o200k_harmony", "gpt-oss-120b": "o200k_harmony"}
EFFORTS = {"groq": ("low", "medium", "high"), "anthropic": ("low", "medium", "high", "max")}
GROQ_DEFAULT_CAP = 1024                                  # Groq: max_completion_tokens default [P1-2]

EMBEDDER_SPECIALS = ("[CLS]", "[SEP]", "[PAD]", "[MASK]", "[UNK]")
SPECIAL_RE = re.compile(r"<\|[^<>|\s]{1,64}\|>")
CODE_LINE = re.compile(
    r"^\s*(?:def |class |import |from \S+ import |return\b|elif\b|else:|try:|except\b|for .+ in .+:|while .+:|"
    r"if .+:\s*$|@\w+|#include|function\b|const |let |var )|[{};]\s*$|^\s*[}\])]|"
    r"\w+\s*(?:==|!=|\+=|-=|=>|->)\s*\S|\w\(\)|\w+\.\w+\(")


# ---------------------------------------------------------------------------------------------------------------- input
def load_documents(paths, doc_ids=None):
    """Files or folders (.pdf, .txt, .md; folders searched recursively, sorted). Same extraction as bm25_fit_check."""
    files, seen = [], set()
    for p in map(Path, paths):
        if p.is_dir():
            found = sorted(q for q in p.rglob("*") if q.is_file() and q.suffix.lower() in EXTS)
        elif p.is_file():
            if p.suffix.lower() not in EXTS:
                raise ValueError(f"unsupported file type: {p} (use .pdf, .txt or .md)")
            found = [p]
        else:
            raise FileNotFoundError(f"no such file or folder: {p}")
        for f in found:
            if f.resolve() not in seen:
                seen.add(f.resolve())
                files.append(f)
    if doc_ids and len(doc_ids) != len(files):
        raise ValueError(f"--doc-ids gives {len(doc_ids)} id(s) for {len(files)} document(s)")
    docs = []
    for n, f in enumerate(files):
        if f.suffix.lower() == ".pdf":
            import pymupdf                                # pinned 1.26.7 in this project
            with pymupdf.open(f) as d:
                pages = [pg.get_text() for pg in d]
        else:
            pages = [f.read_text(encoding="utf-8", errors="replace")]
        docs.append({"name": f.name, "id": doc_ids[n] if doc_ids else f.stem, "pages": pages,
                     "is_pdf": f.suffix.lower() == ".pdf", "text": "\n".join(pages)})
    return docs


def load_questions(source):
    """A path (.txt or .jsonl) or a list of dicts / strings. Returns [{"id", "q"}]."""
    if source is None:
        return []
    if isinstance(source, (str, Path)) and Path(source).is_file():
        path = Path(source)
        lines = path.read_text(encoding="utf-8").splitlines()
        if path.suffix.lower() == ".jsonl":
            items = []
            for n, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise ValueError(f"{path}, line {n}: not valid JSON ({e})") from None
        else:
            items = []
            for line in lines:
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                qid, sep, q = line.partition(" | ")
                items.append({"id": qid.strip(), "q": q.strip()} if sep else line.strip())
    elif isinstance(source, (list, tuple)):
        items = list(source)
    else:
        raise FileNotFoundError(f"questions file not found: {source}")
    out = []
    for n, it in enumerate(items, 1):
        it = {"q": it} if isinstance(it, str) else dict(it)
        q = str(it.get("q") or it.get("question") or "").strip()
        if not q:
            raise ValueError(f"question {n}: missing \"q\"")
        out.append({"id": str(it.get("id") or it.get("qid") or f"Q{n}"), "q": q})
    return out


def load_prices(path=None):
    if path is None:
        return DEFAULT_PRICES
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "models" not in data:
        raise ValueError(f"{path}: a price sheet needs a \"models\" object")
    return data


# ---------------------------------------------------------------------------------------------------------------- tokenizers
def resolve_generator(generator, encoding=None):
    """'provider:model' -> encoding, by name. Returns a dict with the encoding object and how it was found.
    Also records what the naive call tiktoken.encoding_for_model(<model id as in .env>) does (trap K2)."""
    provider, sep, model = generator.partition(":")
    if not sep or not model:
        raise ValueError("--generator must be provider:model, e.g. groq:openai/gpt-oss-20b or anthropic:claude-haiku-5-5")
    provider = provider.lower()
    try:
        naive = f"-> {tiktoken.encoding_for_model(model).name}"
    except KeyError as e:
        naive = "-> KeyError: " + str(e).strip("'\"").split(". ")[0] + "."
    base = model.split("/")[-1]
    info = {"provider": provider, "model": model, "base": base, "naive": f"encoding_for_model({model!r}) {naive}",
            "proxy": False, "resolved": True}
    if encoding:
        info.update(encoding=encoding, how=f"--encoding {encoding} (by name)")
    elif provider == "anthropic":
        info.update(encoding="o200k_base", proxy=True,
                    how="proxy: o200k_base (tiktoken does not know Claude's tokenizer; Claude's count comes from count_tokens)")
    elif base in KNOWN_ENCODINGS:
        info.update(encoding=KNOWN_ENCODINGS[base], how=f"by name: {base} -> {KNOWN_ENCODINGS[base]}")
    else:
        try:
            name = tiktoken.encoding_for_model(base).name
            info.update(encoding=name, how=f"encoding_for_model({base!r}) on the id without the provider prefix -> {name}")
        except KeyError:
            info.update(encoding="o200k_base", resolved=False,
                        how=f"UNKNOWN: no tiktoken encoding for {base!r}; counted with o200k_base as a stand-in "
                            "(pass --encoding NAME, or count with the model's own tokenizer)")
    info["enc"] = tiktoken.get_encoding(info["encoding"])
    return info


def ntok(enc, text):
    return len(enc.encode(text, disallowed_special=()))


class WordPiece:
    """MiniLM's WordPiece tokenizer, read offline from the local Hugging Face cache (tokenizers library)."""

    def __init__(self, model=MINILM):
        from huggingface_hub import snapshot_download
        from tokenizers import Tokenizer
        path = Path(snapshot_download(model, local_files_only=True))
        self.snapshot = path.name
        self.tk = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tk.no_truncation()
        self.tk.no_padding()
        cfg = json.loads((path / "sentence_bert_config.json").read_text(encoding="utf-8"))
        self.max_seq_length = int(cfg["max_seq_length"])  # 256 IDs incl. [CLS] and [SEP]
        self.limit = self.max_seq_length - 2              # 254 text tokens

    def count(self, text):                                # text tokens only (no [CLS]/[SEP])
        return len(self.tk.encode(text, add_special_tokens=False).ids)


# ---------------------------------------------------------------------------------------------------------------- chunks
def make_chunks(docs, size=1000, overlap=200, unit="chars", enc=None):
    """Plain windows per document. unit=chars: P3's 91 windows for the climate PDF at 1000/200. unit=tokens: windows of
    generator tokens, decoded back to text."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need chunk-size > 0 and 0 <= overlap < chunk-size")
    if unit not in ("chars", "tokens"):
        raise ValueError("--unit must be chars or tokens")
    chunks = []
    for d in docs:
        text = d["text"]
        starts, pos = [], 0
        for pg in d["pages"]:
            starts.append(pos)
            pos += len(pg) + 1
        page = (lambda a: bisect.bisect_right(starts, a)) if d["is_pdf"] else (lambda a: 1)
        if unit == "chars":
            spans = [(a, min(a + size, len(text))) for a in range(0, len(text), size - overlap)]
        else:
            ids = enc.encode(text, disallowed_special=())
            _, offs = enc.decode_with_offsets(ids)
            offs = list(offs) + [len(text)]
            spans = [(offs[a], offs[min(a + size, len(ids))]) for a in range(0, len(ids), size - overlap)]
        for j, (a, e) in enumerate(spans):
            chunks.append({"id": f"{d['id']}#{j}", "doc": d["id"], "page": page(a), "start": a, "end": e, "text": text[a:e]})
    return chunks


def build_prompt(question, chunks):
    """06 §3.3: SYSTEM_V0 + 'Sources:\\n[1] (doc:page)\\n<chunk>\\n\\n[2] ...\\n\\nQuestion: q\\nAnswer:'."""
    ctx = "\n\n".join(f"[{i}] ({c['doc']}:{c['page']})\n{c['text']}" for i, c in enumerate(chunks, 1))
    return ctx, f"Sources:\n{ctx}\n\nQuestion: {question}\nAnswer:"


# ---------------------------------------------------------------------------------------------------------------- helpers
def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * p / 100
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def price(x):
    t = f"{x:.3f}".rstrip("0")
    return "$" + (t + "0" if len(t.split(".")[1]) < 2 else t)


def money(x):
    if x is None:
        return "-"
    if x == 0:
        return "$0"
    d = max(2, -math.floor(math.log10(abs(x))) + 2)
    return f"${x:,.{d}f}"


def _version(p):
    try:
        return md.version(p)
    except md.PackageNotFoundError:
        return "not installed"


def content_mix(docs, enc):
    text = "\n".join(d["text"] for d in docs)
    chars = len(text)
    digits = sum(ch.isdigit() for ch in text)
    letters = [ch for ch in text if ch.isalpha()]
    nonlatin = [ch for ch in letters if not unicodedata.name(ch, "").startswith("LATIN")]
    lines = [ln for ln in text.splitlines() if ln.strip()]
    code = [ln for ln in lines if CODE_LINE.search(ln)]
    runs = re.findall(r"\d[\d.,:\-/]*\d|\d", text)
    nl_runs = re.findall(r"[^\W\d_A-Za-z\u00C0-\u024F]+", text)

    def ratio(parts):
        s = "".join(parts)
        t = sum(ntok(enc, p) for p in parts)
        return (len(s) / t) if t else None
    return {"chars": chars, "digits": digits, "pct_digits": 100 * digits / chars if chars else 0.0,
            "digit_runs": len(runs), "digit_ct": ratio(runs),
            "letters": len(letters), "nonlatin": len(nonlatin),
            "pct_nonlatin": 100 * len(nonlatin) / len(letters) if letters else 0.0, "nonlatin_ct": ratio(nl_runs),
            "lines": len(lines), "code_lines": len(code), "pct_code": 100 * len(code) / len(lines) if lines else 0.0,
            "code_ct": ratio(code), "code_examples": code[:3]}


def find_specials(docs, enc):
    gen = {}
    for d in docs:
        for m in SPECIAL_RE.finditer(d["text"]):
            s = m.group(0)
            if s in enc.special_tokens_set:
                gen[s] = gen.get(s, 0) + 1
    emb = {s: sum(d["text"].count(s) for d in docs) for s in EMBEDDER_SPECIALS}
    emb = {s: n for s, n in emb.items() if n}
    demo = None
    if gen:
        s = next(iter(gen))
        try:
            enc.encode(s)
            demo = f"encode({s!r}) did not raise"
        except ValueError as e:
            demo = f"encode({s!r}) -> ValueError: {str(e)[:90]}"
    return {"generator": gen, "embedder": emb, "demo": demo}


# ---------------------------------------------------------------------------------------------------------------- traces
def _get(d, *path):
    for p in path:
        if isinstance(d, dict):
            d = d.get(p)
        elif isinstance(d, list) and isinstance(p, int) and len(d) > p:
            d = d[p]
        else:
            return None
    return d


def parse_trace(rec):
    """One recorded response -> usage numbers. Accepts Groq/OpenAI-shaped, flat, or Claude-shaped records."""
    r = rec.get("response") if isinstance(rec.get("response"), dict) else rec
    usage = r.get("usage") or rec.get("usage") or {}
    prompt = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion = usage.get("completion_tokens", usage.get("output_tokens"))
    reasoning = _get(usage, "completion_tokens_details", "reasoning_tokens")
    finish = rec.get("finish_reason") or _get(r, "choices", 0, "finish_reason") or r.get("stop_reason") or rec.get("stop_reason")
    answer = rec.get("answer", rec.get("content") if isinstance(rec.get("content"), str) else None)
    if answer is None:
        answer = _get(r, "choices", 0, "message", "content")
    if answer is None and isinstance(r.get("content"), list):
        answer = "".join(b.get("text", "") for b in r["content"] if isinstance(b, dict) and b.get("type") == "text")
    return {"prompt": prompt, "completion": completion, "reasoning": reasoning,
            "cached": _get(usage, "prompt_tokens_details", "cached_tokens"),
            "finish": finish, "length": finish in ("length", "max_tokens"),
            "empty": answer is not None and not str(answer).strip(), "answer_known": answer is not None,
            "messages": rec.get("messages"), "counted": rec.get("counted_prompt_tokens"),
            "cap": rec.get("max_completion_tokens") or _get(rec, "params", "max_completion_tokens")}


def trace_stats(path, enc):
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(parse_trace(json.loads(line)))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}, line {n}: not valid JSON ({e})") from None
    for t in rows:
        if t["counted"] is None and isinstance(t["messages"], list):
            t["counted"] = sum(ntok(enc, str(m.get("content", ""))) for m in t["messages"] if isinstance(m, dict))
    comp = [t["completion"] for t in rows if t["completion"] is not None]
    reas = [t["reasoning"] for t in rows if t["reasoning"] is not None]
    share = [t["reasoning"] / t["completion"] for t in rows if t["reasoning"] is not None and t["completion"]]
    over = [t["prompt"] - t["counted"] for t in rows if t["prompt"] is not None and t["counted"] is not None]
    finishes = {}
    for t in rows:
        finishes[str(t["finish"])] = finishes.get(str(t["finish"]), 0) + 1
    return {"path": str(path), "n": len(rows), "finishes": finishes,
            "length": sum(t["length"] for t in rows), "empty": sum(t["empty"] for t in rows),
            "answers_known": sum(t["answer_known"] for t in rows),
            "completion_p50": pct(comp, 50), "completion_p95": pct(comp, 95), "completion_max": max(comp) if comp else None,
            "reasoning_n": len(reas), "reasoning_p50": pct(reas, 50), "reasoning_p95": pct(reas, 95),
            "share_p50": pct(share, 50), "share_p95": pct(share, 95),
            "overhead_n": len(over), "overhead_p50": pct(over, 50), "overhead_max": max(over) if over else None,
            "cached_n": sum(1 for t in rows if t["cached"]), "caps": sorted({t["cap"] for t in rows if t["cap"]})}


# ---------------------------------------------------------------------------------------------------------------- the check
def run_check(docs, questions=None, doc_ids=None, chunk_size=1000, overlap=200, unit="chars", k=4,
              generator="groq:openai/gpt-oss-20b", encoding=None, max_completion_tokens=512, effort="low",
              temperature="auto", overhead=71, embedder="minilm", prices=None, tpm=8000, tpd=200000, runs=100,
              max_minutes=60.0, traces=None, pilot=None, claude_count=False, today=None):
    """docs: file/folder paths (or loaded documents); questions: a path or a list. Returns a result dict."""
    if k < 1:
        raise ValueError("k must be at least 1")
    if max_completion_tokens < 1:
        raise ValueError("max-completion-tokens must be at least 1")
    if embedder not in ("minilm", "cohere"):
        raise ValueError("--embedder must be minilm or cohere")
    gen = resolve_generator(generator, encoding)
    enc = gen["enc"]
    provider = gen["provider"]
    if temperature == "auto":
        temperature = 0.0 if provider == "groq" else None      # 06 §3.1: T = 0 on Groq; Claude: send none
    effort = None if effort in (None, "none", "") else effort
    sheet = prices if isinstance(prices, dict) else load_prices(prices)
    model_key = f"{provider}:{gen['model']}"
    mprice = sheet["models"].get(model_key)
    today = dt.date.fromisoformat(today) if isinstance(today, str) else (today or dt.date.today())
    docs = docs if (docs and isinstance(docs[0], dict)) else load_documents(docs, doc_ids)
    qs = load_questions(questions)
    chunks = make_chunks(docs, chunk_size, overlap, unit, enc)
    notes = []
    if pilot:
        notes.append(f"--pilot {pilot}: {LLMOPS_NOTE}.")
    if claude_count:
        notes.append(f"--claude-count: {LLMOPS_NOTE}.")
    if embedder == "cohere":
        notes.append(f"--embedder cohere (fetching Cohere's tokenizer): {LLMOPS_NOTE}.")
    res = {"settings": {"generator": generator, "encoding": gen["encoding"], "chunk_size": chunk_size, "overlap": overlap,
                        "unit": unit, "k": k, "cap": max_completion_tokens, "effort": effort, "temperature": temperature,
                        "overhead": overhead, "embedder": embedder, "tpm": tpm, "tpd": tpd, "runs": runs,
                        "max_minutes": max_minutes, "today": today.isoformat(), "traces": str(traces) if traces else None,
                        "pilot": pilot, "claude_count": claude_count,
                        "versions": {p: _version(p) for p in ("tiktoken", "tokenizers", "pymupdf")}},
           "generator": {kk: v for kk, v in gen.items() if kk != "enc"}, "notes": notes,
           "documents": [{"name": d["name"], "id": d["id"], "pages": len(d["pages"]), "chars": len(d["text"]),
                          "bytes": len(d["text"].encode("utf-8"))} for d in docs]}
    # ---- 1 corpus ratios
    full = "\n".join(d["text"] for d in docs)
    wp = None
    if embedder == "minilm":
        try:
            wp = WordPiece()
        except Exception as e:  # noqa: BLE001
            notes.append(f"MiniLM tokenizer could not load from the local cache ({type(e).__name__}: {str(e)[:120]}).")
    tokenizers_ = [(gen["encoding"], "generator" + (" (proxy)" if gen["proxy"] else ""), lambda t: ntok(enc, t))]
    for name in ("o200k_base", "cl100k_base"):
        if name != gen["encoding"]:
            e2 = tiktoken.get_encoding(name)
            tokenizers_.append((name, "comparison", lambda t, e2=e2: ntok(e2, t)))
    if wp:
        tokenizers_.append(("MiniLM WordPiece", "embedder", wp.count))
    chars, nbytes = len(full), len(full.encode("utf-8"))
    corpus = []
    for name, role, f in tokenizers_:
        n = f(full)
        corpus.append({"tokenizer": name, "role": role, "tokens": n, "ct": chars / n if n else None,
                       "bt": nbytes / n if n else None, "div4": chars / 4,
                       "err4": 100 * (chars / 4 - n) / n if n else None})
    res["corpus"] = {"chars": chars, "bytes": nbytes, "rows": corpus}
    # ---- 2 content mix and specials
    res["mix"] = content_mix(docs, enc)
    res["specials"] = find_specials(docs, enc)
    # ---- 3 chunks
    for c in chunks:
        c["gen"] = ntok(enc, c["text"])
        c["wp"] = wp.count(c["text"]) if wp else None
    ratios = [len(c["text"]) / c["gen"] for c in chunks if c["gen"]]

    def dist(xs):
        return {"min": min(xs), "median": st.median(xs), "p95": pct(xs, 95), "max": max(xs)} if xs else None
    trunc = None
    if wp:
        over = [c for c in chunks if c["wp"] > wp.limit]
        lost = sum(c["wp"] - wp.limit for c in over)
        trunc = {"limit": wp.limit, "max_seq_length": wp.max_seq_length, "snapshot": wp.snapshot, "n_over": len(over),
                 "rate": 100 * len(over) / len(chunks) if chunks else 0.0,
                 "lost_tokens": lost, "lost_pct": 100 * lost / sum(c["wp"] for c in chunks) if chunks else 0.0,
                 "worst": [{"id": c["id"], "page": c["page"], "tokens": c["wp"]}
                           for c in sorted(over, key=lambda c: -c["wp"])[:5]]}
    res["chunks"] = {"N": len(chunks), "chars": dist([len(c["text"]) for c in chunks]),
                     "gen": dist([c["gen"] for c in chunks]), "wp": dist([c["wp"] for c in chunks]) if wp else None,
                     "ratio": dist(ratios), "truncation": trunc}
    # ---- 4 prompt budget
    sys_t = ntok(enc, SYSTEM_V0)
    sample = chunks[:k]
    upper = sorted(chunks, key=lambda c: (-c["gen"], chunks.index(c)))[:k]
    window = mprice.get("context_window") if mprice else None
    max_out = mprice.get("max_output") if mprice else None
    qrows = []
    for q in (qs or [{"id": "(no question)", "q": ""}]):
        row = {"id": q["id"], "q": q["q"], "q_tokens": ntok(enc, q["q"])}
        for label, cs in (("sample", sample), ("upper", upper)):
            ctx, user = build_prompt(q["q"], cs)
            row[f"{label}_sources"] = ntok(enc, ctx)
            row[f"{label}_input"] = sys_t + ntok(enc, user)
            row[f"{label}_total"] = row[f"{label}_input"] + overhead + max_completion_tokens
        row["sample_chars"] = len(SYSTEM_V0) + len(build_prompt(q["q"], sample)[1])
        row["pct_window"] = 100 * row["upper_total"] / window if window else None
        qrows.append(row)
    res["budget"] = {"system": sys_t, "questions": qrows, "given": bool(qs), "window": window, "max_output": max_out,
                     "sample_ids": [c["id"] for c in sample], "upper_ids": [c["id"] for c in upper]}
    # ---- 5 output cap and traces
    res["traces"] = trace_stats(traces, enc) if traces else None
    # ---- 6 cost (per model in the sheet; input = counted, as the lesson's K7; "+overhead" = billed estimate)
    n_q = len(qrows)
    mean_in = sum(r["sample_input"] for r in qrows) / n_q
    max_up = max(r["upper_input"] for r in qrows)
    cost = []
    for key, p in sheet["models"].items():
        one_s = (mean_in * p["input"] + max_completion_tokens * p["output"]) / 1e6
        one_u = (max_up * p["input"] + max_completion_tokens * p["output"]) / 1e6
        one_o = ((max_up + overhead) * p["input"] + max_completion_tokens * p["output"]) / 1e6
        q1 = qrows[0]["sample_input"]
        one_q1 = (q1 * p["input"] + max_completion_tokens * p["output"]) / 1e6
        cost.append({"model": key, "one_q1": one_q1,
                     "q1_share": 100 * max_completion_tokens * p["output"] / 1e6 / one_q1, "p_in": p["input"], "p_out": p["output"], "p_cached": p.get("cached_input"),
                     "ratio": p["output"] / p["input"] if p["input"] else None, "one_sample": one_s, "one_upper": one_u,
                     "one_overhead": one_o, "out_share": 100 * max_completion_tokens * p["output"] / 1e6 / one_s,
                     "run_sample": runs * one_s, "run_upper": runs * one_u, "run_overhead": runs * one_o,
                     "generator": key == model_key})
    for r in qrows:
        if mprice:
            r["cost_one"] = (r["sample_input"] * mprice["input"] + max_completion_tokens * mprice["output"]) / 1e6
            r["cost_100"] = 100 * r["cost_one"]
        else:
            r["cost_one"] = r["cost_100"] = None
        r["min_100"] = 100 * r["sample_total"] / tpm if tpm else None
    res["cost"] = {"rows": cost, "mean_input": mean_in, "max_upper_input": max_up, "priced": bool(mprice),
                   "version": sheet.get("price_table_version"), "source": sheet.get("source"), "unit": sheet.get("unit")}
    # ---- 7 time
    per_s = mean_in + overhead + max_completion_tokens
    per_u = max_up + overhead + max_completion_tokens
    res["time"] = {"per_call_sample": per_s, "per_call_upper": per_u, "tokens_sample": runs * per_s,
                   "tokens_upper": runs * per_u, "min_sample": runs * per_s / tpm if tpm else None,
                   "min_upper": runs * per_u / tpm if tpm else None,
                   "pct_tpd": 100 * runs * per_u / tpd if tpd else None,
                   "limits": sheet.get("rate_limits", {}).get(model_key)}
    res["checklist"] = checklist(res, gen, mprice, sheet, today)
    res["recommendation"] = recommend(res)
    return res


# ---------------------------------------------------------------------------------------------------------------- 8 checklist
def checklist(res, gen, mprice, sheet, today):
    s, cor, mix, sp, ch, bud, tr = (res["settings"], res["corpus"], res["mix"], res["specials"], res["chunks"],
                                    res["budget"], res["traces"])
    items = []

    def add(cid, text, verdict, evidence, how):
        items.append({"id": cid, "check": text, "verdict": verdict, "evidence": evidence, "how": how})

    # C1
    how1 = ("Resolve the encoding by name (tiktoken.get_encoding('o200k_harmony') for gpt-oss), or strip the provider "
            "prefix before encoding_for_model; for Claude, count with client.messages.count_tokens.")
    if gen["proxy"]:
        add("C1", "The generator's tokenizer was resolved by encoding name (no provider-prefix KeyError)", ASK,
            f"{gen['how']}. Counts for {gen['model']} below are an o200k proxy, not Claude's count. {gen['naive']}. "
            f"--claude-count {LLMOPS_NOTE}.", how1)
    elif not gen["resolved"]:
        add("C1", "The generator's tokenizer was resolved by encoding name (no provider-prefix KeyError)", BAD,
            f"{gen['how']}. {gen['naive']}.", how1)
    else:
        add("C1", "The generator's tokenizer was resolved by encoding name (no provider-prefix KeyError)", OK,
            f"{gen['how']}. The naive call on the id as written in .env: {gen['naive']}.", how1)
    # C2
    g = cor["rows"][0]
    r = ch["ratio"]
    add("C2", "Measured chars/token for your corpus vs ÷4; flag an error above 20%", BAD if abs(g["err4"]) > 20 else OK,
        f"{g['tokenizer']}: {cor['chars']:,} chars / {g['tokens']:,} tokens = {g['ct']:.2f} chars/token; ÷4 gives "
        f"{g['div4']:,.0f}, an error of {g['err4']:+.0f}%"
        + (f" ({'over' if g['err4'] > 0 else 'under'}-count)" if abs(g["err4"]) > 20 else "")
        + (f". Per chunk: {r['min']:.2f} to {r['max']:.2f} chars/token (median {r['median']:.2f})" if r else "") + ".",
        "Count a sample of your own text with the generator's tokenizer; use the measured ratio, never 4.")
    # C3
    hi = []
    if mix["pct_digits"] > 10:
        hi.append(f"digits {mix['pct_digits']:.1f}% of characters (> 10%)")
    if mix["pct_code"] > 20:
        hi.append(f"code-like lines {mix['pct_code']:.1f}% of lines (> 20%)")
    if mix["pct_nonlatin"] > 5:
        hi.append(f"non-Latin letters {mix['pct_nonlatin']:.1f}% of letters (> 5%)")
    fmt = lambda x: "-" if x is None else f"{x:.2f}"
    add("C3", "Costly content share: digits, code, non-Latin script", BAD if hi else OK,
        ("; ".join(hi) + ". " if hi else "")
        + f"Digits {mix['pct_digits']:.1f}% of characters ({fmt(mix['digit_ct'])} chars/token in number runs); "
          f"code-like lines {mix['code_lines']} of {mix['lines']} ({mix['pct_code']:.1f}%, {fmt(mix['code_ct'])} chars/token); "
          f"non-Latin letters {mix['pct_nonlatin']:.1f}% ({fmt(mix['nonlatin_ct'])} chars/token).",
        "Look at section 2; for a mixed corpus measure chars/token per content type, not one average.")
    # C4
    found = sp["generator"]
    emb = sp["embedder"]
    if found or emb:
        ev = []
        if found:
            ev.append(f"{sum(found.values())} special-token string(s) of {gen['encoding']} in your documents: "
                      + ", ".join(f"`{k}` ×{n}" for k, n in found.items()) + f". {sp['demo']}. This tool counted them "
                      "as ordinary text with disallowed_special=()")
        if emb:
            ev.append("embedder special-token text: " + ", ".join(f"`{k}` ×{n}" for k, n in emb.items())
                      + " (WordPiece reads it as the special token itself)")
        add("C4", "Special-token strings present in your documents (would crash a default counter)", BAD, "; ".join(ev) + ".",
            "Search your text for '<|' ... '|>' and [CLS]/[SEP]; count with encode(text, disallowed_special=()).")
    else:
        add("C4", "Special-token strings present in your documents (would crash a default counter)", OK,
            f"none of {gen['encoding']}'s {len(gen_enc_specials(gen))} special-token strings and no [CLS]/[SEP]-style text found.",
            "Search your text for '<|' ... '|>' and [CLS]/[SEP]; count with encode(text, disallowed_special=()).")
    # C5
    t = ch["truncation"]
    how5 = ("MiniLM: count each chunk with its own WordPiece tokenizer; over 254 text tokens is cut silently. "
            "Cohere embed-v4.0: 128k context, `truncate` default END; check the setting your code sends.")
    if s["embedder"] == "cohere":
        add("C5", "Embedder truncation rate (MiniLM: chunks over 254 text tokens; Cohere: check the `truncate` setting)", ASK,
            f"not measured: fetching Cohere's tokenizer {LLMOPS_NOTE}. Cohere embed-v4.0 reads up to 128k tokens and its "
            "`truncate` default is END (LLMOPS_FOUNDATION §6.2).", how5)
    elif t is None:
        add("C5", "Embedder truncation rate (MiniLM: chunks over 254 text tokens; Cohere: check the `truncate` setting)", ASK,
            "MiniLM's tokenizer did not load from the local cache.", how5)
    else:
        add("C5", "Embedder truncation rate (MiniLM: chunks over 254 text tokens; Cohere: check the `truncate` setting)",
            BAD if t["rate"] > 5 else OK,
            f"{t['n_over']} of {ch['N']} chunks ({t['rate']:.1f}%) exceed {t['limit']} WordPiece text tokens "
            f"({t['max_seq_length']} incl. [CLS]/[SEP]); longest chunk {ch['wp']['max']} tokens"
            + (f"; {t['lost_tokens']:,} tokens ({t['lost_pct']:.1f}%) never reach the vector" if t["n_over"] else "") + ".",
            how5)
    # C6
    w, mo, cap = bud["window"], bud["max_output"], s["cap"]
    worst = max(bud["questions"], key=lambda r: r["upper_total"])
    how6 = "input + template overhead + max_completion_tokens ≤ the model's window (keep a 10% margin); cap ≤ max output."
    if not w:
        add("C6", "Input + output cap fits the window with a margin", ASK,
            f"no window for {res['settings']['generator']} in the price sheet; worst case {worst['upper_total']:,} tokens.", how6)
    else:
        why = []
        if worst["upper_total"] > 0.9 * w:
            why.append(f"worst case {worst['upper_total']:,} tokens > 90% of the {w:,} window")
        if mo and cap > mo:
            why.append(f"cap {cap:,} > max output {mo:,}")
        add("C6", "Input + output cap fits the window with a margin", BAD if why else OK,
            ("; ".join(why) + ". " if why else "")
            + f"Worst case ({worst['id']}, the {s['k']} longest chunks): {worst['upper_input']:,} counted + {s['overhead']} "
              f"overhead + {cap:,} cap = {worst['upper_total']:,} tokens = {100 * worst['upper_total'] / w:.2f}% of {w:,}"
            + (f"; cap {cap:,} ≤ max output {mo:,}." if mo else "."), how6)
    # C7
    how7 = ("Read usage.completion_tokens_details.reasoning_tokens from recorded calls (--traces results.jsonl), or "
            "run --pilot 5 once study/llmops/ exists; the cap must hold reasoning + the visible answer.")
    if tr and tr["completion_p95"] is not None:
        sh = (f"; reasoning share p50 {100 * tr['share_p50']:.0f}%, p95 {100 * tr['share_p95']:.0f}% of completion tokens "
              f"({tr['reasoning_n']} traces report reasoning_tokens)" if tr["share_p95"] is not None else
              "; no reasoning_tokens field in the traces")
        bad7 = tr["completion_p95"] > 0.8 * cap
        add("C7", "Output cap leaves room for reasoning (p95 reasoning share from traces or the pilot)", BAD if bad7 else OK,
            f"recorded completion tokens p95 {tr['completion_p95']:.0f} (max {tr['completion_max']}) vs the planned cap {cap:,}"
            + (" (> 80% of the cap)" if bad7 else " (≤ 80% of the cap)") + sh
            + ". Whether Groq's completion_tokens includes reasoning_tokens is UNVERIFIED; check one live response.", how7)
    else:
        add("C7", "Output cap leaves room for reasoning (p95 reasoning share from traces or the pilot)", ASK,
            "no recorded usage" + (f"; --pilot {LLMOPS_NOTE}" if s["pilot"] else "")
            + f". Your cap is {cap:,} at effort {s['effort'] or 'not sent (server default)'}; Groq's default cap is "
              f"{GROQ_DEFAULT_CAP:,} and the logged O2 call returned an empty answer at a cap of 12.", how7)
    # C8
    how8 = "Count finish_reason == 'length' (Claude: stop_reason 'max_tokens') and empty answers in your logged traces."
    if tr:
        bad8 = tr["length"] > 0 or tr["empty"] > 0
        add("C8", "`finish_reason = length` and empty-answer rates in recorded traces are 0", BAD if bad8 else OK,
            f"{tr['n']} traces: finish_reason " + ", ".join(f"{k_} ×{n}" for k_, n in tr["finishes"].items())
            + f"; cut at the cap {tr['length']}/{tr['n']} ({100 * tr['length'] / tr['n']:.0f}%); empty answers "
              f"{tr['empty']}/{tr['answers_known']} with answer text.", how8)
    else:
        add("C8", "`finish_reason = length` and empty-answer rates in recorded traces are 0", ASK,
            "no traces given (--traces results.jsonl).", how8)
    # C9
    how9 = ("Compare usage.prompt_tokens with your own count of the same messages; the difference is the template "
            "overhead. Record 'messages' or 'counted_prompt_tokens' with each trace.")
    if tr and tr["overhead_n"]:
        bad9 = tr["overhead_max"] > s["overhead"]
        add("C9", "Billed vs counted overhead calibrated from recorded `usage`", BAD if bad9 else OK,
            f"billed − counted over {tr['overhead_n']} traces: median {tr['overhead_p50']:.0f}, max {tr['overhead_max']} "
            f"tokens; this report assumed {s['overhead']}"
            + (f": rerun with --overhead {tr['overhead_max']}." if bad9 else ": the assumption holds."), how9)
    else:
        add("C9", "Billed vs counted overhead calibrated from recorded `usage`", ASK,
            f"not calibrated: this report assumes {s['overhead']} tokens per call, inferred from one logged call (P1 B.3: "
            "78 billed vs 7 counted, a call with no system prompt)"
            + ("; the traces carry no prompt text or counted_prompt_tokens" if tr else "")
            + (f"; --pilot {LLMOPS_NOTE}" if s["pilot"] else "") + ".", how9)
    # C10
    how10 = "Re-read the provider's price page and update price_table_version in your price sheet."
    ver = sheet.get("price_table_version")
    try:
        age = (today - dt.date.fromisoformat(str(ver))).days
    except (TypeError, ValueError):
        age = None
    if age is None:
        add("C10", "Price sheet dated within 30 days", ASK, f"price_table_version {ver!r} is not a date.", how10)
    else:
        miss = "" if res["cost"]["priced"] else f" The sheet has no row for {res['settings']['generator']}."
        add("C10", "Price sheet dated within 30 days", BAD if age > 30 or miss else OK,
            f"price_table_version {ver}, {age} day(s) before {today.isoformat()}"
            + (" (older than 30 days)." if age > 30 else ".") + miss, how10)
    # C11
    tm = res["time"]
    how11 = "Tokens per run = calls × (input + overhead + cap); minutes ≥ tokens ÷ TPM; compare with your plan's daily quota."
    why = []
    if s["tpd"] and tm["tokens_upper"] > s["tpd"]:
        why.append(f"{tm['tokens_upper']:,.0f} tokens > the daily quota {s['tpd']:,}")
    if tm["min_upper"] is not None and tm["min_upper"] > s["max_minutes"]:
        why.append(f"≥ {tm['min_upper']:.1f} min > your limit of {s['max_minutes']:g} min")
    lim = tm["limits"]
    add("C11", "Planned run fits the daily token quota and its minimum time is acceptable", BAD if why else OK,
        ("; ".join(why) + ". " if why else "")
        + f"{s['runs']} calls × up to {tm['per_call_upper']:,.0f} tokens = {tm['tokens_upper']:,.0f} tokens "
          f"({tm['pct_tpd']:.0f}% of {s['tpd']:,} per day); at {s['tpm']:,} TPM ≥ {tm['min_upper']:.1f} min"
        + (f" (rate limits: {lim['note']})." if lim and lim.get("note") else "."), how11)
    # C12
    how12 = ("Groq gpt-oss: temperature 0–2 (0 is sent as 1e-8), reasoning_effort low/medium/high, default medium. "
             "Claude: send no temperature (non-default sampling values return 400); set effort explicitly.")
    prov, eff, temp = res["generator"]["provider"], s["effort"], s["temperature"]
    why = []
    if prov == "anthropic" and temp is not None:
        why.append(f"temperature {temp} would be sent to a Claude model, which rejects it (400)")
    if prov == "groq" and temp is not None and not 0 <= float(temp) <= 2:
        why.append(f"temperature {temp} is outside Groq's 0–2")
    if eff is None:
        why.append("effort not sent: the server default applies (Groq gpt-oss: medium)")
    elif prov in EFFORTS and eff not in EFFORTS[prov]:
        why.append(f"effort {eff!r} is not one of {', '.join(EFFORTS[prov])} for {prov}")
    tnote = ("not sent" if temp is None else f"{temp:g}" + (" (Groq sends 0 as 1e-8)" if prov == "groq" and float(temp) == 0 else ""))
    add("C12", "Sampling parameters are accepted by the provider (no `temperature` sent to current Claude models; effort sent explicitly)",
        BAD if why else (OK if prov in EFFORTS else ASK),
        ("; ".join(why) + ". " if why else "") + f"Flags: temperature {tnote}, effort {eff or 'not sent'}"
        + ("." if prov in EFFORTS else f"; no rules for provider {prov!r} in this tool."), how12)
    return items


def gen_enc_specials(gen):
    return tiktoken.get_encoding(gen["encoding"]).special_tokens_set


# ---------------------------------------------------------------------------------------------------------------- 9 recommendation
RULES = [
    (("C4", "C1"), "fix the counter first",
     "next: resolve the encoding by name and count with encode(text, disallowed_special=()); until then your own "
     "pipeline's counts are unreliable or crash (this report already counts safely)."),
    (("C6",), "reduce k or chunk size, or raise nothing: the call cannot fit",
     "next: lower k or the chunk size until the worst case is under 90% of the window; keep the cap within max output."),
    (("C7", "C8"), "raise `max_completion_tokens` or lower effort",
     "next: raise the cap (Groq's default is 1,024) or use effort low, then re-check finish_reason on recorded calls."),
    (("C5",), "chunks are being truncated: shrink chunks or switch embedder (see P4)",
     "next: shrink chunks below the embedder's limit, or use an embedder that reads longer inputs (P4)."),
    (("C2",), "size chunks in tokens, not characters",
     "next: set chunk sizes in tokens (--unit tokens, a token splitter) or budget with the measured chars/token, never ÷ 4. "
     "Over-counting wastes budget; under-counting overflows it."),
    (("C11",), "split the run or lower volume; check the daily quota",
     "next: spread the calls over more than one day, or run fewer."),
]


def recommend(res):
    c = {i["id"]: i for i in res["checklist"]}
    for ids, verdict, lead in RULES:
        failed = [i for i in ids if c[i]["verdict"] == BAD]
        if failed:
            return {"verdict": verdict, "rule": ids,
                    "reasons": [f"{i}: {c[i]['evidence']}" for i in failed] + [lead]}
    cost = next((r for r in res["cost"]["rows"] if r["generator"]), None)
    s, tm = res["settings"], res["time"]
    reasons = []
    if cost:
        reasons.append(f"{s['runs']} calls cost ≤ {money(cost['run_upper'])} at the cap "
                       f"({money(cost['run_sample'])} with the sample prompts), price sheet {res['cost']['version']}.")
    reasons.append(f"Run time ≥ {tm['min_upper']:.1f} min at {s['tpm']:,} TPM.")
    asks = [i["id"] for i in res["checklist"] if i["verdict"] == ASK]
    if asks:
        reasons.append("still to check by hand: " + ", ".join(asks) + " (see the checklist).")
    return {"verdict": "budget OK", "rule": None, "reasons": reasons}


# ---------------------------------------------------------------------------------------------------------------- report
def _cell(x):
    return str(x).replace("|", "\\|").replace("\n", " ")


def _num(x, d=0):
    """d decimals; for d == 0, one decimal when x is not a whole number (a median or p95 can fall between two)."""
    if x is None:
        return "-"
    if d == 0 and abs(x - round(x)) > 1e-9:
        return f"{x:,.1f}"
    return f"{x:,.{d}f}"


def _n(x, d=0):
    return "-" if x is None else (f"{x:,.{d}f}" if d else f"{round(x):,}")


def render_report(res):
    s, gen, cor, mix, sp, ch, bud, tr, co, tm = (res["settings"], res["generator"], res["corpus"], res["mix"],
                                                  res["specials"], res["chunks"], res["budget"], res["traces"],
                                                  res["cost"], res["time"])
    L = []
    w = L.append
    w("# Token budget check")
    w("")
    w("**What this is:** local token counts for your documents, chunks and prompts, turned into a window check, a cost "
      "estimate and a minimum run time.")
    w("**What this is not:** a bill. Your own counts miss the provider's template tokens (a lower bound on input), and "
      "the output side is the cap (an upper bound). Replace estimates with recorded `usage`.")
    w("")
    rec = res["recommendation"]
    w(f"**Recommendation: {rec['verdict']}** (section 9). Checklist: "
      + " ".join(f"{i['id']} {i['verdict']}" for i in res["checklist"]) + ".")
    w("")
    w(f"Settings: generator `{s['generator']}` (tokenizer `{s['encoding']}`) · {s['chunk_size']}-{'character' if s['unit'] == 'chars' else 'token'} "
      f"chunks, overlap {s['overlap']} · k {s['k']} · `max_completion_tokens` {s['cap']:,} · effort {s['effort'] or 'not sent'} · "
      f"temperature {'not sent' if s['temperature'] is None else format(s['temperature'], 'g')} · overhead {s['overhead']} tokens per call "
      f"(inferred from one logged call, P1 B.3) · embedder {s['embedder']} · {s['runs']} planned calls · {s['tpm']:,} TPM, "
      f"{s['tpd']:,} tokens/day · tiktoken {s['versions']['tiktoken']}, tokenizers {s['versions']['tokenizers']}, "
      f"pymupdf {s['versions']['pymupdf']}.")
    w("Documents: " + "; ".join(f"`{d['name']}` as `{d['id']}` ({d['pages']} page(s), {d['chars']:,} characters)"
                                 for d in res["documents"]) + ".")
    if res["notes"]:
        w("")
        w("Not run (no external call in this version):")
        for n in res["notes"]:
            w(f"- {n}")
    w("")
    # 1
    w("## 1 Corpus ratios per tokenizer")
    w("")
    w(f"Whole corpus: {cor['chars']:,} characters, {cor['bytes']:,} UTF-8 bytes. Tokenizer: {gen['how']}.")
    w(f"Naive call on the id as written (lesson trap K2): `{_cell(gen['naive'])}`")
    if gen["proxy"]:
        w("**Claude:** tiktoken does not know Claude's tokenizer. Every generator count below is an o200k proxy; Claude's "
          "own count comes from its free `count_tokens` endpoint (an estimate itself), which this version cannot call.")
    w("")
    w("| Tokenizer | Role | Tokens | Chars/token | Bytes/token | Chars ÷ 4 | ÷ 4 error |")
    w("|---|---|---|---|---|---|---|")
    for r in cor["rows"]:
        w(f"| `{r['tokenizer']}` | {r['role']} | {r['tokens']:,} | {_n(r['ct'], 2)} | {_n(r['bt'], 2)} | {r['div4']:,.0f} | {r['err4']:+.0f}% |")
    w("")
    w("÷ 4 error = (chars ÷ 4 − tokens) ÷ tokens: positive means ÷ 4 over-counts. WordPiece counts exclude [CLS]/[SEP].")
    w("")
    # 2
    w("## 2 Content mix")
    w("")
    fmt = lambda x: "-" if x is None else f"{x:.2f}"
    w("| Content | Share | Chars/token (generator) | Why it matters |")
    w("|---|---|---|---|")
    w(f"| Digits | {mix['pct_digits']:.1f}% of characters ({mix['digit_runs']:,} number runs) | {fmt(mix['digit_ct'])} | numbers are cut into short groups |")
    w(f"| Code-like lines | {mix['code_lines']:,} of {mix['lines']:,} lines ({mix['pct_code']:.1f}%) | {fmt(mix['code_ct'])} | code has fewer characters per token than prose |")
    w(f"| Non-Latin letters | {mix['nonlatin']:,} of {mix['letters']:,} letters ({mix['pct_nonlatin']:.1f}%) | {fmt(mix['nonlatin_ct'])} | other scripts can cost several times more tokens |")
    w("")
    if mix["code_examples"]:
        w("Code-like line examples (a rough pattern match): " + " · ".join(f"`{_cell(x.strip()[:60])}`" for x in mix["code_examples"]))
        w("")
    if sp["generator"] or sp["embedder"]:
        w("**Special-token strings found** (lesson trap K3): "
          + ", ".join(f"`{k}` ×{n}" for k, n in {**sp["generator"], **sp["embedder"]}.items()) + "."
          + (f" `{_cell(sp['demo'])}`." if sp["demo"] else "")
          + " This report counts them as ordinary text (`disallowed_special=()`).")
    else:
        w(f"Special-token strings: none found (checked `<|…|>` against `{s['encoding']}` and [CLS]/[SEP]/[PAD]/[MASK]/[UNK]).")
    w("")
    # 3
    w("## 3 Chunks: tokens per chunk and embedder truncation")
    w("")
    w(f"{ch['N']} chunks ({s['chunk_size']} {s['unit']}, overlap {s['overlap']}).")
    w("")
    w("| Per chunk | Min | Median | p95 | Max |")
    w("|---|---|---|---|---|")
    for label, d, dd in (("Characters", ch["chars"], 0), (f"`{s['encoding']}` tokens", ch["gen"], 0),
                         ("MiniLM WordPiece text tokens", ch["wp"], 0), ("Chars/token (generator)", ch["ratio"], 2)):
        if d:
            w(f"| {label} | {_num(d['min'], dd)} | {_num(d['median'], dd)} | {_num(d['p95'], dd)} | {_num(d['max'], dd)} |")
    w("")
    t = ch["truncation"]
    if t:
        w(f"MiniLM (`{MINILM}`, cache snapshot `{t['snapshot']}`) reads {t['max_seq_length']} IDs including [CLS] and [SEP], "
          f"so {t['limit']} text tokens. Chunks over the limit: **{t['n_over']} of {ch['N']} ({t['rate']:.1f}%)**. The cut is "
          "silent: no error, no warning (P1_FACTS S6).")
        if t["worst"]:
            w("")
            w("| Chunk | Page | WordPiece tokens | Tokens never embedded |")
            w("|---|---|---|---|")
            for x in t["worst"]:
                w(f"| {x['id']} | {x['page']} | {x['tokens']} | {x['tokens'] - t['limit']} |")
    elif s["embedder"] == "cohere":
        w(f"Cohere embed-v4.0: not measured ({LLMOPS_NOTE}). It reads up to 128k tokens; `truncate` default END.")
    w("")
    # 4
    w("## 4 Prompt budget per question and window fit")
    w("")
    w(f"Prompt = the 06 §3.3 v0 template: system rules ({bud['system']} tokens) + `Sources:` with {s['k']} numbered chunks + "
      "the question. *Sample* = the first k chunks (" + ", ".join(bud["sample_ids"]) + "; as P1_FACTS S9, not a retrieval "
      "result). *Upper* = the k chunks with the most tokens (" + ", ".join(bud["upper_ids"]) + "), the worst case.")
    if not bud["given"]:
        w("No questions given: the question is empty.")
    w("")
    w(f"| Question | Question tokens | Sources (sample) | Input counted (sample) | Input (upper) | + overhead + cap (upper) | % of window | One call | 100 calls | 100 calls ≥ min |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for r in bud["questions"]:
        w(f"| {_cell(r['id'])} | {r['q_tokens']} | {r['sample_sources']} | {r['sample_input']:,} | {r['upper_input']:,} | "
          f"{r['upper_total']:,} | {_n(r['pct_window'], 2)}{'%' if r['pct_window'] is not None else ''} | ≤ {money(r['cost_one'])} | "
          f"≤ {money(r['cost_100'])} | {_n(r['min_100'], 1)} |")
    w("")
    w(f"Window: {_n(bud['window'])} tokens; max output {_n(bud['max_output'])} (price sheet). "
      f"Cost columns: counted sample input + the {s['cap']:,} cap, generator prices; minutes: (sample input + "
      f"{s['overhead']} + {s['cap']:,}) × 100 ÷ {s['tpm']:,} TPM.")
    w("")
    # 5
    w("## 5 Output cap and reasoning")
    w("")
    w(f"`max_completion_tokens` {s['cap']:,} (Groq's default is {GROQ_DEFAULT_CAP:,}; `max_tokens` is deprecated). The cap "
      "holds reasoning tokens **and** the visible answer: if reasoning uses it up, the answer is empty and the call stops "
      f"at the cap (`finish_reason` `length`). Effort: {s['effort'] or 'not sent'}.")
    w("")
    if tr:
        w(f"Recorded traces (`{_cell(tr['path'])}`, {tr['n']} calls):")
        w("")
        w("| Measure | Value |")
        w("|---|---|")
        w("| finish_reason | " + ", ".join(f"{k_} ×{n}" for k_, n in tr["finishes"].items()) + " |")
        w(f"| Cut at the cap | {tr['length']} of {tr['n']} |")
        w(f"| Empty answers | {tr['empty']} of {tr['answers_known']} with answer text |")
        w(f"| Completion tokens p50 / p95 / max | {_n(tr['completion_p50'])} / {_n(tr['completion_p95'])} / {_n(tr['completion_max'])} |")
        w(f"| Reasoning tokens p50 / p95 | {_n(tr['reasoning_p50'])} / {_n(tr['reasoning_p95'])} ({tr['reasoning_n']} traces report them) |")
        if tr["share_p95"] is not None:
            w(f"| Reasoning share of completion p50 / p95 | {100 * tr['share_p50']:.0f}% / {100 * tr['share_p95']:.0f}% |")
        w(f"| Billed − counted prompt tokens (overhead) | " + (f"median {tr['overhead_p50']:.0f}, max {tr['overhead_max']} over {tr['overhead_n']}" if tr["overhead_n"] else "not measurable (no prompt text recorded)") + " |")
        if tr["caps"]:
            w(f"| Caps recorded | {', '.join(map(str, tr['caps']))} |")
    else:
        w("No recorded usage: run with `--traces results.jsonl` (your logged responses). A pilot (`--pilot 5`) "
          f"{LLMOPS_NOTE}.")
    w("")
    # 6
    w("## 6 Cost")
    w("")
    w(f"Price sheet `price_table_version` {co['version']} ({co['unit']}; {co['source']}). Output is billed at the cap "
      f"({s['cap']:,} tokens), so every figure is an upper bound on output. *Sample*: mean counted input over your "
      f"questions ({co['mean_input']:,.1f} tokens). *Upper*: the longest prompt ({co['max_upper_input']:,} tokens). "
      f"*+ overhead*: upper + {s['overhead']} template tokens.")
    w("")
    q1 = bud["questions"][0]
    w(f"| Model | In / out per 1M | Out ÷ in | One call, {_cell(q1['id'])} ({q1['sample_input']:,} in) | Output share | "
      f"{s['runs']} calls, {_cell(q1['id'])} | {s['runs']} calls (sample mean) | {s['runs']} calls (upper) | {s['runs']} calls (+ overhead) |")
    w("|---|---|---|---|---|---|---|---|---|")
    runs_ = s["runs"]
    for r in co["rows"]:
        name = f"`{r['model']}`" + (" (generator)" if r["generator"] else "") + (" *o200k proxy count*" if r["model"].startswith("anthropic:") else "")
        w(f"| {name} | {price(r['p_in'])} / {price(r['p_out'])} | {_n(r['ratio'], 1)}× | ≤ {money(r['one_q1'])} | {r['q1_share']:.1f}% | "
          f"≤ {money(runs_ * r['one_q1'])} | ≤ {money(r['run_sample'])} | ≤ {money(r['run_upper'])} | ≤ {money(r['run_overhead'])} |")
    w("")
    gp = next((r for r in co["rows"] if r["generator"]), None)
    if any(r["model"].startswith("anthropic:") for r in co["rows"]):
        w("Claude rows reuse the generator-side counts (an o200k proxy); Claude's own count comes from `count_tokens`.")
        w("")
    if gp and gp["p_cached"]:
        w(f"Cached input is ${gp['p_cached']} per 1M on this sheet; this estimate assumes no cache hits.")
        w("")
    # 7
    w("## 7 Run time")
    w("")
    w(f"Minimum time = tokens ÷ tokens per minute. Per call: input + {s['overhead']} overhead + {s['cap']:,} cap.")
    w("")
    w("| Plan | Tokens per call | Tokens per run | Minutes at TPM | Share of the daily quota |")
    w("|---|---|---|---|---|")
    w(f"| {s['runs']} calls, sample prompts | {tm['per_call_sample']:,.0f} | {tm['tokens_sample']:,.0f} | ≥ {tm['min_sample']:.1f} | {100 * tm['tokens_sample'] / s['tpd']:.0f}% |")
    w(f"| {s['runs']} calls, upper | {tm['per_call_upper']:,.0f} | {tm['tokens_upper']:,.0f} | ≥ {tm['min_upper']:.1f} | {tm['pct_tpd']:.0f}% |")
    w("")
    if tm["limits"]:
        w(f"Rate limits for this model on the sheet: {tm['limits'].get('tpm'):,} TPM, {tm['limits'].get('tpd'):,} tokens/day ({tm['limits'].get('note')}).")
        w("")
    # 8
    w("## 8 Checklist")
    w("")
    w("✓ = no problem found · ✗ = a problem found on your data · ? = check by hand (the evidence and *how to check* help).")
    w("")
    w("| # | Check | Verdict | Evidence | How to check |")
    w("|---|---|---|---|---|")
    for i in res["checklist"]:
        w(f"| {i['id']} | {_cell(i['check'])} | {i['verdict']} | {_cell(i['evidence'])} | {_cell(i['how'])} |")
    w("")
    # 9
    w("## 9 Recommendation")
    w("")
    w(f"**{rec['verdict']}**" + (f" (rule: {' or '.join(rec['rule'])} failed; first match wins)" if rec["rule"] else ""))
    w("")
    for r in rec["reasons"]:
        w(f"- {_cell(r)}")
    w("")
    w("Order of the rules: C4/C1 counter → C6 window → C7/C8 output cap → C5 truncation > 5% → C2 ÷4 error > 20% → "
      "C11 quota/time → budget OK.")
    w("")
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Does each call fit, what will it cost, how long will a run take? "
                                             "Writes a Markdown report. No API calls.")
    ap.add_argument("--docs", nargs="+", required=True, help="files or folders (.pdf, .txt, .md)")
    ap.add_argument("--doc-ids", default="", help="comma-separated doc ids for the source headers (default: file stems)")
    ap.add_argument("--questions", help=".txt (one per line, optional 'ID | question') or .jsonl ({\"id\", \"q\"})")
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--unit", choices=("chars", "tokens"), default="chars")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--generator", default="groq:openai/gpt-oss-20b", help="provider:model, e.g. anthropic:claude-haiku-5-5")
    ap.add_argument("--encoding", help="tiktoken encoding name, overrides the lookup")
    ap.add_argument("--max-completion-tokens", type=int, default=512)
    ap.add_argument("--effort", default="low", help="low / medium / high (Claude also max); 'none' = not sent")
    ap.add_argument("--temperature", default="auto", help="a number, 'none' (not sent) or 'auto' (Groq 0, Claude not sent)")
    ap.add_argument("--overhead", type=int, default=71, help="template tokens per call (71: inferred from one logged call)")
    ap.add_argument("--embedder", choices=("minilm", "cohere"), default="minilm")
    ap.add_argument("--prices", help="price sheet JSON (default: the built-in sheet dated 2026-10-17)")
    ap.add_argument("--tpm", type=int, default=8000)
    ap.add_argument("--tpd", type=int, default=200000)
    ap.add_argument("--runs", type=int, default=100, help="planned number of calls")
    ap.add_argument("--max-minutes", type=float, default=60.0, help="longest acceptable run time (C11)")
    ap.add_argument("--traces", help="recorded responses, .jsonl (usage, finish_reason, answer)")
    ap.add_argument("--pilot", type=int, nargs="?", const=5, help="N recorded calls (needs study/llmops/; not built)")
    ap.add_argument("--claude-count", action="store_true", help="Claude count_tokens (needs study/llmops/; not built)")
    ap.add_argument("--today", help=argparse.SUPPRESS)
    ap.add_argument("--report", help="write the Markdown report here (default: print it)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    temp = a.temperature if a.temperature in ("auto",) else (None if a.temperature == "none" else float(a.temperature))
    for flag, on in (("--pilot", a.pilot), ("--claude-count", a.claude_count), ("--embedder cohere", a.embedder == "cohere")):
        if on:
            print(f"{flag}: {LLMOPS_NOTE}.", file=sys.stderr)
    res = run_check(a.docs, a.questions, [x.strip() for x in a.doc_ids.split(",") if x.strip()] or None, a.chunk_size,
                    a.overlap, a.unit, a.k, a.generator, a.encoding, a.max_completion_tokens, a.effort, temp, a.overhead,
                    a.embedder, a.prices, a.tpm, a.tpd, a.runs, a.max_minutes, a.traces, a.pilot, a.claude_count, a.today)
    text = render_report(res)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8")
        g = res["corpus"]["rows"][0]
        print(f"chunks {res['chunks']['N']}, {g['tokenizer']} {g['ct']:.2f} chars/token")
        for i in res["checklist"]:
            print(f"{i['id']:4s} {i['verdict']}  {i['check']}")
        print(f"recommendation: {res['recommendation']['verdict']}")
        print(f"report: {a.report}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
