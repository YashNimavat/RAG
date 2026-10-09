# Writing style for explanations

**What this is:** how to write every explanation in this course: lesson teaching parts, topic docs, review write-ups, findings and reports.
**What this is not:** the lesson structure (that is the Parts A–M template in [07](../07_SAMPLE_LESSON.md)) or the way questions are asked (one short question with a reply template, 05 §3.1 CR-01).

**Where it came from (2026-10-09).** Yash shared three documents from another project as the model to follow:
- `Design_State_And_Examples.md`: a design write-up that follows one worked example the whole way.
- `What_The_Research_Says.md`: research findings explained in plain language.
- `Part8_Answered.md`: a deep answer to a few specific questions.

The patterns below are taken from those documents.

---

## The one rule

**Show the thing, say what it means, say what it means for you.** Every section moves from a concrete example, to a plain reading of it, to the consequence for the project.

---

## 1. Open with two lines

```
**What this is:** <one sentence>
**What this is not:** <one sentence: the nearby thing a reader might expect>
```

Then lead with the conclusion. A reader who stops after the first screen should already know the answer.

## 2. Explain each finding or concept in the same four beats

| Beat | What goes in it |
|---|---|
| **The setup.** | What was done or measured: the experiment, the lab run, the book page. |
| **The result.** | The numbers, in a code block or a small table. Never buried in a sentence. |
| **What this means.** | One short plain-English paragraph. No new jargon. |
| **For your project:** | The concrete consequence for "Ask My Technical PDFs" (which file, setting, version card or metric changes). |

Example, using a fact already logged in the course (O2 smoke test, session log 2026-10-08 #2):

> **The setup.** We asked `openai/gpt-oss-20b` on Groq to reply "smoke test ok", with `max_tokens=12`.
>
> **The result.**
> ```
> max_tokens = 12,  reasoning on       → reply: ""        (empty)
> max_tokens = 256, reasoning_effort=low → reply: "smoke test ok"
> ```
> **What this means.** A reasoning model thinks before it answers, and the thinking spends the same token budget. A small `max_tokens` can be used up before a single word of the answer appears.
>
> **For your project:** every generation call sets `reasoning_effort="low"` and enough `max_tokens`. Every check asserts on the reply text, not just on "the call succeeded".

## 3. Follow one example the whole way

When explaining a pipeline or a method, take **one** real input and walk it through every step: `Step 1 … Step N`. Show the actual artefact at each step (the chunk text, the scores, the prompt, the answer) in a code block. Do not switch examples halfway.

## 4. Show, don't describe

- Real data in code blocks: scores, ranks, token counts, short text.
- Bar sketches for counts: `✓ B  ███████ 7/15`.
- Side-by-side contrast: a bad version and a good version of the same thing, with margin notes (`← nobody picks this`).
- Small tables, at most 5 columns.

## 5. Name the insight in the heading

Headings say what the reader will learn, not just the topic. Patterns that work:
- "The mistake to avoid first"
- "The transition that's easy to miss"
- "The rule that protects everything else"
- "Why X beats Y"
- "The honest limit"
- "The consequence nobody has said out loud"

## 6. Formula, then numbers, then where to look

Give the formula. Then a table of worked values. Then point at the column or row that matters, and say what it shows ("Read the right-hand column: the second reviewer adds +0.17, the next four add +0.23 between them").

## 7. Say where each claim comes from

Decision and claim tables carry a **Why** column that names the basis: *evidence* (with a cite), *your requirement*, or *reasoning*. This fits the course rule: every number cites a book page (`Ch4 p.3/15`), a notebook cell, a FACTS row or a logged run, or is marked **UNVERIFIED**. Never invent a number to make an example look real.

## 8. State caveats plainly, in their own line

Use `**Caveat, stated plainly:**` or a section called "The honest limit". Say what is a measurement and what is a proxy, and what would change the conclusion.

## 9. Use scorecards when judging a design

```
Backed by the evidence ✅   | what holds up, and why
Knocked down ❌            | what was wrong, and what replaces it
```

## 10. End with decisions and next steps

- "Decisions for you" or "Questions back to you": at most 3, numbered, each answerable in a word or two.
- "Next": the staged plan, saying which step comes first and why.

## 11. Sentences

- Short sentences. One idea each.
- Talk to the reader: "you", "your project".
- **Bold** the one takeaway per section, not whole paragraphs.
- Plain words first; the technical term second, in brackets, the first time it appears.

---

## How this fits the course rules

| Course rule | How the style respects it |
|---|---|
| Copyrighted books (the RAG book, the AI Eval book) | Paraphrase in our own words and cite the page or section. Never quote 15 words or more. |
| MIT repos (ai-system-design-guide, AI-Engineer-Interview-Questions) | Their text may be quoted verbatim, marked as a quote with the MIT notice. Our plain-English wording comes after it. |
| Part A comes first and must not leak answers | The style applies to the teaching parts (D onward), never to the questions in Part A. |
| Questions to the learner | Still one short, plain question per turn with a reply template (05 §3.1 CR-01), not a styled essay. |
| Retrieval quality and answer quality stay separate | "The result" blocks report them in separate rows or tables. |
