# Self-contained visual HTML lessons

## Delivery preference

Default to one browser-openable `.html` with inline CSS and JavaScript, no network/CDN dependency, and no build step. Prefer semantic sections and accessible controls. Use Markdown only when asked or when the environment cannot deliver HTML. Treat `examples/BM25_Approved_Example.html` as a benchmark for **clarity, visual usefulness and working interaction**, not as a style guide to reproduce. For every new topic, choose the layout, color palette, typography, diagrams and interactions that communicate **that topic** best. Use readable spacing, legible typography, sufficient contrast and cohesive styling throughout the current lesson.

## Adaptive visual design (automatic default)

- **No repeated prompting:** Apply these decisions on every invocation of the skill. The user does not need to paste or remind Claude of this rule.
- **Choose, do not clone:** The BM25 lesson is an example of quality; never copy its palette, blocks, chart types or visual hierarchy merely for consistency with the example.
- **Match the concept:** Numerical relations may need graphs; systems may need flowcharts; conceptual relations may need mind maps; comparisons may need tables; some concepts should be mostly prose. Choose one useful visual over many decorative ones.
- **Allow different presentations across lessons:** A research-summary lesson may look different from an engineering tutorial or a thinking-skills lesson. Keep strong readability and design consistency *within* each page, not a forced uniform look across every topic.
- **Accessible by default:** Use sufficient contrast, legible text, visible focus, mobile-friendly layout and color-independent labeling. For dynamic visuals, provide a textual explanation of what the user should notice.

## Structure

- Title, 2–3 line answer-first overview, and an optional short learning map.
- Short / Full control: **Short** exposes complete essential explanations, **Full** reveals deeper sections without removing earlier required context. Maintain accurate anchor behavior and keyboard-accessible toggle.
- Related concepts: link existing project material using relative links when feasible. If a linked markdown file won't render in the browser, give a human-readable path and/or a link to an exported HTML version; don't promise a working link without checking.
- Main body: causal explanation with one continuous example and short section headers based on actual concepts; do not force fixed chapters.
- Optional one-check recap or self-test (user can answer and get real feedback). If quiz is complex, keep it separate.

## Choose the visual by information need

| Understanding need | Visual | Example |
| --- | --- | --- |
| How value responds to a parameter | Interactive 2D graph | BM25 frequency saturation as `k1` changes |
| Hierarchy or conceptual relations | Mind map/relationship diagram | TF / DF / IDF -> TF-IDF -> BM25 |
| A procedure or decision | Flowchart | Query -> tokenize -> match -> score -> rank |
| Choice between alternatives | Comparison table or aligned bars | Sparse vs dense retrieval |
| Progression over time | Timeline | Iterative training or a historical sequence |
| A calculation or algorithm | Annotated worked example | Calculate one term score by hand |
| Nothing truly visual | Text alone | Plain-language definition or misconception |

A diagram must have an explanatory caption and accessible text counterpart. Use SVG for sharp responsive charts, labeled axes and interactive states. Distinguish measured vs illustrative values directly in chart subtitles/captions. Do not choose arbitrary numerical curves. When possible derive points from the actual disclosed formula or source data.

## Interaction requirements

- A slider or toggle must cause a real, visible change in the chart/result. Labels and current values update together.
- Do not display fake buttons, disconnected controls or decorative interactions.
- Guard against divide-by-zero, NaN and invalid parameter combinations. Apply domain restrictions consistent with the selected library; don't imply all BM25 implementations behave identically.
- Keyboard accessible labels, visible focus, responsive layout; use color **plus** text/shape rather than color alone.
- Formula notes: define symbols and defaults, give one meaningful computation, and cite the implementation/version when behavior depends on it.
- Test the HTML in a browser when a browser/testing facility is available; otherwise do static checks and state what wasn't verified. Don't assert that interactions were tested if they weren't.

## File size and maintainability

No arbitrary limit. Prefer simple inline vanilla JS/CSS in the standalone lesson. Avoid bundling large third-party frameworks solely to draw a mind map or 2D chart. If the project already has its own lesson CSS/components, reuse them when suitable while maintaining offline exports if requested.
