# Portable lesson style: use it in any project

**What this is:** everything a Claude session needs to write explanations and lessons in the same style, structure and visual design as the RAG course's P3 lesson, in **any** project.
**What this is not:** RAG content. Keep the *method* and the *design*; change the subject.

Source of truth: the P3 pilot, `C:\Yash\New-Work\Book RAG\rag_learning\study\lessons\P3_bm25.html`, and its fonts folder `...\study\lessons\fonts\`. Version: 2026-10-17. After Yash's final approval, the same rules also go into the `visual-learning-writer` skill.

---

## Part A: for Yash, how to use this in another project

| Option | What you do | When to use it |
|---|---|---|
| **1. Point a session at this file** | In the other project's session, say: `Read C:\Yash\New-Work\Book RAG\rag_learning\study\PORTABLE_LESSON_STYLE.md and apply it to <topic or file>.` | Quick, one-off |
| **2. Make it that project's rule (recommended)** | Copy this file into the other project, for example `docs/LESSON_STYLE.md`. Add one line to that project's `CLAUDE.md`: `When writing explanations, lessons or study pages, follow docs/LESSON_STYLE.md.` | Every session in that project then follows it automatically |
| **3. A personal skill** (after final approval) | The updated `visual-learning-writer` skill is installed in `C:\Users\Yash\.claude\skills\`. Every project can then use `/visual-learning-writer <topic>` | All projects, no copying |

With option 2, also copy the template files (Part C) into the other project, so its pages work offline there too.

---

## Part B: for the Claude session applying this

Follow every section, in order. Ask Yash only about real preferences, never whether a needed idea belongs in the lesson. If Yash asks for "the plan" or "your approach", give the plan and **wait**.

### B1. Before writing: the gap audit (decides the content)

1. **List every idea the topic uses.** Pull them from the sources (book pages, docs, papers, code), the existing notes, any quiz or exercise, and what the research shows a learner must know.
2. **For each idea:** is it explained *before* it is used? Which topic owns it? Has the learner studied that topic? (Written is not the same as studied.)
3. **Classify each idea:**
   - **core:** teach it fully;
   - **bridge:** needed here, owned elsewhere; teach it briefly, where it is needed;
   - **next:** link only.
4. **Check every question:** each key point of every question or exercise must be answerable from the **Short** version.
5. Keep the audit as a separate file, `<topic>_gap_audit.md`, so the learner can see why each part exists.

### B2. Page structure, top to bottom

1. **Title, and a one-line subtitle.**
2. **The answer first:** about 5 plain sentences that state the whole idea. A reader who stops here still has the core.
3. **The theory in one read:** the whole topic once, as 8–12 numbered, linked ideas in the order they build. Each idea gets 2–4 sentences, its formula or rule if it has one, and a button to its detailed step. No measurements here.
4. **Formula sheet:** cards, one term each, with the formula, a plain one-line meaning, a tiny example, and a link to its step.
5. **Step by step:** one running example followed through every step. Each step goes:
   - a plain explanation;
   - a visual, if it earns its place;
   - the numbers;
   - **Common mistake** (the tempting wrong idea, and the right one);
   - **In your project** (the practical consequence).
6. **Full-only parts** (dashed border): exact definitions, a calculator, edge cases, library differences, engineering defaults, and "the source checked against measurements".
7. **Verify it yourself:** a notebook that rebuilds every number and chart on the page, with checks. It uses Plotly for interactive charts.
8. **Use it on your own data:** a tool that runs the topic's checks on the learner's own data, plus a **real-world checklist** of 8–12 checks, each with "how to check".
9. **LLMOps notebook** (when the project involves LLMs or ML in production): the technique built with a framework, then traced, evaluated, cost-tracked and monitored. Every external call is **cached** (record / replay / auto), so it reruns with no credits.
10. **Check yourself:** 3 quick questions with real feedback, plus a link to the full quiz.
11. **Footer:** where every number comes from, what is added background, and what is UNVERIFIED.

### B3. Writing style (this is non-negotiable)

- **Pattern:**
  1. the answer first;
  2. the background the reader needs, in a sentence or two;
  3. intuition before the technical term;
  4. one example, followed all the way;
  5. *why* it works: contrast the tempting wrong idea with the right one;
  6. ground the result: what was tested, what came out, its limits, what it means for the project;
  7. state the honest limits;
  8. stop when it is clear.
- Plain English, short sentences, one idea each. Talk to the reader as "you". Give the plain word first and the technical term second.
- Use tables for comparisons, code blocks for numbers, and **bold** for the one takeaway per section. Do not use rigid "The setup / The result" labels in lessons.
- **Never invent** a number, page, citation or result. Label every number **measured** (from a real run), **toy** (made-up data) or **formula** (computed).
- **Copyright:** paraphrase books, cite pages, and never copy 15 or more consecutive words. MIT-licensed text may be quoted, with its notice.
- **Short** must be complete for a first understanding. **Full** adds depth, not padding.

### B4. Visual design (copy it exactly from the template)

**Layout:**
- A sticky top bar holds, left to right: **⌂ All phases or topics** (back to the main page) · **☰ Contents** · the title, plus a breadcrumb when the contents panel is hidden · **Short | Full** · the **theme picker** · **☾ Dark / ☀ Light**.
- **There is always a way back.** The ⌂ button, and a "Course" block at the bottom of the contents panel, link to the main page listing every topic, plus the previous and next topics.
  - In the RAG kit, they go to the kit's Route page; opened as a plain file, to `RAG_ROUTE_MAP.html`.
  - In another project, point them at that project's index page (create one if missing).
- **The contents panel is docked to the window edge.** On the left, it touches the left edge and the text starts right beside it, with spare space only on the far right. On the right, it is the mirror image. When hidden, the text is centred.
- The panel shows "On this page", a progress line, and every section, highlighting the current one and scrolling itself to keep it in view. Full-only sections are marked "Full".
- **Contents button, or the T key:** hides or shows the panel on any width. **⇆** moves it left or right. All of these choices are remembered.
- **Phone width (below 980px):** the panel becomes a drawer that closes when you tap the page.
- **A round ↑ button** at the bottom right appears after scrolling.
- Text column: about **68–75 characters per line** (720px in the Reader themes, 800px in the others).

**Themes** (each has Light and Dark; the choice is remembered across lessons):

| Theme | Feel | Fonts |
|---|---|---|
| Reader · Literata | best for long reading: warm paper, small caps, a drop cap | Literata (bundled, OFL), 19px, line height about 1.7 |
| Reader · Atkinson Hyperlegible | the clearest letters | Atkinson Hyperlegible (bundled, OFL) |
| Clean notebook (default) | white or blue, GitHub-like | system sans |
| Textbook | serif, italic section labels | Cambria |
| Editor (VS Code) | `#` headings, an editor palette | Cascadia Code headings |
| Minimal reading | large text, no borders | Charter or Georgia |
| Card catalogue | warm, index-card feel | Palatino |

**Typography rules (from research):** lines of 50–75 characters; line height 1.5 or more; no justified text; dark mode on dark grey (about `#1C1B19`) with off-white text, never pure black or white; numbers in tables as lining, tabular figures.

**Charts:**
- **Hand-drawn inline SVG** in the page; no chart library in lessons. Every chart has a caption saying **what to notice**, plus a measured/toy/formula badge.
- Sliders change the chart *and* a text readout.
- Lines are cut at the chart edge, never drawn flat along it.
- Plotly is used only in the notebooks.

**Offline:** no CDN, no web fonts from the internet, no external scripts. The fonts load from `fonts/` beside the HTML.

---

## Part C: the template files (copy these)

| Copy from | To | Why |
|---|---|---|
| `C:\Yash\New-Work\Book RAG\rag_learning\study\lessons\P3_bm25.html` | `<other project>/lessons/<topic>.html` | The page shell: themes, layout, controls and chart helper |
| `C:\Yash\New-Work\Book RAG\rag_learning\study\lessons\fonts\` (6 `.woff2` files + 2 licences) | `<other project>/lessons/fonts/` | The reading fonts, offline |

**Keep as they are:**
- the whole `<style>` block;
- the early `<script>` in `<head>`, which restores saved choices before the page paints;
- the top bar, the contents panel, the ↑ button;
- these parts of the main script: depth, theme, style, contents panel and side, `spy()`, the back-to-top button, the `chart()` helper, the stacked-bar helper, and the quick-check engine.

**Replace:**
- every `<section>` inside `<main>`, keeping the order in B2 and the section ids used by the panel;
- the `#toc` panel links, to match your sections;
- the topic-specific scripts (in P3: the toy BM25 index, the tokenizer playground, the calculator, the checklist items and the quick-check questions);
- the `data-kit` and `data-book` links. They only work inside the RAG study kit; in another project, use plain relative links.

---

## Part D: before delivering

- The gap audit is done, and every question's key points are answerable from Short.
- Every number is matched against its source run or formula; every citation was opened; the rest is marked UNVERIFIED.
- The copyright check passes: no run of 15 or more words matches a book.
- **The page is tested in a browser:**
  - Short and Full;
  - every theme in Light and Dark;
  - the panel left, right and hidden;
  - the T key and the ↑ button;
  - phone width (390px);
  - every slider and quick check;
  - no console errors, and it works offline.
- The verify notebook runs top to bottom, with all checks passing; the LLMOps notebook replays with no API calls.
- Report to the user in a few lines: what was made, where, and what was checked.
