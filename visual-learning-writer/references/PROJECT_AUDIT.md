# Project awareness, prerequisites and user approval

## Find material efficiently

1. Determine project root and the topic. Look for `README*`, relevant learning plans, curriculum/index files, `concepts/`, `lessons/`, `study/`, `reading/`, `sources/`, `research/`, notebooks, and source code. Respect repository organization. Do not indiscriminately read every file.
2. Search titles and relevant contents for the target topic, its synonyms and immediate prerequisite terms. Inspect short and full versions when both exist. Record actual paths and sections.
3. Create a *private* coverage map. Report a *small, user-facing* map only for meaningful dependencies. Statuses:
   - **Explained adequately:** exists in context with enough explanation for this lesson; recap and refer to its file/path.
   - **Present but incomplete:** the term appears, but its why/how/illustration is missing or incorrect.
   - **Missing:** absent from checked files; report what was checked, not an absolute claim about the entire project.
   - **Not checked:** project too large or access unavailable; state the limit.
4. Distinguish an explanation being **written** from the learner having **demonstrated** understanding. Use learning records only if present and relevant; never assume a concept is mastered because a file exists.

## Classify connections

- **Essential prerequisite:** reader cannot follow the new idea without it. Include a short, self-contained explanation even if it has a separate prior lesson. For BM25: term frequency, document frequency, inverse document frequency and the TF-IDF comparison all matter when present in the supplied source.
- **Helpful deeper prerequisite:** a derivation or worked exercise that improves depth but is not necessary for the short mode. Offer it if missing/incomplete.
- **Adjacent/future topic:** explain its relationship briefly; link instead of turning the current lesson into a second course.

## Preflight user report (when gaps matter)

Example, after actually checking files:

| Related concept | Existing coverage | Suggested handling |
| --- | --- | --- |
| BM25 | Full lesson found at `concepts/P3_bm25.md` | Brief recap/link |
| Dense retrieval | Existing explanation found | One-paragraph connection |
| RRF | Only mentioned, not explained | Offer a focused explanation |
| Score normalization | Not found in checked files | Optional short note; only if relevant |

"I found two useful gaps: RRF and score normalization. Should I **generate and include both** in the Hybrid Retrieval lesson, **include RRF only**, or **keep just the essential context**?"

Ask once, together, not a series of questions. Explicit user approval of extra explanations is required. A previously supplied instruction like "generate with all prerequisite gaps" counts as approval; don't ask again. Never make a full optional explanation merely because a keyword is absent. Do not delay core teaching for a tangential missing concept.

## When the user approves

Explain requested additions **in the same lesson where the connection matters** or link separate approved output if they ask for it. Preserve a coherent narrative: prerequisite → connection → new concept. Avoid duplicate full lessons, repeated boilerplate, and unsupported claims.

## If no project is available

State "I couldn't inspect existing project explanations here" and work from any user-supplied source. Do not claim a related lesson does not exist. If the user requested content directly and there are no meaningful optional additions, generate the core lesson.
