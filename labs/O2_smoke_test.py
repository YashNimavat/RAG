"""O2 smoke test (approval gate B items E-2 and E-3). Never prints secrets.

Checks:
1. A local embedding (fallback model) and a cosine top-1.
2. A BM25 top-1.
3. One Cohere embed call (default embedder, D-03).
4. One Groq chat call (generation provider, D-04).

Run:  uv run python labs/O2_smoke_test.py
Writes progress/O2_smoke_test_<date>.json (model ids, limits, latencies; no keys).
"""
import datetime, json, os, pathlib, sys, time

import numpy as np
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]
ONLY = set(sys.argv[1:])   # optional: run a subset, e.g. `... O2_smoke_test.py groq` (local, bm25, cohere, groq)
run = lambda name: not ONLY or name in ONLY


class SkipCheck(Exception):
    pass
load_dotenv(ROOT / ".env")
today = datetime.date.today().isoformat()
report = {"date": today, "python": sys.version.split()[0], "checks": {}}

docs = ["BM25 ranks documents by term frequency and inverse document frequency.",
        "Cosine similarity compares the angle between two embedding vectors.",
        "The Paris Agreement aims to limit global warming to well below 2 degrees Celsius."]
query = "How do you measure the angle between two vectors?"


def ok(name, **info):
    report["checks"][name] = {"status": "PASS", **info}
    print(f"[PASS] {name}: " + ", ".join(f"{k}={v}" for k, v in info.items()))


def fail(name, err):
    report["checks"][name] = {"status": "FAIL", "error": f"{type(err).__name__}: {err}"[:300]}
    print(f"[FAIL] {name}: {type(err).__name__}: {str(err)[:200]}")


# 1. local embedding fallback + cosine top-1
try:
    if not run("local"):
        raise SkipCheck
    import torch
    from sentence_transformers import SentenceTransformer
    t0 = time.perf_counter()
    m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    D = m.encode(docs, normalize_embeddings=True)
    q = m.encode([query], normalize_embeddings=True)[0]
    scores = D @ q                                   # unit vectors: dot product = cosine
    top = int(np.argmax(scores))
    assert top == 1, f"expected doc 1, got {top}"
    ok("local_embedding_cosine_top1", model="all-MiniLM-L6-v2", max_seq_length=m.max_seq_length,
       dim=int(D.shape[1]), top1=top, score=round(float(scores[top]), 3), torch=torch.__version__,
       cuda=torch.cuda.is_available(), seconds=round(time.perf_counter() - t0, 1))
except SkipCheck:
    pass
except Exception as e:
    fail("local_embedding_cosine_top1", e)

# 2. BM25 top-1
try:
    if not run("bm25"):
        raise SkipCheck
    from rank_bm25 import BM25Okapi
    bm = BM25Okapi([d.lower().split() for d in docs])
    s = bm.get_scores("paris agreement warming".split())
    top = int(np.argmax(s))
    assert top == 2, f"expected doc 2, got {top}"
    ok("bm25_top1", top1=top, score=round(float(s[top]), 3))
except SkipCheck:
    pass
except Exception as e:
    fail("bm25_top1", e)

# 3. Cohere embed (one call)
try:
    if not run("cohere"):
        raise SkipCheck
    import cohere
    assert os.getenv("COHERE_API_KEY"), "COHERE_API_KEY missing in .env"
    co = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])
    available = []
    try:
        lst = co.models.list(endpoint="embed")
        available = [(x.name, getattr(x, "context_length", None)) for x in (lst.models or [])]
    except Exception as e_list:
        available = [("models.list failed", str(e_list)[:80])]
    names = [n for n, _ in available]
    model = next((n for n in ("embed-v4.0", "embed-english-v3.0") if n in names), "embed-english-v3.0")
    t0 = time.perf_counter()
    r = co.embed(texts=docs[:2], model=model, input_type="search_document", embedding_types=["float"])
    vec = r.embeddings.float_[0]
    ok("cohere_embed", model=model, dim=len(vec), input_type="search_document",
       context_length=dict(available).get(model), seconds=round(time.perf_counter() - t0, 2),
       embed_models_listed=len(available))
    report["checks"]["cohere_embed"]["embed_models"] = available[:20]
except SkipCheck:
    pass
except Exception as e:
    fail("cohere_embed", e)

# 4. Groq chat (one call)
try:
    if not run("groq"):
        raise SkipCheck
    from groq import Groq
    assert os.getenv("GROQ_API_KEY"), "GROQ_API_KEY missing in .env"
    g = Groq(api_key=os.environ["GROQ_API_KEY"])
    ids = sorted(x.id for x in g.models.list().data)
    model = os.getenv("GROQ_MODEL_ID") or next(
        (i for i in ("llama-3.1-8b-instant", "llama-3.3-70b-versatile") if i in ids),
        next(i for i in ids if "whisper" not in i and "guard" not in i))
    extra = {"reasoning_effort": "low"} if "gpt-oss" in model else {}   # reasoning models spend tokens thinking first
    t0 = time.perf_counter()
    c = g.chat.completions.create(model=model, temperature=0, max_tokens=256, **extra,
                                  messages=[{"role": "user", "content": "Reply with exactly: smoke test ok"}])
    text = (c.choices[0].message.content or "").strip()
    assert "smoke test ok" in text.lower(), f"unexpected reply {text[:60]!r} (finish_reason={c.choices[0].finish_reason})"
    ok("groq_chat", model=model, reply=text[:40], prompt_tokens=c.usage.prompt_tokens,
       completion_tokens=c.usage.completion_tokens, seconds=round(time.perf_counter() - t0, 2),
       models_listed=len(ids))
    report["checks"]["groq_chat"]["models_available"] = ids
except SkipCheck:
    pass
except Exception as e:
    fail("groq_chat", e)

out = ROOT / "progress" / f"O2_smoke_test_{today}.json"
if ONLY and out.exists():   # subset run: merge into the existing report
    prev = json.loads(out.read_text(encoding="utf-8"))
    prev["checks"].update(report["checks"]); report = prev
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
n_pass = sum(v["status"] == "PASS" for v in report["checks"].values())
print(f"\n{n_pass}/{len(report['checks'])} checks passed -> {out.relative_to(ROOT)}")
