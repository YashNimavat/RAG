---
name: visual-learning-writer
description: Creates or improves source-grounded, visually clear, prerequisite-aware learning lessons, usually as self-contained interactive HTML with short and full reading depths. Use when the user requests a concept explanation, study lesson, research-to-plain-language teaching, or a rewrite of existing learning content.
argument-hint: "Concept or learning source, e.g. BM25 or Hybrid Retrieval"
---

# Visual Learning Writer

Turn supplied research, books, notes, code and project files into **easy-to-learn explanations**, not long reference dumps. Use the approved lesson in `examples/BM25_Approved_Example.html` as a **quality reference**, never a fixed design template. The user does not need to restate or paste visual-design instructions on future requests. The user's `What_The_Research_Says` and `Part8_Answered` samples define the preferred **plain-language explanation behavior**. Do **not** treat `Design_State_And_Examples` as the writing-style template.

## Workflow (follow in order)

1. **Discover the actual workspace.** Identify the topic and the user-provided sources. Inspect nearby README, learning plan, concepts, research, code and lesson files by filenames/targeted search; read the sections relevant to this topic. Avoid scanning generated/build/vendor directories or pretending all files were read. Use project files over generic recollection. See `references/PROJECT_AUDIT.md`.
2. **Map dependencies.** Identify prerequisite terms, related concepts and existing explanation locations. For each, mark `explained adequately`, `present but incomplete`, `missing`, or `not checked`; record why it matters. Also distinguish *documented* from *learner demonstrated understanding*; do not infer mastery merely from file presence. Include important prerequisites present in the source material (e.g., TF, DF, IDF and TF-IDF before BM25).
3. **Ask about optional additions before generating them.** Briefly present found material and meaningful gaps. Ask one batch question: "Generate the lesson with these missing/incomplete explanations, or keep only the essential background?" Wait for the user's choice where additions are proposed. "Generate", "include these", or equivalent approves them; "skip" declines optional expansion. The user's original request authorizes the *core lesson* but not unsolicited substantial related lessons. If there are no material gaps, or the user already decided, proceed without a redundant question. Explain unavoidable prerequisite basics succinctly even if optional expansions are declined.
4. **Draft the explanation before designing the page.** Follow `references/WRITING_STYLE.md`: problem/question → intuitive explanation → why/how → one sustained, concrete example → boundary/failure → practical relevance. Teach prerequisite bridges in place, not in a detached jargon glossary. Preserve source facts and limits; separate sourced claims, illustrative examples and independent inference.
5. **Design adaptively—automatically, without asking the user to repeat style instructions.** Choose the page structure, color palette, typography, diagrams and interactions for **this topic and learning goal**; do not copy the BM25 theme or layout by default. Maintain readability, accessibility, consistent styling within the lesson and the approved explanation quality. Default to **one self-contained HTML lesson** with Short / Full mode: short is enough to understand the topic; full adds derivations, calculations, implementation specifics and nuanced failure cases where relevant. Use graphs, mind maps, flowcharts, comparison tables or interactive controls **only when they convey something that prose cannot explain as efficiently**. See `references/HTML_VISUAL_SPEC.md`. Keep each section as short as understanding permits, not at an arbitrary word count.
6. **Build and verify.** Write readable semantic HTML/CSS/JS, preferably self-contained and offline. Label toy/example vs measured numbers; test interactive calculations and short/full visibility; check accessibility/responsive layout. Compare the finished lesson to the relevant source sections using `references/QUALITY_CHECK.md`; do not silently drop central prerequisites, contradict source findings or invent experimental results.
7. **Deliver.** Save to the project's existing lesson/output folder if known, otherwise `lessons/<descriptive-topic>.html` (create only the needed output directory). Link or report the exact file path. Briefly state what is covered and any intentionally deferred topics. Do not overwrite source files, alter curriculum plans, or create learning records without user authorization.

## How to invoke

- `/visual-learning-writer BM25` — audit relevant project material; ask about meaningful expansions when needed; generate the lesson.
- `/visual-learning-writer Rewrite my existing RRF explanation` — preserve verified content, improve clarity/visuals and prerequisite links.
- `/visual-learning-writer Explain finding 8 of this research` — teach the requested section in context rather than producing an unrelated course.

## Operating boundaries

- Source fidelity beats flourish: no unverified claims presented as measurements, invented citations, or misleading confidence.
- Missing sources? Say what was and was not found; request the particular missing material only if necessary, otherwise proceed with clearly labeled general explanation.
- Do not browse or add new research unless requested, needed to resolve a substantive source conflict, or necessary to verify a consequential technical fact; label external findings separately.
- No decorative charts, unnecessary quizzes, compulsory A–M chapters, redundant preludes, or compulsory learning-tracker files.
- Reusable visual components can be adapted from the example, but change the subject matter, sample values and explanation to fit the current concept. Different lessons may use different layouts, palettes and visualization types. Never add a diagram solely for decoration.

## Reference loading

- Always read `references/PROJECT_AUDIT.md` before auditing a project; read `references/WRITING_STYLE.md` before drafting; read `references/QUALITY_CHECK.md` before delivery.
- Read `references/HTML_VISUAL_SPEC.md` when making HTML/visuals. Consult `examples/RESEARCH_AND_FOLLOWUP_PATTERN.md` when converting research or answering focused follow-up questions. Inspect `examples/BM25_Approved_Example.html` selectively when implementing the visual style.
