# Teaching writing style: plain, connected, sufficient

## Goal

A reader should be able to say **what**, **why**, **how**, **where useful**, and **what it doesn't do** without deciphering a textbook. Write as an attentive teacher, not as a promotional blog, a technical specification, or an A–M course template.

## Narrative pattern (adapt, don't mechanically repeat headings)

1. **Answer first:** a compact plain-language thesis. Show a familiar failure/question before definitions when that helps.
2. **Bridge the prerequisite:** explain the previous concept and the limitation that motivates this one. Never write "TF-IDF is used" without briefly explaining TF-IDF and its relevance if needed.
3. **Introduce correct terms after intuition:** define terms in ordinary language, then retain their technical names and precision.
4. **Follow one example:** progressively extend it through the mechanism, numerical evidence and consequences. Introduce a new example only when the first cannot show the difference.
5. **Make the mechanism causal:** show *why* the result changes; contrast the tempting wrong explanation with the right one.
6. **Ground the result:** if source is research, explain what was studied, what the result actually showed, what it means, and what it means for this learner/project. Distinguish result from inference and recommendation.
7. **Name limitations honestly:** include the important exception, implementation-specific behavior or uncertainty without a long caveat catalogue.
8. **End when clear:** give a succinct takeaway or 1–2 recall/transfer questions where useful. Don't repeat the entire lesson in a conclusion.

## Two connected depths

- **Short — first understanding:** problem, core prerequisite bridge, main idea, intuitive mechanism, one grounded example, use case and major limitation. No long formulas, metadata dumps or unnecessary benchmarks. If a formula is essential to the concept, explain every symbol in plain language.
- **Full — working understanding:** retain the short narrative and add necessary details: exact definitions, derivation, worked computation, library differences, engineering trade-offs, failure/debugging scenarios and source qualification. Don't inflate the page with repetitive examples or compulsory lesson subsections.
- Technical details are **not optional** when removing them would make the explanation misleading (e.g., tokenizer mismatch, BM25 IDF floor, short/long chunk distinction). Place necessary detail in the appropriate mode, or as a small clearly labeled nuance.
- If a topic is inherently simple, short and full may be similarly sized. If huge, split it into coherent lessons with explicit links rather than write a giant full mode.

## Good transformations

**Dense source statement:** "Term frequency contributes a non-linear saturating term, controlled by k1."

**Readable version:** "One mention of a word is strong evidence. The tenth mention adds much less than the first. BM25 makes that drop-off explicit; the parameter `k1` controls how quickly the reward flattens." Then show a small graph or two illustrative values.

**Research explanation pattern:** "The study: what was tested. The result: the relevant measurement, properly qualified. What this means: the mechanism or interpretation. For this project: the decision it informs." Do not fabricate a study or imply correlation establishes causation.

## Avoid

- Glossary-first walls of abbreviations; symbols before intuition; ten examples when one works.
- Empty enthusiasm ("revolutionary", "game-changing"), academic verbosity, verbose intros and decorative summaries.
- Blindly copying all source sections when a coherent, accurate lesson can combine them; or compressing until an essential intermediate idea disappears.
- Confusing "full" with all available background reading, a lab script, dozens of flashcards, or a permanent course plan.
- Presenting toy numbers as evaluation results or extrapolating a handpicked demonstration to general performance.
