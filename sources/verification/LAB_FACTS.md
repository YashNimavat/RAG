# LAB_FACTS — what the C2 chunking lesson can rely on (lab-verified)

Verifier run date: **2026-10-08**. Each fact below came from running code, except where it is labelled STATIC (read from source) or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11, AMD64). It runs in an isolated uv venv at `scratchpad/labenv`.
  - Every script ran with `python -I` from `scratchpad/labscripts/`, with data paths passed as arguments.
- **Library versions.**

  | Package | Version |
  |---|---|
  | langchain-text-splitters | 1.1.3 |
  | langchain-core | 1.6.7 |
  | langchain-community | 0.4.2 (it emits a "being sunset" DeprecationWarning on import) |
  | pypdf | 6.19.0 |
  | pymupdf | 1.28.2 |
  | tiktoken | 0.14.0 |
  | numpy | 2.5.3 |
  | llama-index-core | 0.14.25 |
  | llama-index-readers-file | 0.7.0 |
  | tokenizers | 0.23.2 |

  - `llama-index-readers-file` and `tokenizers` go beyond the requested install list. I added them, inside labenv only, so I could:
    - reproduce `SimpleDirectoryReader` PDF loading;
    - count tokens with the embedding models' own WordPiece tokenizers instead of a proxy.
  - No torch, no sentence-transformers, and no LLM or API calls were used. LlamaIndex ran with `MockLLM` and `MockEmbedding`.
- **Corpus.** `C:/Yash/New-Work/RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`.
  - SHA-256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`.
  - It comes from the repo pinned at commit `009adba2…`.
- **Hugging Face files.** I downloaded these with curl into `scratchpad/hfdl/` (untrusted data; only parsed as JSON, text or tokenizer).
  - Revisions at fetch time, from `https://huggingface.co/api/models/<id>` → `sha`:
    - `sentence-transformers/all-MiniLM-L6-v2` @ `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
    - `BAAI/bge-small-en-v1.5` @ `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- **Scripts** (all in `C:/Users/Yash/AppData/Local/Temp/claude/C--Users-Yash/3dbbca21-771e-4b2e-ab07-8e5a8ab0a107/scratchpad/labscripts/`). Each has a saved stdout file named `out_<name>.txt`.

  | Script | What it checks |
  |---|---|
  | `lab01_03_math.py` | Items 1–3 |
  | `lab04_06_libs.py` | Items 4–6 |
  | `lab04b_equal_overlap.py` | Behaviour when overlap equals size |
  | `lab05b_choose_chunk_size_paths.py` | What choose_chunk_size indexes |
  | `lab05c_sort_order.py` | File sort order |
  | `lab07_climate.py` | Item 7 |
  | `lab08_worked_example.py` | Item 8 |
  | `chunklib.py` | Minimal implementation |
  | `lab09_minimal_impl.py`, `lab09b_trace23.py` | Item 9 |
  | `lab10_wordpiece.py` | Items 7 and 10, WordPiece counts |

- **Re-run** (Git Bash):
  ```bash
  S=C:/Users/Yash/AppData/Local/Temp/claude/C--Users-Yash/3dbbca21-771e-4b2e-ab07-8e5a8ab0a107/scratchpad
  PY=$S/labenv/Scripts/python.exe; PDF=C:/Yash/New-Work/RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf
  cd $S/labscripts
  $PY -I lab01_03_math.py; $PY -I lab04_06_libs.py; $PY -I lab04b_equal_overlap.py
  $PY -I lab05b_choose_chunk_size_paths.py C:/Yash/New-Work/RAG/upstream/RAG_Techniques/data; $PY -I lab05c_sort_order.py
  $PY -I lab07_climate.py $PDF; $PY -I lab08_worked_example.py; $PY -I lab09_minimal_impl.py $PDF; $PY -I lab09b_trace23.py
  $PY -I lab10_wordpiece.py $PDF $S/hfdl/sentence-transformers_all-MiniLM-L6-v2__tokenizer.json $S/hfdl/BAAI_bge-small-en-v1.5__tokenizer.json
  ```

## Verdicts on SAMPLE_LESSON_SPEC claims (read this first)

| # | Spec claim | Verdict | Correct statement for the lesson |
|---|---|---|---|
| 1 | P(contained) = min(1,(S−F+1)/(S−O)); 0.501 / 0.626 / 0.835 | **CONFIRMED** | The brute force matches exactly for interior start positions. Near the document edges the probability is slightly higher (§1). |
| 1b | A span is always contained iff F ≤ O+1 | **CONFIRMED** | F=201 → 1.0 and F=202 → 0.99875 at S=1000, O=200. |
| 2 | #chunks = ceil((L−O)/(S−O)) for L>S; storage ≈ S/(S−O) | **CONFIRMED** | 0 mismatches over about 40k lengths. Storage approaches S/(S−O) from below (1.247 vs 1.25 for L=73,536). |
| 3 | Dilution toy cosines 1.000/0.707/0.447/0.316; competitor 0.600 wins for n≥2 | **CONFIRMED** | n=4 gives 0.243. |
| 4a | Default separators `["\n\n","\n"," ",""]`; length_function=len | **CONFIRMED** | The defaults also include chunk_size=4000, chunk_overlap=200, keep_separator=True for the recursive splitter, and strip_whitespace=True. |
| 4b | Actual overlap ≤ chunk_overlap and varies | **CONFIRMED** | With overlap=40 the achieved overlaps were 39, 39, 28, 39 (§4). |
| 4c | "chunk_overlap ≥ chunk_size → error (LangChain raises ValueError)" | **CORRECTED** | Only `chunk_overlap > chunk_size` raises. Equality is accepted and produces near-duplicate chunks that advance one piece at a time (§4). A negative overlap raises a different ValueError. |
| 5a | "LlamaIndex SentenceSplitter raises" when overlap ≥ size | **CORRECTED** | It raises only when overlap > size. `SentenceSplitter(chunk_size=200)`, which keeps the default overlap of 200, is accepted. |
| 5b | choose_chunk_size.py L48 crashes for 128 | **CONFIRMED (ran)** | `SentenceSplitter(chunk_size=128)` raises ValueError because the default overlap is 200. chunk_size=256 does **not** crash, but it runs with overlap 200 (78% of the chunk). |
| 5c | Settings.chunk_size is in tokens | **CONFIRMED** | The default tokenizer is tiktoken `cl100k_base`. The notebook path (cell 10) runs without error. |
| 6 | Custom prompt registered under "your_prompt_key" is silently ignored | **CONFIRMED (ran)** | It raised no exception, returned None, and changed no template. A positive control using `eval_template` does change the prompt. |
| 7a | PyPDFLoader `page` metadata is 0-based | **CONFIRMED** | The first doc has `page: 0, page_label: '1'`. |
| 7b | encode_pdf chunks never cross pages, so overlap cannot rescue a sentence cut by a page break | **CONFIRMED with a real example** | See §7. The PPP sentence crosses PDF pages 12→13 and no per-page chunk contains it whole. |
| 7c | "~4x" chars-per-token difference | **CORRECTED for this corpus** | 5.57 chars/token (cl100k), 5.07 (gpt2) and 6.20 (BERT WordPiece). On this corpus "1000 tokens" is about 5.6× "1000 characters". The ratio depends on the corpus. |
| 10 | max_seq_length of all-MiniLM-L6-v2 / bge-small-en-v1.5 | **VERIFIED from config** | 256 / 512 WordPiece tokens. MiniLM uses mean pooling and bge uses CLS pooling, and both normalize. Longer input is truncated (§10). |

New facts the lesson should use:

- On the climate PDF with the repo default of 1000/200 characters, **no chunk exceeds 256 WordPiece tokens** (the maximum is 182). Truncation is therefore *not* a live failure for v0 on corpus D. It does appear at 2000-character chunks, where 32 of 65 chunks exceed 256 tokens for MiniLM (§7).
- **choose_chunk_size indexes more than the climate PDF.** On Windows, `documents[0:20]` is 5 non-PDF files (customers-100.csv, the full Nike annual report, 3 Q/A JSON files) plus climate pages 1–15. On POSIX the order differs (§5).
- **Half of the climate PDF's page breaks orphan a heading.** Of 32 page breaks, 16 leave a section heading at the bottom of page N with its body on page N+1, and 8 cut a sentence mid-way (§7).

---

## 1. Boundary-containment probability (fixed windows)

**Model.**
- Chunk k covers the characters `[k·(S−O), k·(S−O)+S)`.
- A fact is the span `[p, p+F)` with F ≤ S.
- Containment in chunk k requires `0 ≤ p − k·stride ≤ S−F`.
- For p uniform modulo the stride, P = #{r ∈ [0, stride) : r ≤ S−F} / stride = min(1, (S−F+1)/(S−O)).
- P is 1 for every p iff S−F+1 ≥ S−O, that is iff **F ≤ O+1**.

**Code (excerpt of `lab01_03_math.py`):**
```python
def fixed_window_spans(L, S, O):
    stride = S - O
    spans, start = [], 0
    while True:
        end = min(start + S, L)
        spans.append((start, end))
        if end >= L:
            break
        start += stride
    return spans

def p_contained_formula(S, O, F):
    return min(1.0, (S - F + 1) / (S - O))

def p_contained_exhaustive(L, S, O, F):          # every start position, every chunk
    spans = fixed_window_spans(L, S, O)
    hit = total = 0
    for p in range(0, L - F + 1):
        total += 1
        hit += any(a <= p and p + F <= b for a, b in spans)
    return hit / total, hit, total
# brute(interior): same test over start positions p in [S, S + n*stride) (whole number of strides, no edge effects)
```
**Output:**
```
S=1000 F=500 O=0: formula=0.501000  brute(interior,L=200000)=0.501000 (98697/197000)  exhaustive(all starts,L=20000)=0.513820 (10020/19501)
S=1000 F=500 O=200: formula=0.626250  brute(interior,L=200000)=0.626250 (123246/196800)  exhaustive(all starts,L=20000)=0.632019 (12325/19501)
S=1000 F=500 O=400: formula=0.835000  brute(interior,L=200000)=0.835000 (164328/196800)  exhaustive(all starts,L=20000)=0.837547 (16333/19501)
Guarantee threshold check (P==1 iff F <= O+1), S=1000, O=200:
  F=200: formula=1.000000 brute=1.000000
  F=201: formula=1.000000 brute=1.000000
  F=202: formula=0.998750 brute=0.998750
  F=250: formula=0.938750 brute=0.938750
```
**Conclusion.**
- The formula is exact for start positions away from the document edges.
- Over a whole finite document the rate is slightly higher (0.5138, 0.6320, 0.8375 at L=20,000), because the last, shorter window adds coverage near the end.
- The lesson's numbers are confirmed: 501/1000 = 0.501, 501/800 = 0.626, 501/600 = 0.835.
- Caveat for the lesson: this model is for *fixed character windows*. Recursive splitters place boundaries at separators and get their overlap from whole pieces, so the formula is only an approximation for them.

**Confidence:** high (exact enumeration).

## 2. Chunk-count formula

**Code:** `fixed_window_spans` (above), compared with `math.ceil((L - O) / (S - O))` for every L from S+1 to 20S−1.

**Output:**
```
S=1000 O=200: checked L=1001..19999, mismatches=0
S=300 O=60: checked L=301..5999, mismatches=0
S=300 O=0: checked L=301..5999, mismatches=0
S=500 O=100: checked L=501..9999, mismatches=0
  L=1001 S=1000 O=200: impl=2 formula=2 stored_chars/L=1.200 (S/(S-O)=1.250)
  L=1800 S=1000 O=200: impl=2 formula=2 stored_chars/L=1.111 (S/(S-O)=1.250)
  L=1801 S=1000 O=200: impl=3 formula=3 stored_chars/L=1.222 (S/(S-O)=1.250)
  L=5000 S=1000 O=200: impl=6 formula=6 stored_chars/L=1.200 (S/(S-O)=1.250)
  L=73536 S=1000 O=200: impl=92 formula=92 stored_chars/L=1.247 (S/(S-O)=1.250)
```
The implementation emits windows until one reaches L; the final window may be short.

**Conclusion.**
- The formula is exact for this implementation. For L ≤ S there is 1 chunk.
- The storage multiplier S/(S−O) is an upper-bound asymptote, not exact for short documents.
- The 23-character fixtures in §9 also match the formula: ceil(20/7) = 3 and ceil(19/4) = 5.

**Confidence:** high.

## 3. Dilution toy model (label it a simplification: real encoders do not average sentence vectors)

**Code (condensed from `lab01_03_math.py`; the full loop is in the script):**
```python
q = np.array([1.0, 0.0]); r, u = np.array([1.0, 0.0]), np.array([0.0, 1.0]); comp = np.array([0.6, 0.8])
cos = lambda a, b: float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
for n in range(0, 5):
    chunk = np.mean(np.vstack([r] + [u] * n), axis=0)
    print(n, chunk, cos(q, chunk), 1 / math.sqrt(1 + n * n), cos(q, chunk) > cos(q, comp))
```
**Output:**
```
competitor c=[0.6,0.8]: cos(q,c)=0.600
n=0 off-topic: chunk=[1.0, 0.0] cos=1.000 1/sqrt(1+n^2)=1.000 beats_competitor=True
n=1 off-topic: chunk=[0.5, 0.5] cos=0.707 1/sqrt(1+n^2)=0.707 beats_competitor=True
n=2 off-topic: chunk=[0.3333, 0.6667] cos=0.447 1/sqrt(1+n^2)=0.447 beats_competitor=False
n=3 off-topic: chunk=[0.25, 0.75] cos=0.316 1/sqrt(1+n^2)=0.316 beats_competitor=False
n=4 off-topic: chunk=[0.2, 0.8] cos=0.243 1/sqrt(1+n^2)=0.243 beats_competitor=False
```
**Conclusion.**
- cos = 1/√(1+n²) is confirmed. The mean is (1, n)/(n+1), and the cosine is invariant to scale.
- The chunk that contains the answer loses to the partial-topic competitor from n = 2 onward.
- This is a *toy illustration*, not a claim about MiniLM or bge, where mean or CLS pooling acts over contextual token states.

**Confidence:** high, for the toy only.

## 4. LangChain `RecursiveCharacterTextSplitter` behaviour (langchain-text-splitters 1.1.3)

**Code (excerpt of `lab04_06_libs.py`):**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters.base import TextSplitter
print(inspect.signature(TextSplitter.__init__)); print(inspect.signature(RecursiveCharacterTextSplitter.__init__))
default = RecursiveCharacterTextSplitter()
print(default._separators, default._chunk_size, default._chunk_overlap, default._length_function is len)
sp = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=40, length_function=len, add_start_index=True)
docs = sp.create_documents([SAMPLE])     # SAMPLE: 388-char original paragraph about overlap (see script)
# overlap_with_prev = previous chunk end offset - this chunk start offset (offsets from start_index)
for cs, co in ((100, 100), (100, 150), (100, 99), (100, -1)):
    try: RecursiveCharacterTextSplitter(chunk_size=cs, chunk_overlap=co)
    except Exception as ex: print(type(ex).__name__, ex)
```
**Output:**
```
TextSplitter.__init__ signature: (self, chunk_size: 'int' = 4000, chunk_overlap: 'int' = 200, length_function: 'Callable[[str], int]' = <built-in function len>, keep_separator: "bool | Literal['start', 'end']" = False, add_start_index: 'bool' = False, strip_whitespace: 'bool' = True) -> 'None'
RecursiveCharacterTextSplitter.__init__ signature: (self, separators: 'list[str] | None' = None, keep_separator: "bool | Literal['start', 'end']" = True, is_separator_regex: 'bool' = False, **kwargs: 'Any') -> 'None'
default _separators: ['\n\n', '\n', ' ', '']
default _chunk_size, _chunk_overlap: 4000 200
default _length_function is len: True

SAMPLE length: 388
chunk 0: [0,116) len=116 overlap_with_prev=None | 'Retrieval quality depends on what each vector represents. A chunk that mixes three topics produces an embedding that'
chunk 1: [77,195) len=118 overlap_with_prev=39 | 'three topics produces an embedding that sits between them. A chunk that is too short loses the sentence that names its'
chunk 2: [156,274) len=118 overlap_with_prev=39 | 'short loses the sentence that names its subject. Overlap repeats text across neighbouring chunks so that a boundary is'
chunk 3: [246,363) len=117 overlap_with_prev=28 | 'chunks so that a boundary is less likely to cut a short fact in half. It does not guarantee anything for facts longer'
chunk 4: [324,388) len=64 overlap_with_prev=39 | 'not guarantee anything for facts longer than the overlap itself.'

Overlap/size validation:
  chunk_size=100 chunk_overlap=100: OK (no exception)
  chunk_size=100 chunk_overlap=150: ValueError: Got a larger chunk overlap (150) than chunk size (100), should be smaller.
  chunk_size=100 chunk_overlap=99: OK (no exception)
  chunk_size=100 chunk_overlap=-1: ValueError: chunk_overlap must be >= 0, got -1

Oversized single word (no separator can split it) with chunk_size=10:
   ['short', 'xxxxxxxxx', 'xxxxxxxxxx', 'xxxxxx', 'tail']
```
**What happens when overlap equals size** (`lab04b_equal_overlap.py`; each case ran in a subprocess with a 60 s timeout; TEXT is 60 words "word000 … word059", 479 characters):
```
LangChain size=40 overlap=40: 56 chunks; first 3 = ['word000 word001 word002 word003 word004', 'word001 word002 word003 word004 word005', 'word002 word003 word004 word005 word006']
LlamaIndex size=40 overlap=40: 41 chunks; first 2 = ['word000 word001 ... word019', 'word001 word002 ... word020']
```
The LlamaIndex chunk texts are elided here; the full text is in `out_lab04b.txt`.

**Source (STATIC, the installed package).**
- `langchain_text_splitters/base.py` validates in `__init__`:
  - `chunk_size <= 0` → ValueError (L88–L90)
  - `chunk_overlap < 0` → ValueError (L91–L93)
  - `chunk_overlap > chunk_size` → ValueError (L94–L99)
- `_merge_splits` (around L167–L210) drops pieces from the front of the current chunk while `total > chunk_overlap`, or while the next piece would not fit. So the carried-over overlap consists of **whole trailing pieces whose combined length is ≤ chunk_overlap**.
- These line numbers refer to the installed 1.1.3 file, not to the repo.

**Conclusion.**
- **Defaults:** separators `["\n\n", "\n", " ", ""]`, `length_function=len` (characters), chunk_size 4000, chunk_overlap 200, `keep_separator=True` for the recursive splitter, `strip_whitespace=True`.
  - The repo always passes 1000/200 explicitly (`helper_functions.py:L66-L68`).
- **Achieved overlap is ≤ the requested overlap and varies:** 39, 39, 28, 39 for a request of 40, because the overlap is built from whole word pieces and the joining space is stripped.
- **Exact exception messages:**
  - `ValueError: Got a larger chunk overlap (150) than chunk size (100), should be smaller.`
  - `ValueError: chunk_overlap must be >= 0, got -1`
- **Correction to the spec:** `chunk_overlap == chunk_size` does *not* raise. It terminates but produces about one chunk per word (56 chunks for 60 words). The achieved overlap is still < chunk_size, because one piece must be dropped for the next to fit.
- If no separator can split a piece, the `""` separator splits it into characters, so pieces never exceed chunk_size.

**Confidence:** high (ran, and matches source).

## 5. LlamaIndex `SentenceSplitter`, `Settings`, and choose_chunk_size (llama-index-core 0.14.25)

**Code (excerpts of `lab04_06_libs.py` and `lab05b_choose_chunk_size_paths.py`):**
```python
ss = SentenceSplitter(); print(ss.chunk_size, ss.chunk_overlap)
for cs in (128, 200, 201, 256):
    try: x = SentenceSplitter(chunk_size=cs); print("OK", x.chunk_overlap)
    except Exception as ex: print(type(ex).__name__, ex)
tok = get_tokenizer(); print(tok)                       # llama_index.core.utils.get_tokenizer
Settings.chunk_size = 128; Settings.chunk_overlap = 128 // 5   # notebook cell 10 order
# --- lab05b: real data dir, MockLLM + MockEmbedding(embed_dim=8), no API calls
documents = SimpleDirectoryReader(data_dir).load_data(); eval_documents = documents[0:20]
for cs in (128, 256):          # notebook path (cell 10)
    Settings.chunk_size = cs; Settings.chunk_overlap = cs // 5
    idx = VectorStoreIndex.from_documents(eval_documents)
for cs in (128, 256):          # script path (choose_chunk_size.py L48)
    splitter = SentenceSplitter(chunk_size=cs)
    idx = VectorStoreIndex.from_documents(eval_documents, transformations=[splitter])
```
**Output (`lab04_06_libs.py`):**
```
SentenceSplitter() chunk_size, chunk_overlap: 1024 200
constants DEFAULT_CHUNK_SIZE: 1024  SENTENCE_CHUNK_OVERLAP: 200
  SentenceSplitter(chunk_size=128): ValueError: Got a larger chunk overlap (200) than chunk size (128), should be smaller.
  SentenceSplitter(chunk_size=200): OK, chunk_overlap=200
  SentenceSplitter(chunk_size=201): OK, chunk_overlap=200
  SentenceSplitter(chunk_size=256): OK, chunk_overlap=200
default tokenizer: functools.partial(<bound method Encoding.encode of <Encoding 'cl100k_base'>>, allowed_special='all')
  len(get_tokenizer()(probe)) = 10 | cl100k_base = 10 | gpt2 = 12

Settings defaults: chunk_size = 1024  chunk_overlap = 200
Settings.node_parser type: SentenceSplitter
Settings.chunk_size = 128 -> OK; node_parser.chunk_overlap now 200
Settings.chunk_overlap = 25 -> node_parser: 128 25
Settings.node_parser on synthetic text: 25 nodes, token lens min/max = 88/110 (limit 128); char lens min/max = 495/619
```
**Output (`lab05b_choose_chunk_size_paths.py`, run against the repo `data/`, read-only):**
```
SimpleDirectoryReader(data) -> documents: 39
documents per file: {'customers-100.csv': 1, 'nike_2023_annual_report.txt': 1, 'q_a.json': 1, 'q_a_smith.json': 1, 'q_a_smith_short.json': 1, 'Understanding_Climate_Change.pdf': 33, 'wealth_retrieved_passages_from_original_memorag.csv': 1}
documents[0:20] (file_name, page_label): [('customers-100.csv', None), ('nike_2023_annual_report.txt', None), ('q_a.json', None), ('q_a_smith.json', None), ('q_a_smith_short.json', None), ('Understanding_Climate_Change.pdf', '1'), ... ('Understanding_Climate_Change.pdf', '15')]
DatasetGenerator import OK; warnings at import: []
notebook path chunk_size=128 overlap=25: 1462 nodes; tokens max=99; chars min/max=51/604
notebook path chunk_size=256 overlap=51: 610 nodes; tokens max=224; chars min/max=10/1299
script path chunk_size=128: ValueError: Got a larger chunk overlap (200) than chunk size (128), should be smaller.
script path chunk_size=256: OK, overlap=200, nodes=2123
```
In the `documents[0:20]` line, the climate PDF entries elided as "..." are pages '2' to '14', in order. The full line is in `out_lab05b.txt`.

**OS-dependent file order** (`lab05c_sort_order.py`). `SimpleDirectoryReader` builds its file list with `new_input_files = sorted(all_files)` (STATIC: `llama_index/core/readers/file/base.py` L422 in the installed package). Sorting Path objects gives:
```
Windows order: ['customers-100.csv', 'nike_2023_annual_report.txt', 'q_a.json', 'q_a_smith.json', 'q_a_smith_short.json', 'Understanding_Climate_Change.pdf', 'wealth_retrieved_passages_from_original_memorag.csv']
POSIX order:   ['Understanding_Climate_Change.pdf', 'customers-100.csv', 'nike_2023_annual_report.txt', 'q_a.json', 'q_a_smith.json', 'q_a_smith_short.json', 'wealth_retrieved_passages_from_original_memorag.csv']
```
**Source (STATIC):**
- `llama_index/core/evaluation/dataset_generation.py` L48 and L113 carry `@deprecated(...)` decorators. They point users to `LabelledRagDataset` and `RagDatasetGenerator`.
- So DatasetGenerator is deprecated, but it still imports in 0.14.25.

**Conclusion.**
- **Defaults and errors:**
  - SentenceSplitter defaults to chunk_size=1024 and chunk_overlap=200 tokens.
  - Overlap > size raises `ValueError: Got a larger chunk overlap (200) than chunk size (128), should be smaller.`
  - Equality is accepted (chunk_size=200 is OK).
- **The script crashes; the notebook path does not:**
  - **`all_rag_techniques_runnable_scripts/choose_chunk_size.py:L48` crashes on its first default chunk size, 128.** The defaults `[128, 256]` are at L133.
  - The run never reaches 256. Even if it did, chunk_size=256 would run with overlap 200, which is 78% of the chunk and produced 2123 nodes against 610 in the notebook path.
  - The notebook path (cell 10, `Settings.chunk_overlap = chunk_size // 5`) runs. Setting `Settings.chunk_size = 128` while the overlap is still 200 does not raise; the overlap is fixed on the next line.
- **Units:** `Settings.chunk_size` and SentenceSplitter sizes are **tokens** counted with **tiktoken `cl100k_base`** (the default `get_tokenizer()`).
  - Observed node token counts stay below the limit (max 99 for 128, 224 for 256), because the metadata string also uses part of the budget.
  - At 128 tokens, chunks were 51–604 characters, so character length varies widely at a fixed token budget.
- **What choose_chunk_size actually indexes.** `SimpleDirectoryReader("../data")` loads **all 7 files** in data/.
  - On Windows, `documents[0:20]` = the CSV, the full Nike annual report (1 document), 3 Q/A JSON files and climate PDF pages 1–15.
  - On POSIX, sorting is case-sensitive, so the uppercase `Understanding_…pdf` sorts first and `documents[0:20]` would be climate pages 1–20 (inferred from Path sorting; not run on Linux).
  - The questions therefore come from a mixed, OS-dependent corpus.
  - Assumption: the data/ folder may have held fewer files when the saved output was produced; that run's path is `C:\Users\N7\…`, i.e. Windows. UNVERIFIED.

**Confidence:** high for the defaults, exception, crash, units and Windows order (ran). Medium-high for the POSIX order (inferred from PurePosixPath sorting).

## 6. `FaithfulnessEvaluator` prompt keys and the "silently ignored" claim (choose_chunk_size.ipynb cell 8; script L107)

**Code (condensed excerpt of `lab04_06_libs.py`):**
```python
from llama_index.core.llms import MockLLM
from llama_index.core.evaluation import FaithfulnessEvaluator
from llama_index.core.prompts import PromptTemplate
ev = FaithfulnessEvaluator(llm=MockLLM())
before = {k: v.get_template() for k, v in ev.get_prompts().items()}
NEW = PromptTemplate("CUSTOM PROMPT Information: {query_str} Context: {context_str} Answer:")
ret = ev.update_prompts({"your_prompt_key": NEW})
after = {k: v.get_template() for k, v in ev.get_prompts().items()}
print(list(before), ret, any(before[k] != after[k] for k in before))
ev.update_prompts({"eval_template": NEW})            # positive control
```
**Output:**
```
get_prompts().keys(): ['eval_template', 'refine_template']
update_prompts({'your_prompt_key': ...}) returned: None | raised: no
any template changed: False
any template contains 'CUSTOM PROMPT': False
after update_prompts({'eval_template': ...}): eval_template changed = True | contains CUSTOM PROMPT = True
first 120 chars of default eval_template: 'Please tell if a given piece of information is supported by the context.\nYou need to answer with either YES or NO.\nAnswe'
```
**Source (STATIC, installed package):**
- `prompts/mixin.py` `update_prompts` (L54–L79) passes the dict to `_update_prompts`. It raises only for an unknown *sub-module* key (one containing `:`).
- `evaluation/faithfulness.py` `_update_prompts` (L152–L157) acts only on the keys `"eval_template"` and `"refine_template"`.

**Conclusion.**
- **CONFIRMED:** the custom faithfulness prompt in choose_chunk_size (notebook cell 8; `choose_chunk_size.py:L107`) is a silent no-op, and the evaluator keeps its default prompt.
- The correct key is `eval_template`.
- Lesson: verify that a configuration change took effect by reading it back.

**Confidence:** high.

## 7. Climate PDF through the repo's `encode_pdf` splitting path (no embeddings)

**Code (excerpt of `lab07_climate.py`; mirrors `helper_functions.py:L62-L69`):**
```python
docs = PyPDFLoader(pdf).load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
chunks = splitter.split_documents(docs)                       # per-page, as encode_pdf does
full = "\n".join(d.page_content for d in docs)                # concatenated alternative
cross = splitter.create_documents([full])
# page-break scan: page N whose stripped text does not end in . ! ? : " ) -> print last/first 80 chars
for name in ("cl100k_base", "gpt2"): enc = tiktoken.get_encoding(name); len(full) / len(enc.encode(full))
```
**Output** (abridged: the page-break listing is reduced to its final count, with examples below; the metadata line is shortened as noted; the full stdout is in `out_lab07.txt`):
```
PyPDFLoader pages (Documents): 33
first doc metadata: {'producer': 'Microsoft® Word 2021', 'creator': 'Microsoft® Word 2021', 'creationdate': '2024-07-13T20:17:34+03:00', 'author': 'Nir', 'moddate': '2024-07-13T20:17:34+03:00', 'source': '.../data/Understanding_Climate_Change.pdf', 'total_pages': 33, 'page': 0, 'page_label': '1'}
last doc metadata page/page_label: 32 33
empty pages: []

per-page split_documents(1000,200,len): 97 chunks; len min/median/max = 391/933/999; chunks < 200 chars = 0
chunk metadata keys: ['author', 'creationdate', 'creator', 'moddate', 'page', 'page_label', 'producer', 'source', 'total_pages']
any chunk metadata with >1 page: impossible by construction; distinct pages in chunks: 33
chunks containing a tab (what replace_t_with_space L18-L31 would change): 0

concatenated split (same splitter): 92 chunks; len min/median/max = 603/960.0/998
concatenated chunks that span a page break: 39

Page breaks where page N does not end with terminal punctuation: count: 24 of 32 page breaks
cl100k_base  PyPDFLoader: chars=72523 tokens=13016 chars/token=5.572
cl100k_base  PyMuPDF    : chars=72593 tokens=13026 chars/token=5.573
gpt2         PyPDFLoader: chars=72523 tokens=14305 chars/token=5.070
gpt2         PyMuPDF    : chars=72593 tokens=14375 chars/token=5.050

per-page 1000/200 chunks, cl100k tokens: min/median/max = 67/164/192; > 256 tokens: 0/97; > 512 tokens: 0/97
per-page 1000/200 chunks, gpt2 tokens: min/median/max = 75/181/211; > 256: 0; > 512: 0
lines appearing on >= 3 pages: []
```
The "®" in the producer field printed as a replacement character in the Windows console, and `source` is shortened here.

**The 24 non-terminal page breaks fall into two kinds.** Pages below are 1-based PDF pages, which equal metadata `page` + 1.
- **8 real mid-sentence cuts**, where the next page starts in lowercase. They are at PDF pages 12→13, 14→15, 15→16, 16→17, 21→22, 22→23, 24→25 and 28→29. Example (exact output):
  ```
  page(meta) 11 -> 12:
    END   ...'rtnerships (PPPs) can leverage resources, expertise, and innovation to implement'
    START 'large-scale climate solutions. PPPs are particularly effective in areas such as '...
  page(meta) 20 -> 21:
    END   ...'onsibility (CSR) initiatives. This includes reducing emissions, enhancing energy'
    START 'efficiency, and adopting sustainable supply chain practices. Transparent reporti'...
  ```
  - The PPP cut is independently confirmed with pdftotext: page 12 ends "…innovation to implement" and page 13 starts "large-scale climate solutions."
- **16 orphaned headings**, where page N ends with a section heading whose body is on page N+1. They are at PDF pages 1→2, 2→3, 3→4, 4→5, 5→6, 6→7, 7→8, 8→9, 10→11, 11→12, 17→18, 18→19, 20→21, 27→28, 30→31 and 31→32. Example:
  ```
  page(meta) 0 -> 1:
    END   ...'icant increase in fossil fuel consumption, which continues to rise \ntoday. \nCoal'
    START 'Coal is the most carbon-intensive fossil fuel, and its use for electricity gener'...
  ```
  - With per-page splitting, the heading "Coal" sits in a page-1 chunk, separated from the paragraph it introduces.

**Conclusion.**
- **Page metadata:** PyPDFLoader's `page` is **0-based** and `page_label` is the 1-based printed label ('1'…'33'). The lesson should cite PDF pages as 1-based and convert.
- **Chunks never cross pages.** `encode_pdf` splits each page separately: 97 chunks, against 92 when the same splitter runs on the concatenated text, where 39 of 92 chunks cross a page break. Overlap therefore cannot rescue the 8 cross-page sentences. §9 shows that the PPP sentence is in no per-page chunk.
- **Cleaning is a no-op here.** `replace_t_with_space` (L18–L31) only replaces tabs, and this PDF has none in any chunk.
- **No repeated lines.** No line repeats on ≥3 pages, so this PDF has no header/footer boilerplate. The failure scenario needs another example, such as the book PDFs' "OceanofPDF.com" footer (orchestrator fact; not re-run here).
- **Chars/token is corpus-specific:**
  - 5.57 chars/token for cl100k_base, 5.07 for gpt2 and 6.20 for BERT WordPiece (§10 script).
  - The text averages 6.72 characters per word and 7.84 characters per whitespace-delimited word including the space, i.e. long technical vocabulary.
  - The common "≈4 chars/token" heuristic would overestimate token counts by about 40% here.
- **Truncation is not active at 1000 characters.** Per-page 1000-character chunks are 67–192 cl100k tokens (median 164). None exceed 256 or 512, so truncation is not a live failure at v0 settings on corpus D.

**WordPiece check** (`lab10_wordpiece.py`; uses the models' own tokenizers; counts include [CLS]/[SEP]; tokenizer.json padding and truncation are disabled). Lines marked `...` are abridged; the full output is in `out_lab10.txt`:
```
-- per-page RecursiveCharacterTextSplitter(1000,200,len): 97 chunks
   all-MiniLM-L6-v2   WordPiece tokens (incl. CLS/SEP) min/median/max = 59/149/182; > 256: 0; > 512: 0; over this model's limit 256: 0
   bge-small-en-v1.5  WordPiece tokens (incl. CLS/SEP) min/median/max = 59/149/182; > 256: 0; > 512: 0; over this model's limit 512: 0
   cl100k_base tokens min/median/max = 67/164/192; > 256: 0
-- per-page RecursiveCharacterTextSplitter(1500,300,len): 65 chunks
   all-MiniLM-L6-v2   WordPiece tokens (incl. CLS/SEP) min/median/max = 109/215/270; > 256: 4; > 512: 0; over this model's limit 256: 4
   bge-small-en-v1.5  ... over this model's limit 512: 0
   cl100k_base tokens min/median/max = 114/238/292; > 256: 18
-- per-page RecursiveCharacterTextSplitter(2000,400,len): 65 chunks
   all-MiniLM-L6-v2   WordPiece tokens (incl. CLS/SEP) min/median/max = 59/160/365; > 256: 32; > 512: 0; over this model's limit 256: 32
   bge-small-en-v1.5  ... over this model's limit 512: 0
   cl100k_base tokens min/median/max = 67/175/393; > 256: 32
full text: chars=72523 whitespace-separated words=9255 chars/word=7.84 mean word length=6.72
full text, all-MiniLM-L6-v2 WordPiece: tokens=11694 chars/token=6.202
full text, bge-small-en-v1.5 WordPiece: tokens=11694 chars/token=6.202
```
- **The two models tokenize identically.** Both use a BERT-uncased vocabulary of size 30522, so their counts match exactly.
- **cl100k is a conservative proxy here.** It over-counts compared with WordPiece on this text (it flags 18 chunks over 256 at 1500 characters, where WordPiece flags 4).
- **The I1 grid can use this as a measurable truncation-rate metric.** For MiniLM on this corpus, truncation first appears at 1500 characters (4 of 65 chunks) and reaches 32 of 65 chunks at 2000. For bge-small, nothing up to 2000 characters exceeds 512.

**Confidence:** high (ran; the page cut is confirmed by two extractors).

## 8. Original worked example (S=300, O=0 vs O=60)

**Text.** This is an original 785-character paragraph written for this lab, not taken from the book. Its offsets come from `lab08_worked_example.py`. The paragraph describes MiniLM-style mean pooling with a 256 cap, consistent with §10.
```python
PARA = (
    "A bi-encoder turns a passage into one vector in three steps. First, a WordPiece tokenizer "
    "splits the text into subword tokens and adds the special [CLS] and [SEP] markers. Second, a "
    "small transformer reads the token sequence and produces one contextual vector per token. "
    "Third, a pooling layer averages those token vectors into a single fixed-size embedding, "
    "which is then scaled to unit length. Two passages are later compared by the cosine of their "
    "vectors. Because the model was trained on short inputs, its "
    "configuration caps the sequence at 256 tokens. Tokens beyond the cap are silently dropped "
    "before the transformer runs. A sentence placed at the end of a long chunk can therefore have "
    "no influence at all on the chunk's embedding, even though the chunk text still contains it."
)
FACT = "Tokens beyond the cap are silently dropped before the transformer runs."
QUERY = "What happens to tokens past an embedding model's sequence limit?"
```
**Output (exact, = `out_lab08.txt`):**
```
len(PARA)=785; FACT span=[558,629) len=71
QUERY: What happens to tokens past an embedding model's sequence limit?

--- fixed_window_chunks(size=300, overlap=0): 3 chunks
[0]   0-300 'A bi-encoder turns a passage into one vector in three steps. First, a WordPiece tokenizer splits the text into subword tokens and adds the special [CLS] and [SEP] markers. Second, a small transformer reads the token sequence and produces one contextual vector per token. Third, a pooling layer averag'
[1] 300-600 'es those token vectors into a single fixed-size embedding, which is then scaled to unit length. Two passages are later compared by the cosine of their vectors. Because the model was trained on short inputs, its configuration caps the sequence at 256 tokens. Tokens beyond the cap are silently dropped'
[2] 600-785 " before the transformer runs. A sentence placed at the end of a long chunk can therefore have no influence at all on the chunk's embedding, even though the chunk text still contains it."
chunks wholly containing FACT: []

--- fixed_window_chunks(size=300, overlap=60): 4 chunks
[0]   0-300 'A bi-encoder turns a passage into one vector in three steps. First, a WordPiece tokenizer splits the text into subword tokens and adds the special [CLS] and [SEP] markers. Second, a small transformer reads the token sequence and produces one contextual vector per token. Third, a pooling layer averag'
[1] 240-540 'e contextual vector per token. Third, a pooling layer averages those token vectors into a single fixed-size embedding, which is then scaled to unit length. Two passages are later compared by the cosine of their vectors. Because the model was trained on short inputs, its configuration caps the sequen'
[2] 480-780 "s trained on short inputs, its configuration caps the sequence at 256 tokens. Tokens beyond the cap are silently dropped before the transformer runs. A sentence placed at the end of a long chunk can therefore have no influence at all on the chunk's embedding, even though the chunk text still contain"
[3] 720-785 " chunk's embedding, even though the chunk text still contains it."
chunks wholly containing FACT: [2]

--- recursive_chunks(size=300, overlap=60) [our simplified version]: 4 chunks
[0]   0-294 len=294 'A bi-encoder turns a passage into one vector in three steps. First, a WordPiece tokenizer splits the text into subword tokens and adds the special [CLS] and [SEP] markers. Second, a small transformer reads the token sequence and produces one contextual vector per token. Third, a pooling layer '
[1] 238-534 len=296 'one contextual vector per token. Third, a pooling layer averages those token vectors into a single fixed-size embedding, which is then scaled to unit length. Two passages are later compared by the cosine of their vectors. Because the model was trained on short inputs, its configuration caps the '
[2] 478-773 len=295 "was trained on short inputs, its configuration caps the sequence at 256 tokens. Tokens beyond the cap are silently dropped before the transformer runs. A sentence placed at the end of a long chunk can therefore have no influence at all on the chunk's embedding, even though the chunk text still "
[3] 714-785 len=71 "on the chunk's embedding, even though the chunk text still contains it."
chunks wholly containing FACT: [2]

--- LangChain RecursiveCharacterTextSplitter(300, 60, len): 4 chunks
[0]   0-293 len=293 overlap_prev=None contains_FACT=False 'A bi-encoder turns a passage into one vector in three steps. First, a WordPiece tokenizer splits the text into subword tokens and adds the special [CLS] and [SEP] markers. Second, a small transformer reads the token sequence and produces one contextual vector per token. Third, a pooling layer'
[1] 238-533 len=295 overlap_prev=55 contains_FACT=False 'one contextual vector per token. Third, a pooling layer averages those token vectors into a single fixed-size embedding, which is then scaled to unit length. Two passages are later compared by the cosine of their vectors. Because the model was trained on short inputs, its configuration caps the'
[2] 478-772 len=294 overlap_prev=55 contains_FACT=True "was trained on short inputs, its configuration caps the sequence at 256 tokens. Tokens beyond the cap are silently dropped before the transformer runs. A sentence placed at the end of a long chunk can therefore have no influence at all on the chunk's embedding, even though the chunk text still"
[3] 714-785 len=71 overlap_prev=58 contains_FACT=False "on the chunk's embedding, even though the chunk text still contains it."
```
**Conclusion.**
- **At O=0, the fact `[558,629)` is cut at offset 600.** Chunk 1 ends "…silently dropped" and chunk 2 begins " before the transformer runs."
- **At O=60, chunk 2 `[480,780)` contains the fact whole.**
  - The count formula holds: ceil((785−60)/240) = 4 and ceil(785/300) = 3.
  - Since F = 71 > O+1 = 61, this is *luck of placement*, not a guarantee. The §1 formula gives P = (300−71+1)/240 = 0.958 for a random placement.
- **LangChain differs from our simplified chunker in small ways:**
  - Its overlaps are 55, 55 and 58, below the requested 60.
  - Its chunks end without trailing spaces, because strip_whitespace=True.
- In LangChain's output only chunk 2 contains FACT (`contains_FACT=True`); chunks 0, 1 and 3 do not.
- **Query → answer chunk, by hand.** The only chunk that holds the answer sentence whole is O=60 chunk 2.
  - At O=0 the sentence is split: chunk 1 ends with "Tokens beyond the cap are silently dropped", and chunk 2 starts with " before the transformer runs."
  - So in this example chunk 1 still carries the core answer and loses only the "when" detail. The lesson should say so honestly rather than overstate the damage.
  - A boundary falling earlier in the sentence (for example after "Tokens beyond") would remove the answer from both chunks.

**Confidence:** high (exact offsets; the printed output is the saved stdout).

## 9. Minimal implementation (`chunklib.py`) — the code the lesson's Part H.1 can show

Full module (the exact file `labscripts/chunklib.py`, minus its 4-line module docstring; Python 3.12, stdlib only):
```python
from __future__ import annotations

import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    text: str
    char_start: int  # inclusive offset into the source text
    char_end: int    # exclusive offset
    page_start: int | None = None  # 1-based page of char_start (page-aware chunker only)
    page_end: int | None = None    # 1-based page of char_end - 1


def fixed_window_chunks(text: str, size: int, overlap: int = 0) -> list[Chunk]:
    """Windows of `size` chars, each starting `size - overlap` chars after the previous one."""
    if size <= 0:
        raise ValueError("size must be > 0")
    if not 0 <= overlap < size:
        raise ValueError(f"need 0 <= overlap < size, got overlap={overlap}, size={size}")
    stride = size - overlap
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(Chunk(len(chunks), text[start:end], start, end))
        if end == len(text):
            break
        start += stride
    return chunks


DEFAULT_SEPARATORS = ("\n\n", "\n", " ")


def _split_spans(text: str, start: int, end: int, seps: tuple[str, ...], size: int) -> list[tuple[int, int]]:
    """Recursively cut [start, end) into contiguous pieces of <= size chars, preferring early separators.
    A separator stays attached to the END of the piece before it, so pieces tile the text exactly."""
    if end - start <= size:
        return [(start, end)]
    if not seps:  # last resort (like LangChain's "" separator): single characters, merged later
        return [(s, s + 1) for s in range(start, end)]
    sep, rest = seps[0], seps[1:]
    pieces, i = [], start
    while i < end:
        j = text.find(sep, i, end)
        if j == -1:
            pieces.append((i, end))
            break
        pieces.append((i, j + len(sep)))
        i = j + len(sep)
    out: list[tuple[int, int]] = []
    for a, b in pieces:
        out.extend([(a, b)] if b - a <= size else _split_spans(text, a, b, rest, size))
    return out


def recursive_chunks(text: str, size: int, overlap: int = 0,
                     separators: tuple[str, ...] = DEFAULT_SEPARATORS) -> list[Chunk]:
    """Simplified recursive splitter: split on the coarsest separator that works, then greedily merge
    pieces up to `size`; the next chunk re-starts with whole trailing pieces totalling <= `overlap`.
    Unlike LangChain it never strips whitespace, so offsets stay exact."""
    if not 0 <= overlap < size:
        raise ValueError(f"need 0 <= overlap < size, got overlap={overlap}, size={size}")
    if not text:
        return []
    pieces = _split_spans(text, 0, len(text), separators, size)
    spans: list[tuple[int, int]] = []
    cur: list[tuple[int, int]] = []
    for p in pieces:
        if cur and p[1] - cur[0][0] > size:  # adding p would overflow: emit current chunk
            spans.append((cur[0][0], cur[-1][1]))
            keep = []
            for q in reversed(cur):  # whole trailing pieces that fit in the overlap budget
                if cur[-1][1] - q[0] <= overlap:
                    keep.insert(0, q)
                else:
                    break
            cur = keep
            while cur and p[1] - cur[0][0] > size:  # make room for p
                cur.pop(0)
        cur.append(p)
    if cur:
        spans.append((cur[0][0], cur[-1][1]))
    return [Chunk(i, text[a:b], a, b) for i, (a, b) in enumerate(spans)]


def join_pages(pages: list[str], sep: str = "\n") -> tuple[str, list[int]]:
    """Concatenate page texts; return the full text and the start offset of each page."""
    starts, parts, pos = [], [], 0
    for i, p in enumerate(pages):
        if i:
            parts.append(sep)
            pos += len(sep)
        starts.append(pos)
        parts.append(p)
        pos += len(p)
    return "".join(parts), starts


def page_of(offset: int, page_starts: list[int]) -> int:
    """1-based page number containing character `offset`."""
    return bisect.bisect_right(page_starts, offset)


def page_aware_chunks(pages: list[str], size: int, overlap: int, chunker=recursive_chunks) -> list[Chunk]:
    """Chunk ACROSS page breaks (so a sentence cut by a page break can still land in one chunk)
    while recording which pages each chunk spans."""
    full, starts = join_pages(pages)
    out = []
    for c in chunker(full, size, overlap):
        out.append(Chunk(c.chunk_id, c.text, c.char_start, c.char_end,
                         page_of(c.char_start, starts), page_of(c.char_end - 1, starts)))
    return out


def check_chunks(text: str, chunks: list[Chunk], size: int) -> None:
    """Property checks: offsets reproduce text, size limit, full coverage, no gaps, non-negative overlap."""
    assert chunks, "no chunks"
    assert chunks[0].char_start == 0 and chunks[-1].char_end == len(text), "must start at 0 and end at len"
    for c in chunks:
        assert text[c.char_start:c.char_end] == c.text, f"offsets wrong for chunk {c.chunk_id}"
        assert 0 < len(c.text) <= size, f"chunk {c.chunk_id} has length {len(c.text)}"
    for a, b in zip(chunks, chunks[1:]):
        assert b.char_start <= a.char_end, f"gap between chunk {a.chunk_id} and {b.chunk_id}"
        assert b.char_start > a.char_start, "no forward progress"
    # rebuild the document by dropping each chunk's overlap with its predecessor
    rebuilt = chunks[0].text + "".join(b.text[a.char_end - b.char_start:] for a, b in zip(chunks, chunks[1:]))
    assert rebuilt == text, "overlap-removed concatenation must reproduce the document"


def chunks_containing(chunks: list[Chunk], start: int, end: int) -> list[int]:
    """ids of chunks that wholly contain the span [start, end)."""
    return [c.chunk_id for c in chunks if c.char_start <= start and end <= c.char_end]
```
**Run on the climate PDF** (`lab09_minimal_impl.py`; page texts from PyPDFLoader, joined with "\n"):
```
pages=33 full_len=72523
fixed_window_chunks(1000,200) on concatenated text: 91 chunks, len min/median/max=523/1000/1000  -> property checks PASSED
recursive_chunks(1000,200) on concatenated text: 92 chunks, len min/median/max=603/962.0/1000  -> property checks PASSED
randomised property checks: 120 (chunker, size, overlap) combinations PASSED (seed 0)
  fixed_window_chunks('', 5, 2) -> []
  recursive_chunks('', 5, 2) -> []
  fixed_window_chunks('a', 5, 2) -> [(0, 1, 'a')]
  recursive_chunks('a', 5, 2) -> [(0, 1, 'a')]
  fixed_window_chunks('abc', 5, 2) -> [(0, 3, 'abc')]
  recursive_chunks('abc', 5, 2) -> [(0, 3, 'abc')]
  fixed_window_chunks('xxxxxxxxxxx, 5, 2) -> [(0, 5, 'xxxxx'), (3, 8, 'xxxxx'), (6, 11, 'xxxxx'), (9, 14, 'xxxxx'), (12, 17, 'xxxxx'), (15, 20, 'xxxxx'), (18, 23, 'xxxxx')]
  recursive_chunks('xxxxxxxxxxx, 5, 2) -> [(0, 5, 'xxxxx'), (3, 8, 'xxxxx'), (6, 11, 'xxxxx'), (9, 14, 'xxxxx'), (12, 17, 'xxxxx'), (15, 20, 'xxxxx'), (18, 23, 'xxxxx')]
  fixed_window_chunks('abc', size=10, overlap=10) -> ValueError: need 0 <= overlap < size, got overlap=10, size=10
  fixed_window_chunks('abc', size=10, overlap=11) -> ValueError: need 0 <= overlap < size, got overlap=11, size=10
  fixed_window_chunks('abc', size=10, overlap=-1) -> ValueError: need 0 <= overlap < size, got overlap=-1, size=10

recursive_chunks(1000,200) applied per page (like encode_pdf): 97 chunks
page_aware_chunks(1000,200): 92 chunks; spanning 2+ pages: 39; first 3 (id, page_start, page_end): [(0, 1, 1), (1, 1, 1), (2, 1, 2)]

cut sentence span [26844,26973) pages 12-13 (1-based)
  text: 'Public-\nprivate partnerships (PPPs) can leverage resources, expertise, and innovation to implement\nlarge-scale climate solutions.'
  page-aware chunks wholly containing it: [34]
  per-page recursive chunks containing both halves: 0
  LangChain per-page chunks containing both halves: 0 (of 97 chunks)

LangChain on 'x'*23 with chunk_size=5, chunk_overlap=2: ['xxxxx', 'xxxxx', 'xxxxx', 'xxxxx', 'xxxxx', 'xxxxx', 'xxxxx']
```
In the edge-case lines the input repr is truncated to 12 characters by the print format (`!r:.12`); the inputs were `""`, `"a"`, `"abc"` and `"x"*23`.

**Hand-trace fixtures** (`lab09b_trace23.py`, T = "abcdefghijklmnopqrstuvw", 23 characters; W = "the cat sat on the mat", 22 characters):
```
fixed_window_chunks(T, 10, 3) -> [(0, 10, 'abcdefghij'), (7, 17, 'hijklmnopq'), (14, 23, 'opqrstuvw')]
fixed_window_chunks(T, 10, 0) -> [(0, 10, 'abcdefghij'), (10, 20, 'klmnopqrst'), (20, 23, 'uvw')]
fixed_window_chunks(T, 8, 4) -> [(0, 8, 'abcdefgh'), (4, 12, 'efghijkl'), (8, 16, 'ijklmnop'), (12, 20, 'mnopqrst'), (16, 23, 'qrstuvw')]
recursive_chunks(W, 10, 4) -> [(0, 8, 'the cat '), (4, 12, 'cat sat '), (8, 15, 'sat on '), (12, 22, 'on the mat')]
LangChain(10, 4)            -> ['the cat', 'cat sat', 'sat on', 'on the', 'the mat']
```
**Conclusion.**
- **All properties pass on the climate text and on 120 random (size, overlap) settings.** The properties are: offsets reproduce the text, length ≤ size, full coverage with no gaps, forward progress, and overlap-removed concatenation equals the document.
- **The simplified recursive chunker reproduces LangChain's chunk counts on this PDF:** 97 per-page and 92 concatenated, against LangChain's 97 and 92 in §7. It also reproduces the char-level fallback (the 'x'*23 case).
- **It is not identical to LangChain.**
  - Our chunker attaches separators to the *end* of a piece; LangChain's `keep_separator=True` attaches them to the *start* and then strips whitespace. On W this gives 4 chunks against LangChain's 5.
  - This is a useful "same idea, different boundaries" teaching point.
  - It is also why gold labels must be spans, not chunk ids.
- **Page-aware chunking keeps the PPP sentence whole** (chunk 34, pages 12–13). Per-page chunking, both ours and LangChain's, never contains it whole.

**Confidence:** high.

## 10. Embedding-model max sequence length, pooling, truncation

**Fetched files** (HTTP 200 for all, 2026-10-08, at the revisions in §0). The two `sentence_bert_config.json` lines are verbatim; the others are condensed:
```
sentence-transformers/all-MiniLM-L6-v2/sentence_bert_config.json: {"max_seq_length": 256, "do_lower_case": false}
sentence-transformers/all-MiniLM-L6-v2/1_Pooling/config.json: word_embedding_dimension 384, pooling_mode_cls_token false, pooling_mode_mean_tokens true
sentence-transformers/all-MiniLM-L6-v2/modules.json: Transformer -> Pooling -> Normalize
sentence-transformers/all-MiniLM-L6-v2/config.json: BertModel, num_hidden_layers 6, hidden_size 384, max_position_embeddings 512, vocab_size 30522
BAAI/bge-small-en-v1.5/sentence_bert_config.json: {"max_seq_length": 512, "do_lower_case": true}
BAAI/bge-small-en-v1.5/1_Pooling/config.json: word_embedding_dimension 384, pooling_mode_cls_token true, pooling_mode_mean_tokens false
BAAI/bge-small-en-v1.5/modules.json: Transformer -> Pooling -> Normalize
BAAI/bge-small-en-v1.5/config.json: BertModel, num_hidden_layers 12, hidden_size 384, max_position_embeddings 512, vocab_size 30522
```
**Model cards and docs:**
- **all-MiniLM-L6-v2 README.md (L115).** It states that input text longer than 256 word pieces is truncated by default. The same card says training limited the sequence length to 128 tokens (L132).
- **bge-small-en-v1.5 README.md.**
  - Its model table lists Dimension 384 and Sequence Length 512 (L2970).
  - Its transformers usage snippet uses CLS pooling and then normalization (L2840 and L2861–L2864).
  - For short-query-to-passage retrieval it recommends the query instruction "Represent this sentence for searching relevant passages: ", and no instruction for passages (L2680, L2691).
- **sbert.net "Computing Embeddings" → "Input Sequence Length"** (fetched 2026-10-08):
  - Longer texts are truncated to the first `model.max_seq_length` tokens.
  - The length cannot be raised above what the underlying transformer supports.
  - Models trained on short texts may represent long texts poorly.
- **Observed in tokenizer.json:** all-MiniLM-L6-v2's `tokenizer.json` carries built-in `truncation max_length 128` and `padding length 128`; bge's has neither. Per the model card and the sbert docs, the effective limit for `SentenceTransformer.encode` is max_seq_length=256.
  - UNVERIFIED: how sentence-transformers overrides the 128 setting internally. I did not run sentence-transformers.
  - Anyone using raw `tokenizers` or ONNX/fastembed paths should check which limit applies.

**Conclusion (state these in the lesson):**

| Model | max_seq_length (WordPiece tokens) | Pooling | Normalize | Beyond the limit |
|---|---|---|---|---|
| sentence-transformers/all-MiniLM-L6-v2 | **256** | mean | yes | truncated, keeps the first 256 tokens |
| BAAI/bge-small-en-v1.5 | **512** | CLS | yes | truncated, keeps the first 512 tokens |

- Both models use the same uncased BERT WordPiece vocabulary (30522), and the climate-PDF token counts are identical (§7).
- UNVERIFIED (not run): that `[CLS]`/`[SEP]` count toward max_seq_length inside sentence-transformers. This is standard BERT tokenizer behaviour and I believe it, but I did not execute it.

**Confidence:** high for the config values and documented truncation. The runtime truncation behaviour was not executed (no torch).
