# Study kit file formats

**What this is:** the exact format of the reading files and question files in `study/`. The website (`study/app/`) and the quiz program (`study/quiz.py`) both read these files, so a file that breaks the format will not load.
**What this is not:** the lesson template (that is Parts A–M in [07](../07_SAMPLE_LESSON.md)) or the house style (that is [WRITING_STYLE.md](../curriculum/WRITING_STYLE.md)).

Decided by the learner on 2026-10-17: an offline kit for every phase, which a Claude-led session can also use.

---

## 1. Folders

| Path | Holds |
|---|---|
| `concepts/<ID>_<slug>.md` | Full lessons (Parts A–M). Existing P1–C6, plus any later full lessons |
| `study/reading/<ID>_<slug>.md` | Short reading files (book-first) |
| `study/questions/<ID>_questions.md` | One question file per concept. Shared by both lesson depths |
| `progress/study_attempts.jsonl` | Every offline answer, written by the website or the quiz program |
| `progress/study_state.json` | The ticks: reading done, book pages done, lab done |

## 2. Question file

A question file is plain Markdown. Each answer is inside a closed `<details>` block, so the answer stays hidden in VS Code's preview too. HTML comments mark where each question starts and ends.

### 2.1 File header

```markdown
<!-- kit:questions concept=R1 version=1 -->
# R1 questions: sparse vs dense vs hybrid; fusion

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.
```

### 2.2 One question

````markdown
<!-- q id=R1-A-02 type=A set=main -->
### R1-A-02 · Application
**Question:** <one short, plain-English question. Teaching content goes in the reading file, not here.>

**Reply template:** `fused order: ___ , ___ , ___ , ___`

<details><summary>Hint 1</summary>

<H1: direction. Which idea or test case to look at.>

</details>

<details><summary>Hint 2</summary>

<H2: structure. The method skeleton, not the result.>

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** <the answer, in house style. Short. Numbers in a code block.>

**Key points** (a 3 needs every point):
- [ ] <point 1: one checkable fact or step>
- [ ] <point 2>

**For a 4, also:**
- [ ] <the extra the rubric asks for: the mechanism plus a limit (R), a self-check (A), or how to measure it plus when not to use it (T)>

**Common wrong answers:**
- [ ] "<wrong idea, as a learner would say it>": <why it is wrong> (MC-00x if it matches the misconception log)

**If you missed it, reread:** [short §3](../reading/R1_hybrid_fusion.md#3-...) · [full D.2](../../concepts/R1_hybrid_fusion.md#d2-...) · book Ch12 p.7–9/14

</details>
<!-- /q -->
````

### 2.3 Field rules

| Field | Rule |
|---|---|
| `id` | `<concept>-<type>-<nn>`; pre-test items use `<concept>-PRE-<nn>`; cross-concept items use `X-T-<nn>` |
| `type` | `R` recall, `A` application, `T` transfer ([05 §4.1](../05_LEARNING_AND_RETENTION_SYSTEM.md#41-definitions-and-item-types)) |
| `set` | `pre` (optional cold check before reading), `main` (after reading), `review` (extra items for later reviews), `interview` |
| Hints | Hint 1 and Hint 2 are required. Hint 3 (a worked step) is optional, for `A` items only |
| Key points | 2–5 checkable points. Each is one fact or step that a reader can tick yes or no |
| For a 4 | 1–2 points, following the 0–4 rubrics in [05 §4.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#42-graded-rubrics-04) |
| Common wrong answers | 1–3. Phrase them as the learner would. Name the MC id if one matches |
| Reread | At least one link into the reading (short and/or full), plus the book page |
| Interview items | `set=interview`. The id continues the concept's normal numbering (e.g. `R1-R-06`). Add `source=` with the repo question (e.g. `source=AIQ-04-Q24`). Put the verbatim repo question and its notice in the **Question** field: *"From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `<path>`, Copyright (c) 2026 Om, MIT License"*. Put the repo's own answer, quoted, at the start of "Show answer", before **Model answer:** (the kit shows it as a preamble). Our checked answer follows |
| Interview wording | A verbatim repo question may be longer than one sentence. It is the only exception to the one-sentence rule |
| Other external items | A scenario adapted from an MIT repo also gets `source=`, plus a one-line italic credit with the MIT notice inside the model answer. A concept has at most 2 external items in total, interview items included |
| **Hidden seeds** | **Never** put an item from `sources/coach/transfer_seed_bank.md` (seeds or reserves) into a kit file or a lesson. Those scenarios stay unseen, so that the tutor can use them for scored Transfer checks (CR-13). Write new scenarios for the kit instead |
| `set=review` items | List them in the full lesson's Part L (as L.5) or Part M.2, with the same id |
| Data for an item | Put tables or lists the learner needs inside the **Question** field, after the question sentence and before **Reply template:** |
| Inside the answer | In Key points, For a 4 and Common wrong answers, every line must be a `- [ ]` item or an indented continuation of one. Other lines there are dropped. Never nest a `<details>` inside a question |
| Page references | Book pages are always written `ChN p.x/y` (or `App p.x/y`, `Intro p.x/y`); the website links them to the PDF. Write pages of any other PDF as "page N" |

Anchors follow GitHub's rule: lower-case, punctuation removed, each space becomes `-`. `### D.6 Reciprocal rank fusion` becomes `#d6-reciprocal-rank-fusion`. Version numbers lose their dots too: `rank_bm25 0.2.2` becomes `rank_bm25-022`. Check anchors with the concept's `*_md_check.py`, or open the link in the website.

### 2.4 How a self-check becomes a score

The website and the quiz program compute the score from your ticks. You do not choose the number (05 §4.2: no self-rating).

| Ticks | Score |
|---|---|
| Ticked a "common wrong answer" | at most 1 |
| No key point | 0 |
| Some key points, under half | 1 |
| Half or more, but not all | 2 |
| All key points | 3 |
| All key points + every "for a 4" point | 4 |

The hint caps from 05 CR-05 apply on top: Hint 1 seen → at most 3, Hint 2 → at most 2, Hint 3 → at most 1. Opening the answer without writing anything counts as assisted, scored 0.

Every offline score is stored with `"grader": "self"`. When a Claude session is available, the tutor re-grades a sample of saved answers, to check for marking that is too generous.

## 3. Reading file (short depth)

```markdown
<!-- kit:reading concept=R1 depth=short version=1 -->
# R1: <title>

**What this is:** ...
**What this is not:** ...

> **Read in the book:** Ch12 p.1–2/14, p.5–12/14. Read after §1.

## 1. <the failure this fixes>
## 2. ... (house style: setup → result → what it means → for your project)
## N. When not to use it
## Check yourself
→ `study/questions/R1_questions.md`
```

Book text is never copied: use our own words and page pointers, and never quote 15 words or more. Length: about 1,800–3,000 words, not counting code blocks.

## 4. Attempt log (written by the tools; do not edit by hand)

One JSON object per line in `progress/study_attempts.jsonl`:

```json
{"ts":"2026-10-17T10:02:11","date":"2026-10-17","qid":"R1-A-02","concept":"R1","type":"A","set":"main",
 "answer":"...","confidence":3,"hint_level":0,"key_hit":[0,1],"key_total":2,"four_hit":[],"four_total":1,
 "wrong_hit":[],"score":3,"grader":"self","mode":"web"}
```

The review schedule is not stored. It is recomputed from this log with the 05 §5.2 rule: the lowest score of the day sets the step on the ladder `1 → 3 → 7 → 14 → 30 → 60`.
