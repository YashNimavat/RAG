# How to use the study kit

**What this is:** your offline way to study every phase. You read a concept, answer its questions closed-book, check yourself against the key points, and reread where you fell short. The website keeps track of your progress, reviews and calibration.
**What this is not:** a replacement for the tutor. When a Claude session is available, the tutor uses the same files and grades your answers itself (see the end of this page).

---

## Start it

From `rag_learning/` in a terminal:

```
uv run python study/app/server.py
```

Your browser opens `http://127.0.0.1:8765`. Or double-click `study/start_study_kit.bat`. It works with no internet and no Claude subscription. Stop it with Ctrl+C.

Prefer the terminal? `uv run python study/quiz.py R1` runs the same quiz there and saves to the same log.

## The loop for one concept

| Step | What you do | Where |
|---|---|---|
| 1. Read | The **short reading file** (book-first) or the **full lesson** (Parts B–K). Tick "read" at the end | Concept page → step 1 |
| 2. Book | Read the pages it names. Page links open the PDF at that page | Step 2 |
| 3. Lab | If the concept has one, open it in VS Code. Labs that call Groq or Cohere need internet and your keys, but no Claude subscription | Step 3 |
| 4. Quiz | **The next day**, closed book: write your answer, choose how sure you are (1–3), then check | Concept page → Start the quiz |
| 5. Reread | For every score of 2 or less, open the "reread" links, then retry at the next review | End of the quiz |

**Why the next day?** An answer given straight after reading only tests short-term memory. A quiz on the same day still saves, but it does not move your review schedule.

## How your score is decided

You do not pick a number. You tick what your answer **really contains**, and the score follows:

| What you ticked | Score |
|---|---|
| One of the "common wrong answers" | at most 1 |
| No key point | 0 |
| Under half of the key points | 1 |
| Half or more, but not all | 2 |
| All the key points | 3 |
| All of them, plus the "for a 4" points | 4 |

- **Hints cost points:** after hint 1 the most you can score is 3, after hint 2 it is 2, after hint 3 it is 1.
- **"I don't know: show me"** scores 0 and brings the question back soon. That is fine: it is better than guessing and ticking generously.

**Be strict with your ticks.** The tutor re-grades a sample later. Your earlier tutor sessions showed a pattern: you were often sure and wrong, and "My stats" tracks exactly that.

## Reviews

The website works out when each concept is due:
- After reading, the first review is **1 day** later.
- Each review day, your **lowest** score sets the next gap:
  - 3 or 4 moves up the ladder `1 → 3 → 7 → 14 → 30 → 60` days;
  - 2 repeats the same gap;
  - 0 or 1 drops back to 1 day.
- A review is 5 questions, weakest first, and always includes at least 1 Application or Transfer question in every 3.
- **Reviews come first** each day (the "Due" tab), then new reading.

## Where your data lives

| File | What it holds |
|---|---|
| `progress/study_attempts.jsonl` | Every answer: your text, confidence, hints, ticks, score |
| `progress/study_state.json` | Your ticks: read, book pages, lab |

Both are plain text. "My stats" → "Download my data" makes a backup. Ask the tutor before committing them to git.

## When a Claude session is available

The tutor protocol stays as before ([05](../05_LEARNING_AND_RETENTION_SYSTEM.md)):
- The tutor asks the same questions from `study/questions/`, one at a time, with the hint ladder.
- The tutor grades with the 0–4 rubrics and logs the session in `progress/session_log.md`.
- The tutor also re-grades a sample of your self-checked answers to check the ticks were strict.
- Tutor-graded scores count toward the mastery levels. Your self-checked levels (L1–L5 on the website) are a guide.

## What the kit contains

The route page shows which concepts have reading files and questions yet. File formats are in [FORMAT.md](FORMAT.md).
