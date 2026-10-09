# Transfer seed bank: coach-only (the learner must not open this file)

**What this is:** nine fresh questions from outside sources, one per concept, kept here so they stay unseen until the tutor asks them.
**What this is not:** a lesson part or a reading. A seed never goes into a lesson file, and the learner never sees this file.

Approved by the learner on 2026-10-09 from [the external-resources review](../EXTERNAL_RESOURCES_REVIEW_2026-10-09.md) §3b (seeds and reserves only; the "in-file additions" there are not approved yet). Every number and cite below was re-checked on 2026-10-09. The scripts and their outputs are in [`../verification/coach/`](../verification/coach/).

> **Licence notice for quoted repo text.** Lines marked "verbatim, MIT" copy text exactly from two MIT-licensed repositories, pinned read-only in `upstream/`:
> - **AIQ** = AI-Engineer-Interview-Questions (https://github.com/ombharatiya/AI-Engineer-Interview-Questions), commit `e080df2`. Copyright (c) 2026 Om. MIT License.
> - **SDG** = ai-system-design-guide (https://github.com/ombharatiya/ai-system-design-guide), commit `ed955b2`. Copyright (c) 2026 Om Bharatiya. MIT License.
>
> The full licence is the `LICENSE` file in each pinned folder. The AI Eval book (AE) and the RAG book are copyrighted: they are paraphrased and cited here, never quoted.

## Rules

- Ask **one question per turn** (CR-01). Ask for **confidence (1–3) first**, before any hint or answer (CR-16). Reply template for every turn: "____, because ____."
- Each seed is **used once**: either as the lesson's scored CR-13 Transfer item (only if marked CR-13-eligible) or as a review item from Day 14 on. Then fill in `used: <date>, <how>`. A used seed is no longer fresh.
- **Never write a seed into a lesson file.** Never ask one in Part A or before the concept is taught (review §9 item 6; 05 §2.3 step 1: Part A is diagnostic, before any teaching). Hide the key until after the attempt (CR-02, CR-04).
- **Cap:** at most **2 new items per concept** from external sources, counting seeds, Part L items and flashcards together (review §2). A reserve is used only **in place of** a seed, never in addition.
- Grade with the 05 §4.2 rubrics against the key below, not against the repo's answer. For a CR-13 Transfer item, a 4 names a check by measurement and says when not to use the idea (05 §4.2 Transfer). An application item (S8) needs a self-check for a 4; S4 uses debugging_0_3 in the lab.
- After the attempt, the repo's own answer may be shown verbatim with the notice above. Then give our plain-English explanation, then any correction from review §8.
- A multi-turn seed is asked one turn at a time. Grade each turn before asking the next.

**Cap check (approved external items per concept, 2026-10-09):**

| Concept | Approved items | Room left |
|---|---|---|
| P1 | this seed; the 'strawberry' M.1 flashcard planned in review §3a row 2 | 0 once that card is added |
| P3, P4, P6 | this seed (a second item is proposed in review §3b "in-file additions", not approved) | 1, or 0 once that item is approved |
| P5, C1, C4, C6, C7 | this seed | 1 |

---

## Seeds

### S1 · P1 · CR-13-eligible

- **Turns:**
  1. "A 40-page manual of about 25,000 tokens never changes. Send all of it with every question?"
  2. "What would you compute first?"
  3. "Give one reason to retrieve anyway."
- **Source:** AIQ `14-company-interview-questions/harvey.md` Q9 @ e080df2, rewritten as a fresh scenario. The 25,000-token manual is made up for the question.
- **Source text (verbatim, MIT):**
  > When would you put a whole contract in the context window instead of retrieving over it? Defend the answer with numbers.
- **Claim in the repo answer to correct (verbatim, MIT):**
  > Retrieval also gives you citations for free, since you know which passages were used, which matters more here than in most domains.
- **Key:**
  - Turn 1: not by default. First check that it fits the window **with a reserve for reasoning and the answer** (P1 D.5; P7 D.4). The window of `openai/gpt-oss-20b` on Groq is looked up in P1 lab Task 8, never assumed. The book says RAG is overkill when the documents fit in the context window (Ch1 p.12/14).
  - Turn 2: input tokens per query, both ways, then cost (P1 D.7).
    ```
    whole manual   ≈ 25,000 + system + question      (scenario number)
    v0 retrieval   =    976 before template overhead  (P1 D.5, P1_FACTS S9: 4 × 1,000-char chunks)
                   ≈ 1,050 billed (estimate)          (976 + the 71 tokens the O2 call billed beyond its message; composition UNVERIFIED)
    ratio          ≈ 24× more input per query         (DERIVED: 25,000 / ~1,050; input only, output assumed similar, not measured)
    ```
    Confirm with `usage.prompt_tokens` before quoting a ratio.
  - Turn 3: page citations a reader can check; a corpus that will grow; per-minute token limits (Groq's numbers UNVERIFIED here); latency. When not to retrieve: the manual fits, and questions need material scattered across it (Ch1 p.12/14: a few chunks miss scattered material).
  - Corrections to the repo answer: retrieval shows what was **supplied**, not what was **used** (C5 B.1, D.5, D.7), so citations are not "for free". The position of a passage in the prompt (lost in the middle, P7 D.6) is a different effect from the prompt's total length.
- **Use:** CR-13-eligible for P1 L.3. The P1 file has no whole-document scenario (checked, `coach_sources.py`).
- **used:**

### S2 · P3 · CR-13-eligible

- **Turns:**
  1. "You add a sixth PDF to Corpus T. Same query, same old chunk: can its BM25 score change?"
  2. "Can its cosine score change?"
- **Source:** SDG `06-retrieval-systems/04-vector-databases.md` @ ed955b2, under 'Q: How do you handle multi-tenancy in a vector database?', the paragraph 'The hybrid-search catch' (line 731).
- **Source text (verbatim, MIT):**
  > BM25 scores depend on corpus-wide IDF statistics. In a shared collection, one large tenant's vocabulary shifts every other tenant's keyword scores, and term statistics leak across the boundary.
- **Key:**
  - Turn 1: yes. The index keeps corpus-wide counts (P3 D.1). N grows, so every idf changes; n(t) grows if the new chunks contain the term; avgdl moves, so the length factor moves (P3 D.3, D.4). In `rank_bm25` the epsilon floor is a mean over **all** terms, so it moves too (P3 D.3). Only a chunk that matches no query term stays at 0.
  - Turn 2: no. Cosine uses only the query vector and the chunk vector (P4 D.2), and a chunk's vector depends only on its own text and the model (C3 D.4 cache key). Its **rank** can still move, because new chunks may score higher.
  - For the project: the chunk's id does not change (C3 D.2: `doc_id:snapshot_id:params_hash:seq`), yet its BM25 score does. So log a BM25 result with the whole indexed corpus (every document's `snapshot_id`), the `params_hash`, the tokenizer and k1, b, epsilon (reasoning).
  - A 4 adds the check: score one fixed query before and after adding the PDF; the BM25 scores move and the cosine scores do not.
- **Use:** CR-13-eligible for P3 L.3. The P3 file has no added-document scenario; P3-T-01 is about release-note identifiers (checked).
- **used:**

### S3 · P4 · review-only

- **Turn:** "A guide says unrelated texts score well above zero. Our MiniLM gave −0.09 and −0.05. Who is right?"
- **Source:** AIQ `04-rag-and-retrieval/questions.md` Q11 @ e080df2.
- **Source text (verbatim, MIT):**
  > Which distance metric should you use for embedding search - cosine, dot product, or Euclidean - and does the choice actually matter?
- **Claim in the repo answer (verbatim, MIT):**
  > Cosine scores are not calibrated, and many embedders are anisotropic, so even unrelated pairs sit well above zero and pack into a narrow positive band, which means an absolute value like 0.75 tells you little on its own.
- **Key:**
  - Both can be right, because scores are model-specific (P4 D.5). MiniLM-L6 gave −0.0859 and −0.0478 on two unrelated pairs (P4 D.5, P4_FACTS S5); the guide describes other embedders.
  - Never carry a threshold across models (P4 D.5). C4 D.5 shows it: the wrong model gave a rank-1 score of 0.1858 for the same question.
  - Check Cohere `embed-v4.0` separately; it is not measured in the course yet.
  - A 4 names the check: embed a few known-unrelated pairs with each model and read the scores before setting any cut-off.
- **Use:** review-only (the two numbers are in P4 D.5), from Day 14 on.
- **used:**

### S4 · P5 · review-only

- **Turns** (show the code below with turn 1):
  1. "This search() sorts its top k and passes its tests. Is it deterministic when documents are duplicated?"
  2. "How would you fix it?"
- **Source:** AIQ `12-coding-challenges/08_semantic_search_rag.py` @ e080df2, `VectorIndex.search` (L93–L100).
- **Source text (verbatim, MIT):**

```python
    def search(self, query: str, k: int = 3) -> list[tuple[int, float]]:
        if self._matrix is None:
            return []
        k = min(k, len(self.docs))
        scores = self._matrix @ self.embedder.embed(query)  # cosine == dot (unit norm)
        top = np.argpartition(-scores, k - 1)[:k]           # O(n) select, then sort k
        top = top[np.argsort(-scores[top])]
        return [(int(i), float(scores[i])) for i in top]
```

- **Key:**
  - Turn 1: repeatable, but not specified. On one machine the same array gave the same rows on a second call (35/35 real queries). But there is no tie rule: `argpartition` decides which tied copies get in, and NumPy does not define that order (P5 D.3; P5_FACTS S4).
  - The setup: the P5 index with every chunk 5 times (P5 D.3, lab Task 5b), 33 page-head queries, k = 4 (v0's k). Each variant is compared with a reference that breaks ties by the smaller id (06 §3.1).
    ```
    variant                                      differs from the reference
    argpartition, sort the k by score (this code)   33/33  (wrong set: 26/33)
    argpartition, sort the k by (−score, id)        26/33
    course top_k (tie-aware cut)                     0/33
    ```
    Source: `coach_p5_tie_probe.py`, output E3; two runs byte-identical.
  - Turn 2: sorting only the k winners by (−score, id) is **not** enough: the wrong copies are already in. Take every id that scores at least the k-th score, sort by (−score, id), then cut to k, as `top_k` in `p5_measure.py` (L44–L54) does. A full sort with the (−score, id) key is also correct. Or deduplicate at index time (P5 J2). Grade with `debugging_0_3` in the lab.
  - **Caveat, stated plainly:** the review's "26 of 30 queries" came from an unlogged scratch probe. The logged run above gives 26 of 33 page-head queries at k = 4; at k = 10 the cut falls between whole groups of 5 copies, and the set is right for all 33.
- **Use:** review-only (the duplicated index is P5 D.3 and lab Task 5b).
- **used:**

### S5 · P6 · CR-13-eligible

- **Turn:** "A guide says Recall@k is the share of queries with a relevant chunk in the top k. Right or wrong?"
- **Source:** AIQ `07-evaluation-and-observability/questions.md` Q23 @ e080df2 (the same error is in AIQ `GLOSSARY.md`, 'Recall@k').
- **Source text (verbatim, MIT):**
  > Which retrieval metrics would you use - recall@k, MRR, nDCG - and when does each matter?
- **Claim in the repo answer (verbatim, MIT):**
  > fraction of queries where a relevant chunk appears in the top k.
- **Key:**
  - Wrong. That is Hit@k, averaged over queries (the hit rate, P6 D.2). Recall@k divides by **all** relevant chunks in the qrels (P6 D.2).
  - They are guaranteed equal only when every query has exactly one relevant chunk. With more, they still match on a query whose top k holds none or all of its relevant chunks (DERIVED from the D.2 formulas).
  - Self-check on P6 Part F Q1: R@5 = 0.667 but Hit@5 = 1.
  - For multi-fact items, use CE@k (P6 D.7).
  - This targets the O1-Q04 gap (scored 0, session log 2026-10-08 #1). If the score is 2 or less, log a new misconception.
- **Use:** CR-13-eligible for P6 L.3. No P6 item poses a guide's definition (checked); P6-T-01's key states the one-relevant-chunk case, so do not show it first.
- **used:**

### S6 · C1 · CR-13-eligible

- **Turn:** "You have 300 PDFs. How do you find badly parsed pages without reading them all?"
- **Source:** AIQ `04-rag-and-retrieval/questions.md` Q13 @ e080df2.
- **Source text (verbatim, MIT):**
  > How would you detect that a parser silently corrupted documents, at scale, without reading every page?
- **Key:**
  - Two or more cheap per-page signals: characters vs images on the page (empty vs image-only, C1 D.4); the share of non-words (the repo's 'gibberish' signal; not measured in the course); a line repeated on at least half the text pages, minimum 3 (rule R1, C1 D.5).
  - Then hand-check a sample, stratified by document type.
  - A flag needs a look: R1 flagged 5 real section titles in the book's `index.pdf` (C1 D.5).
  - Measure what matters: the share of gold answers that sit on flagged pages.
  - When the check is not needed: no questions touch the flagged pages.
- **Use:** CR-13-eligible for C1 L.3. C1-T-01 is about slide decks; the file has no at-scale scenario (checked).
- **used:**

### S7 · C4 (MC-005) · CR-13-eligible

- **Turns:**
  1. "One source says missing evidence is worse than noise. Another says answers collapse past about half noise. Can both be true?"
  2. "How would you pick k for Corpus T?"
- **Source:** AE Ch7, 'Precision@k and Recall@k'; book Ch22 p.11–12/19. Paraphrased only; no repo text.
- **What the two sources say (paraphrase):**
  - AE: for the **first** retrieval stage, recall matters more than precision. A model can often read past irrelevant text, but it cannot answer if the evidence is missing. No study is cited for this.
  - Book: hold the number of retrieved documents fixed and swap relevant ones for noise step by step. Answers are said to hold up to about half noise, then drop sharply (Ch22 p.11/19; the cliff is drawn on p.12/19). No study is named. Noise that resembles the query but carries a wrong answer is called the most dangerous kind (p.11/19).
- **Key:**
  - Turn 1: yes. AE's claim is about the candidate pool of the first stage, which a reranker trims later. The book's claim is about the final prompt the generator reads, at a fixed number of documents. Distracting noise is the worst kind (Ch22 p.11/19); our D-002 has one (C4 D.4). Both claims are unsourced heuristics where they are made, so measure.
  - Turn 2: on the dev split, sweep k, plot CE@k against mean context tokens, compare arms at an equal token budget, and pick the smallest k near the CE plateau (C4 D.6 toy; 07 Part I). Keep answer quality in a separate table (CR-11).
  - Together with a P6 application item scored 3 or more on another day, this can close MC-005 (two check items ≥ 3 on different days, unassisted; misconception log).
- **Use:** CR-13-eligible for C4 L.3. The C4 file has no two-sources scenario; C4-T-01 asks to choose k for drug leaflets (checked).
- **used:**

### S8 · C6 · application item (review use)

- **Turn:** "Three stages each work 9 times in 10. How often does the whole pipeline work?"
- **Source:** AIQ `04-rag-and-retrieval/questions.md` Q3 @ e080df2 (one line of its answer).
- **Source text (verbatim, MIT):**
  > Walk me through every stage of a production RAG pipeline, from raw documents to a cited answer.
- **Line in the repo answer the seed comes from (verbatim, MIT):**
  > errors compound - 90% parsing quality × 90% retrieval recall × 90% faithful generation ≈ 73% end-to-end, so you must instrument and evaluate each stage independently
- **Key:**
  ```
  0.9 × 0.9 × 0.9 = 0.729   (DERIVED)
  ```
  - This assumes the stages fail independently and any failure is fatal. Neither always holds: a memory answer can survive a retrieval miss (06 §7.1, the danger zone), and one cause can break two stages.
  - Self-check: below 0.9 and at least 0.7.
  - Hence measure each stage separately and find the first broken one (C6 D.5).
- **Use:** application item for review from Day 14 on. It does not fill a Transfer slot.
- **used:**

### S9 · C7 · CR-13-eligible

- **Turn:** "Your pandas filter for Chile returns zero rows. What would you check before answering zero?"
- **Source:** AIQ `11-ai-system-design/case-studies/07-text-to-sql-agent.md` @ e080df2, 'Schema retrieval & pruning' and 'Evaluation plan'.
- **Source text (verbatim, MIT):**
  > Build 'ask our data anything' for a company with a large warehouse - PMs and analysts type questions in English, the system answers with correct numbers.
- **Lines the seed comes from (verbatim, MIT):**
  > for low-cardinality columns (they prevent the classic `segment = 'Enterprise'` vs `'enterprise'` filter miss)

  > execution match can false-positive on degenerate results (two wrong queries both returning 0 rows) - flag empty-result matches for manual review.
- **Key:**
  - An empty result may be a filter bug, not a fact. Likely cause: the value is spelled or cased differently.
  - Check: list the column's distinct values before filtering (or compare case-folded), and stay on the computation route: pandas or SQL for counts, not semantic search (02 C7 card).
    ```
    upstream data/customers-100.csv, 100 rows (coach_c7_chile_check.py)
    Country == 'Chile'              → 1 row
    Country == 'chile'              → 0 rows
    Country.casefold() == 'chile'   → 1 row
    distinct Country values: 85; the only one containing "chil" is 'Chile'
    ```
  - A 4 adds the evaluation side: an empty result gets a second look before it counts as an answer.
- **Use:** CR-13-eligible for the C7 lesson, which is not written yet. Keep this scenario out of it when it is written. The 02 C7 card names "how many customers in Chile?" as a routing example, but not the empty-filter bug.
- **used:**

---

## Reserves

Each line: the item, its source, its one-line key. **Reserve: use only in place of a seed** of the same concept, never in addition (the cap).

- **P1** · reserve: use only in place of a seed · "Our whole PDF is about 12,800 tokens; v0 sends about 980. When would you skip retrieval?" (climate version of S1; review-only) · Source: P1 D.3 and D.5 numbers (12,840 o200k tokens; 976) · Key: about 13× (DERIVED); skip only if it fits with an answer reserve and page citations are not needed (Ch1 p.12/14).
- **P1** · reserve: use only in place of a seed · Flashcard "Does any T change the top token in the S7 table?" · Source: P1 D.6, S7 toy · Key: no; dividing every score by the same T > 0 keeps their order, so YES stays on top at every T (0.879 at T = 0.25 in P1 D.6; 0.329 at T = 4 in P1_FACTS S7).
- **P1** · reserve: use only in place of a seed · A 2-merge BPE hand probe, only if MC-001 comes back in the Part A re-run · Source: review idea; no external text · Key: built live from a 3-word toy corpus; no fixed numbers stored here.
- **P1** · reserve: use only in place of a seed · Greedy vs sampled tokens · Source: AE Ch12, 'Model Cascades' · Key: the claim that the model outputs its most likely token holds only under greedy decoding; at T = 1 the S7 toy drew YES 557 times in 1,000, not 1,000 (P1 D.6).
- **P3** · reserve: use only in place of a seed · Two companies in one BM25 index · Source: SDG `06-retrieval-systems/14-production-rag-at-scale.md`, 'Multi-Tenant RAG Isolation' · Key: shared N, n(t) and avgdl mix the two companies' scores (P3 D.1, D.3); give each its own index or its own statistics. Same mechanism as S2.
- **P3** · reserve: use only in place of a seed · "Ticket titles of 3–12 words: does k1 or b matter more?" · Source: AIQ `04-rag-and-retrieval/questions.md` Q12 (follow-up) · Key (corrected): f is almost always 1, so k1's saturation barely acts (at dl = avgdl the tf part is 1 for any k1, P3 D.4); b still matters because titles differ in length. k1 still scales that length effect when dl ≠ avgdl (DERIVED from the P3 D.3 formula).
- **P3** · reserve: use only in place of a seed · AE's 3-ticket toy · Source: AE Ch2, 'Retrieval Fundamentals' (accuracy not checked in the review) · Key: apply the P3 checks: `split()` keeps punctuation (P3 D.5), and a 3-document corpus gives tiny or floored idf values (P3 D.3, J2). Run a re-typed copy before using it; its output is UNVERIFIED.
- **P6** · reserve: use only in place of a seed · The nDCG IDCG critique, in three turns · Source: AE Ch7, 'Normalized Discounted Cumulative Gain (NDCG@k)' · Key: AE builds IDCG from the retrieved documents only; the course builds it from all relevant chunks in the qrels (P6 D.4; J2: 0.2421, not 1.0). Do not teach the ranking flip as general: per review §3b it appears only on a 0–3 grade scale (UNVERIFIED; not re-checked here).
- **P6** · reserve: use only in place of a seed · "A team targets P@5 above 0.8; each question has one gold chunk." · Source: SDG `00-interview-prep/01-question-bank.md` Q5 · Key: the maximum is 1/5 = 0.2 (DERIVED from P6 D.2), so the target is impossible; a P@k target needs the count of relevant chunks.
- **P6** · reserve: use only in place of a seed · The vendor-number critique: Anthropic's 5.7% top-20 figure vs our CE@4 · Source: Source C #31 (01 §6) · Key: per review §8 the 5.7% is 1 − recall@20 over relevant chunks, a different metric and k from CE@4. UNVERIFIED until the coach opens Source C #31.
- **C2** · reserve: use only in place of a seed · A non-terminating chunker, as a variant of C2-A-04 (07) · Source: SDG `01-foundations/02-tokenization-deep-dive.md`, 'Pattern 2: Chunking at Token Boundaries' · Key: once `end` reaches the length, `start = end - overlap` stays below it, so the loop never ends when overlap > 0; break when `end` equals the length, as 07 `fixed_window_chunks` does.
- **C4** · reserve: use only in place of a seed · A second MC-005 variant · Source: AIQ `04-rag-and-retrieval/questions.md` Q48 vs Q50 · Key: Q48 says trimming k often improves quality; Q50 says retrieve generously. Both are unmeasured rules of thumb; pick k by CE@k against tokens on dev (C4 D.6; 07 Part I).

---

## How each seed was checked (2026-10-09)

| Seed | Numbers and cites | Evidence |
|---|---|---|
| All | Every "verbatim, MIT" line is an exact substring of the pinned file; repo commits and copyright lines; book phrases on Ch1 p.12/14 and Ch22 p.11–12/19; AE section headings; course anchors; CR-13 absence checks; no 15-word run shared with AE or the book | `coach_sources.py` → `out_coach_sources.txt` |
| S1 | 976, 71 (P1_FACTS S9, §2); ~1,050 and 24× (DERIVED) | P1 logged run |
| S3 | −0.0859, −0.0478 (P4_FACTS S5); 0.1858 (C4 D.5) | P4, C4 logged runs |
| S4 | 33/33, 26/33, 0/33; 35/35 repeatable | `coach_p5_tie_probe.py` → `out_coach_p5_tie_probe.txt` |
| S5 | R@5 = 0.667, Hit@5 = 1 (P6 Part F); when Recall@k equals Hit@k (DERIVED) | P6 logged run; `coach_sources.py` (enumerates the D.2 formulas) |
| S8 | 0.729 (DERIVED) | arithmetic |
| S9 | 1 row, 0 rows, 85 distinct values | `coach_c7_chile_check.py` → `out_coach_c7_chile_check.txt` |
