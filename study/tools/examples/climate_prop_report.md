# Proposition fit check

**What this is:** an automatic check of whether proposition indexing suits these documents: the units, the cost forecast, and code checks of each proposition against its source.
**What this is not:** an evaluation of proposition indexing. No LLM is called; a few questions show the mechanism, not a result.

**Recommendation:** Not decided yet: label at least 30 propositions with the labelling sheet (C5); run --dense with at least 10 labelled questions (arm (a) vs the plain chunks; now 0). The checks above say whether these propositions can be trusted, not whether they help. (section 8). Checklist: C1 ✓ C2 ? C3 ✓ C4 ✓ C5 ? C6 ✗ C7 ✓ C8 ✗ C9 ? C10 ✓ C11 ✓ C12 ?.

## 1 Settings and documents

Documents: `Understanding_Climate_Change.pdf` (33 page(s), 72,593 characters with pages joined by a line break).
Propositions: 40 loaded from 40 record(s), hand-written (not LLM output). Questions: 4.
Settings: prompt prop_gen_v1 (built in) · grading `batched` · k 4 · parents = v0 chunks (1000 characters, overlap 200, per page) · daily quota 200,000 tokens · pymupdf 1.26.7. No API call.

| Number | Status |
|---|---|
| Units, spans, align, parents, coverage, duplicates, 8-gram test | measured on your files by this tool |
| Tokens per call (1,050 in / 1,600 out per page to generate; 1,800 / 1,600 batched grade; 870 / 300 per-proposition grade) | **ASSUMED** (research I4 §9), not measured |
| Prices $0.075 / $0.30 per 1M tokens (Groq openai/gpt-oss-20b); 200,000 tokens per day, 8,000 per minute | CITED (LLMOPS §6.2); the plan row is UNVERIFIED |
| Propositions per sentence 2.254 | CITED (Dense X README: 257M / 114M) |
| Page and prompt tokens (characters × 0.1769) | DERIVED (P1's measured ratio on the climate PDF); a proxy for your text |

## 2 Units

621 sentences and 286 headings (907 units) on 33 page(s); sentences per page min 6 / median 19 / max 22; 614 sentences have at least 4 words. Every unit's offsets give back its text: True.

| Page | Sentences | Headings | Unit ids |
|---|---|---|---|
| 1 | 18 | 8 | 1:0 – 1:25 |
| 2 | 20 | 7 | 2:0 – 2:26 |
| 3 | 20 | 7 | 3:0 – 3:26 |
| 4 | 22 | 8 | 4:0 – 4:29 |
| 5 | 21 | 8 | 5:0 – 5:28 |
| 6 | 21 | 8 | 6:0 – 6:28 |
| 7 | 16 | 9 | 7:0 – 7:24 |
| 8 | 18 | 9 | 8:0 – 8:26 |
| 9 | 21 | 8 | 9:0 – 9:28 |
| 10 | 16 | 11 | 10:0 – 10:26 |
| 11 | 18 | 9 | 11:0 – 11:26 |
| 12 | 18 | 9 | 12:0 – 12:26 |
| 13 | 19 | 8 | 13:0 – 13:26 |
| 14 | 20 | 9 | 14:0 – 14:28 |
| 15 | 19 | 9 | 15:0 – 15:27 |
| 16 | 19 | 9 | 16:0 – 16:27 |
| 17 | 20 | 9 | 17:0 – 17:28 |
| 18 | 18 | 10 | 18:0 – 18:27 |
| 19 | 19 | 7 | 19:0 – 19:25 |
| 20 | 18 | 10 | 20:0 – 20:27 |
| 21 | 20 | 10 | 21:0 – 21:29 |
| 22 | 19 | 9 | 22:0 – 22:27 |
| 23 | 19 | 9 | 23:0 – 23:27 |
| 24 | 19 | 9 | 24:0 – 24:27 |
| 25 | 19 | 9 | 25:0 – 25:27 |
| 26 | 21 | 9 | 26:0 – 26:29 |
| 27 | 18 | 11 | 27:0 – 27:28 |
| 28 | 21 | 10 | 28:0 – 28:30 |
| 29 | 20 | 8 | 29:0 – 29:27 |
| 30 | 18 | 11 | 30:0 – 30:28 |
| 31 | 19 | 9 | 31:0 – 31:27 |
| 32 | 21 | 8 | 32:0 – 32:28 |
| 33 | 6 | 2 | 33:0 – 33:7 |

Known splitter limits on this text (shown, not fixed):
- Page-start fragments (a sentence cut by the page break, starting in lower case): 13:0 'large-scale climate solutions.', 15:0 'goals.', 16:0 'empower communities to take action.', 17:0 'community involvement.', 22:0 'efficiency, and adopting sustainable sup', 23:0 'resources.', 25:0 'infrastructure projects.', 29:0 'coordination across government agencies,'.
- Last sentence of a page with no end punctuation (cut at the page end): 12:26, 14:28, 15:27, 16:27, 21:29, 22:27, 24:27, 28:30.
- 'e.g.' or 'i.e.' would end a sentence early: 0 occurrence(s).

## 3 Forecast for the whole collection

33 pages (one generation call each), 621 sentences → about **1,400 propositions** at Dense X's 2.254 per sentence (about 955 at your file's 1.54).

| Grading | Calls | Tokens (ASSUMED sizes) | $ | Days of 200,000 tokens per day | Minutes at 8,000 per minute, at least |
|---|---|---|---|---|---|
| off | 33 | 87,450 | $0.018 | 0.44 | 11 |
| **batched** | 66 | 199,650 | $0.039 | 1.00 | 25 |
| per-prop | 1,433 | 1,725,450 | $0.236 | 8.63 | 216 |

Per 1k chunks (DERIVED: × 1000 / 97 v0 chunks): off 340 calls, $0.19; batched 680 calls, $0.40; per-prop 14,773 calls, $2.43.

| Embedder | Numbers per vector | Chunks (KiB) | Propositions (KiB) |
|---|---|---|---|
| MiniLM | 384 | 146 | 2,100 |
| Cohere embed-v4.0 default | 1536 | 582 | 8,400 |

Index size = n × dim × 4 bytes: **×14.4 vectors** (1,400 propositions vs 97 chunks).

Prompt `prop_gen_v1 (built in)` on the sample pages (`--render-prompt PAGE` prints one, to run it by hand):

| Page | Units | Page characters | Page tokens (DERIVED) | Rendered prompt characters | about tokens (DERIVED) |
|---|---|---|---|---|---|
| 1 | 26 | 2,424 | 429 | 4,139 | 732 |
| 17 | 29 | 2,144 | 379 | 3,920 | 693 |
| 33 | 8 | 636 | 112 | 2,197 | 389 |

Mean page: about 389 tokens (DERIVED); the ASSUMED generation input is 1,050. Largest rendered prompt: page 29, 4,227 characters, about 748 tokens. The output side (about 45 propositions plus reasoning) is the larger, unmeasured share: size `max_completion_tokens` for it and log `finish_reason=length`.

## 4 Proposition checks

40 propositions; 40 with valid ids; 40 indexed (kept). By page: p.2 6, p.10 25, p.23 5, p.29 4.
- align: min 1.000; below 1: 0 (none).
- Pronoun starts: 0 (none). Resolved names used by 15; not found earlier on the page: none.
- Parents: span inside one chunk for 40/40; 1 parent(s) 34, 2 parent(s) 6 (two parents = the 200-character overlap); primary = the first.
- 40 propositions from 26 source sentences = 1.54 per sentence (Dense X: 2.25).
- Identical normalised texts: 2 group(s): p10-08 = p23-02; p10-09 = p23-03.

| Proposition | Source ids | span(p) | align | Unsupported | Pronoun | Parents | Text |
|---|---|---|---|---|---|---|---|
| p10-01 | 10:2 10:3 | [20,628, 20,765) | 1.000 | - | no | #27 | The United Nations Framework Convention on Climate Change (UNFCCC) is an international treaty. |
| p10-02 | 10:3 | [20,692, 20,765) | 1.000 | - | no | #27 | The UNFCCC is aimed at addressing climate change. |
| p10-03 | 10:4 | [20,766, 20,894) | 1.000 | - | no | #27 | The UNFCCC provides a framework for negotiating specific protocols and agreements. |
| p10-04 | 10:4 | [20,766, 20,894) | 1.000 | - | no | #27 | The UNFCCC provides a framework for negotiating the Kyoto Protocol. |
| p10-05 | 10:4 | [20,766, 20,894) | 1.000 | - | no | #27 | The UNFCCC provides a framework for negotiating the Paris Agreement. |
| p10-06 | 10:5 | [20,895, 20,974) | 1.000 | - | no | #27 | Global cooperation under the UNFCCC is crucial for coordinated climate action. |
| p10-07 | 10:7 | [20,993, 21,180) | 1.000 | - | no | #27 | The Paris Agreement was adopted in 2015. |
| p10-08 | 10:7 | [20,993, 21,180) | 1.000 | - | no | #27 | The Paris Agreement aims to limit global warming to well below 2 degrees Celsius above pre-industrial levels. (dup: p23-02) |
| p10-09 | 10:7 | [20,993, 21,180) | 1.000 | - | no | #27 | Efforts under the Paris Agreement aim to limit the increase in global warming to 1.5 degrees Celsius. (dup: p23-03) |
| p10-10 | 10:8 | [21,182, 21,292) | 1.000 | - | no | #27 | Under the Paris Agreement, countries submit nationally determined contributions (NDCs). |
| p10-11 | 10:8 | [21,182, 21,292) | 1.000 | - | no | #27 | Nationally determined contributions (NDCs) outline countries' climate action plans and targets. |
| p10-12 | 10:11 | [21,331, 21,479) | 1.000 | - | no | #27, #28 | Carbon taxes are a carbon pricing mechanism. |
| p10-13 | 10:11 | [21,331, 21,479) | 1.000 | - | no | #27, #28 | Cap-and-trade systems are a carbon pricing mechanism. |
| p10-14 | 10:11 | [21,331, 21,479) | 1.000 | - | no | #27, #28 | Carbon pricing mechanisms incentivize emission reductions by assigning a cost to carbon emissions. |
| p10-15 | 10:12 | [21,480, 21,603) | 1.000 | - | no | #28 | Carbon pricing policies encourage businesses and individuals to reduce their carbon footprints. |
| p10-16 | 10:12 | [21,480, 21,603) | 1.000 | - | no | #28 | Carbon pricing policies encourage businesses and individuals to invest in cleaner technologies. |
| p10-17 | 10:14 | [21,631, 21,703) | 1.000 | - | no | #28 | Many countries have set ambitious targets for renewable energy adoption. |
| p10-18 | 10:15 | [21,704, 21,819) | 1.000 | - | no | #28 | Renewable energy targets are supported by policies such as subsidies, tax incentives, and mandates for renewable energy use. |
| p10-19 | 10:16 | [21,820, 21,898) | 1.000 | - | no | #28 | Achieving renewable energy targets requires robust infrastructure and market development. |
| p10-20 | 10:18 | [21,932, 22,048) | 1.000 | - | no | #28 | Governments implement regulations to limit emissions from key sectors such as energy, transportation, and industry. |
| p10-21 | 10:19 | [22,049, 22,140) | 1.000 | - | no | #28 | Emission reduction regulations can include efficiency standards, emission caps, and pollution controls. |
| p10-22 | 10:20 | [22,141, 22,205) | 1.000 | - | no | #28, #29 | Enforcement and compliance are critical for the effectiveness of emission reduction regulations. |
| p10-23 | 10:23 | [22,262, 22,371) | 1.000 | - | no | #29 | Cities play a pivotal role in climate action due to their high population densities and economic activities. |
| p10-24 | 10:24 | [22,372, 22,506) | 1.000 | - | no | #29 | Urban climate initiatives include sustainable transportation systems, green building standards, and climate-resilient infrastructure. |
| p10-25 | 10:25 | [22,507, 22,600) | 1.000 | - | no | #29 | Community engagement and participatory planning are essential for successful implementation of urban climate initiatives. |
| p23-01 | 23:25 | [51,016, 51,226) | 1.000 | - | no | #68 | The Paris Agreement is a landmark international accord. |
| p23-02 | 23:25 | [51,016, 51,226) | 1.000 | - | no | #68 | The Paris Agreement aims to limit global warming to well below 2 degrees Celsius above pre-industrial levels. (dup: p10-08) |
| p23-03 | 23:25 | [51,016, 51,226) | 1.000 | - | no | #68 | Efforts under the Paris Agreement aim to limit the increase in global warming to 1.5 degrees Celsius. (dup: p10-09) |
| p23-04 | 23:26 | [51,227, 51,325) | 1.000 | - | no | #68 | Under the Paris Agreement, countries submit nationally determined contributions (NDCs) outlining their climate action plans. |
| p23-05 | 23:27 | [51,326, 51,411) | 1.000 | - | no | #68 | Regular reviews and updates of NDCs are essential for meeting the Paris Agreement's goals. |
| p29-01 | 29:12 | [63,528, 63,671) | 1.000 | - | no | #85 | The Conference of the Parties (COP) is the supreme decision-making body of the United Nations Framework Convention on Climate Change (UNFCCC). |
| p29-02 | 29:13 | [63,672, 63,802) | 1.000 | - | no | #85 | COP meetings bring together representatives from all signatory countries. |
| p29-03 | 29:13 | [63,672, 63,802) | 1.000 | - | no | #85 | At COP meetings, representatives negotiate and review progress on climate agreements. |
| p29-04 | 29:14 | [63,803, 63,873) | 1.000 | - | no | #85 | COP meetings play a crucial role in advancing global climate action. |
| p02-01 | 2:0 | [2,425, 2,547) | 1.000 | - | no | #3 | Coal is the most carbon-intensive fossil fuel. |
| p02-02 | 2:0 | [2,425, 2,547) | 1.000 | - | no | #3 | Coal use for electricity generation is a major source of CO2 emissions. |
| p02-03 | 2:1 | [2,548, 2,634) | 1.000 | - | no | #3 | Coal remains a significant energy source globally, despite a decline in some regions. |
| p02-04 | 2:2 | [2,635, 2,786) | 1.000 | - | no | #3 | Coal is mined extensively in countries like China, India, and the United States. |
| p02-05 | 2:8 | [3,171, 3,288) | 1.000 | - | no | #3, #4 | Natural gas is the least carbon-intensive fossil fuel. |
| p02-06 | 2:8 | [3,171, 3,288) | 1.000 | - | no | #3, #4 | Natural gas is often seen as a "bridge fuel" to a lower-carbon future. |

align counts only ADDED words: a dropped qualifier ("well below" → "below") or a wrong referent passes it. Only a person reading against the source catches those (C5, the labelling sheet).

## 5 Coverage

sentence_coverage on the pages with propositions: 26/75 = 0.347. A page you wrote only in part shows its other sentences as uncovered: that is a property of your sample, not of the method.

| Page | Covered / sentences | sentence_coverage | Uncovered sentences |
|---|---|---|---|
| 2 | 4/20 | 0.200 | 2:4, 2:5, 2:6, 2:9, 2:10, 2:12, 2:13, 2:14, 2:16, 2:17, 2:18, 2:20, 2:21, 2:22, 2:24, 2:25 |
| 10 | 16/16 | 1.000 | none |
| 23 | 3/19 | 0.158 | 23:0, 23:1, 23:3, 23:4, 23:5, 23:7, 23:8, 23:9, 23:12, 23:13, 23:14, 23:16, 23:17, 23:19, 23:20, 23:21 |
| 29 | 3/20 | 0.150 | 29:0, 29:2, 29:3, 29:4, 29:5, 29:7, 29:8, 29:9, 29:16, 29:17, 29:18, 29:20, 29:21, 29:22, 29:25, 29:26, 29:27 |

Uncovered sentences (facts the index would not hold):

- [2:4] Oil is used primarily for transportation fuels, such as gasoline and diesel.
- [2:5] The combustion of oil products releases significant amounts of CO2 and other pollutants, contributing to climate change and air quality issues.
- [2:6] The global oil industry is vast, involving extraction, refining, and distribution, with significant geopolitical and economic implications.
- [2:9] However, its extraction and use still contribute to greenhouse gas emissions, particularly methane, which is a potent greenhouse gas.
- [2:10] Innovations in fracking technology have made natural gas more accessible, but this comes with environmental and health concerns.
- [2:12] Forests act as carbon sinks, absorbing CO2 from the atmosphere.
- [2:13] When trees are cut down for timber or to clear land for agriculture, this stored carbon is released back into the atmosphere.
- [2:14] Deforestation reduces the number of trees that can absorb CO2, exacerbating the greenhouse effect.
- [2:16] Tropical rainforests are particularly important for carbon storage.
- [2:17] Deforestation in the Amazon, Congo Basin, and Southeast Asia has significant impacts on global carbon cycles and biodiversity.
- [2:18] These regions are often cleared for agriculture, logging, and mining, leading to habitat loss and species extinction.
- [2:20] Boreal forests, found in the northern regions of North America, Europe, and Asia, also play a crucial role in sequestering carbon.
- [2:21] Logging and land-use changes in these regions contribute to climate change.
- [2:22] These forests are vital for regulating the Earth's climate and supporting indigenous communities and wildlife.
- [2:24] Agriculture contributes to climate change through methane emissions from livestock, rice paddies, and the use of synthetic fertilizers.
- [2:25] Methane is a potent greenhouse gas with a much higher heat-trapping capability than CO2, albeit in smaller quantities.
- [23:0] resources.
- [23:1] Smart grids enhance grid reliability, reduce energy waste, and support the transition to renewable energy.
- [23:3] IoT devices can optimize energy use in homes, buildings, and industries.
- [23:4] Smart thermostats, lighting systems, and appliances can adjust their operation based on occupancy and usage patterns, reducing energy consumption.
- [23:5] IoT also enables predictive maintenance and efficient resource management.
- [23:7] AI can analyze large datasets to optimize energy systems, predict climate impacts, and enhance climate resilience.
- [23:8] Applications include smart grid management, climate modeling, and precision agriculture.
- [23:9] AI-driven solutions can improve efficiency, reduce costs, and support data-driven decision-making.
- [23:12] CCS technology captures CO2 emissions from industrial processes and power plants and stores it underground.
- [23:13] This technology is critical for reducing emissions from hard-to-abate sectors.
- [23:14] Developing cost-effective and scalable CCS solutions is essential for achieving climate goals.
- [23:16] Utilizing captured CO2 to produce valuable products, such as synthetic fuels, chemicals, and building materials, can create economic opportunities and reduce em
- [23:17] Research into carbon utilization technologies is advancing, with potential applications in various industries.
- [23:19] DAC technology removes CO2 directly from the atmosphere, offering a way to achieve negative emissions.
- [23:20] The captured CO2 can be stored or used in various applications.
- [23:21] Scaling DAC technology and reducing costs are critical for its widespread adoption.
- [29:0] coordination across government agencies, stakeholder engagement, and regular monitoring and evaluation.
- [29:2] Various policy instruments are used to address climate change, including regulations, market- based mechanisms, and voluntary agreements.
- [29:3] Regulations set mandatory standards for emissions and energy efficiency.
- [29:4] Market-based mechanisms, such as carbon pricing and emissions trading, create economic incentives for reducing emissions.
- [29:5] Voluntary agreements encourage businesses and industries to commit to sustainability goals.
- [29:7] Ensuring compliance with climate policies requires robust monitoring and enforcement mechanisms.
- [29:8] This includes tracking emissions, verifying data, and imposing penalties for non-compliance.
- [29:9] Transparent reporting and accountability are essential for maintaining public trust and achieving policy objectives.
- [29:16] Developed countries have committed to providing financial support to developing countries to help them mitigate and adapt to climate change.
- [29:17] Climate finance is essential for implementing projects, building capacity, and fostering sustainable development.
- [29:18] Ensuring adequate and predictable funding is a key focus of international negotiations.
- [29:20] International agreements emphasize the importance of technology transfer and capacity building to support climate action in developing countries.
- [29:21] This includes sharing climate- friendly technologies, providing technical assistance, and enhancing institutional capacities.
- [29:22] Collaborative efforts enhance global resilience and equity.
- [29:25] National and local governments are implementing innovative policies and programs to address climate change.
- [29:26] Examples include renewable energy mandates, green building codes, and sustainable transportation initiatives.
- [29:27] Local leadership is crucial for tailoring solutions to specific contexts and engaging communities in climate action.

gold_reachability: 6/6 = 1.000 gold alternatives are overlapped by some span(p). Arm (b) can never beat it.

## 6 Per question

> **Draft questions:** 4 of 4 are `created_by: llm-draft`: an illustration of the mechanism, not checked labels.

| Question | Type | Needs a relation | Relevant chunks | Propositions on the gold | Text states an expect | Gold groups reachable |
|---|---|---|---|---|---|---|
| D-002: In what year was the Paris Agreement adopted? | factual-single-span | no | #27 | p10-07, p10-08, p10-09 | p10-07 | yes |
| D-003: According to the document, what is essential regarding countries' nati | factual-single-span | no | #68 | p23-05 | p23-05 | yes |
| D-005: How does the document contrast coal and natural gas in terms of carbon | multi-span | yes | #3, #4 | p02-01, p02-02, p02-05, p02-06 | p02-01, p02-02, p02-03, p02-04, p02-05, p02-06 | yes yes |
| D-007: What is the supreme decision-making body of the convention that provid | multi-hop | yes | #27, #85 | p10-01, p10-02, p10-03, p10-04, p10-05, p29-01 | p29-01, p29-02, p29-03, p29-04 | yes yes |

Ranking (arm (a) vs the plain chunks, arm (b), the text check) needs `--dense` (a local MiniLM). Not run here.

## 7 Checklist

| Check | Verdict | Evidence | How to check |
|---|---|---|---|
| C1 Forecast before any call: calls, tokens and $ vs the budget and the daily quota | ✓ | grading batched: 66 calls, 199,650 tokens (ASSUMED per-call sizes), $0.039, 1.00 days of 200,000 tokens per day; no budget given | section 3; replace the ASSUMED sizes with the provider's usage numbers after one recorded page |
| C2 Responses are schema-valid; parse failures and length stops under 2%, logged | ? | 0 of 40 records are invalid (0.0%) and listed in section 4; parse-failure and finish_reason=length rates need the run log of a recorded LLM run (this tool sees only the file) | validate every response against proposition_set_v1; log json_validate_failed and finish_reason=length; never turn a failure into an empty list |
| C3 Every source_id exists; every span lies inside the document | ✓ | 40 of 40 propositions have valid ids, spans inside the text and one page | check every id against the numbered units; span(p) = [min a, max b) must lie inside the text |
| C4 Alignment: every proposition with align(p) < 1 is listed | ✓ | 0 of 40 below 1 (min 1.000); align sees only ADDED words: a dropped qualifier or a wrong referent passes, so read C5 | read each listed proposition against its source; an unsupported word is an added or changed fact until a person says otherwise |
| C5 Hand-checked faithfulness on ≥ 30 propositions, with a Wilson lower bound | ? | no labels yet: write the labelling sheet (--labels-csv), label at least 30 rows, then pass it back with --labels | label supported / added / distorted against the source text; report supported / n with its Wilson interval |
| C6 sentence_coverage ≥ 0.9; sentences with no proposition are listed | ✗ | 26/75 = 0.347 of the sentences on the 4 page(s) with propositions; 49 uncovered sentences are listed in section 5 (a page you wrote only in part counts as uncovered) | every sentence that states a fact needs at least one proposition, or its fact is lost from the index |
| C7 No pronoun-initial propositions (decontextualisation) | ✓ | 0 of 40 start with a pronoun; 15 use a resolved name; every resolved name occurs earlier on its page | replace It / They / These … with the full name used earlier on the page, and list that name in resolved |
| C8 Near-duplicates: distinct-facts@k and the share of duplicate texts | ✗ | 38 distinct normalised texts in 40 propositions (duplicate share 0.050): p10-08 = p23-02; p10-09 = p23-03; distinct-facts@4 needs a ranking (--dense) | identical texts take several top-k places; deduplicate at query time or keep them knowingly (a document that repeats itself) |
| C9 The quality grade is compared with your labels (keep-good, catch-bad, n) | ? | grading batched: needs labels (--labels) and the grader's kept flag in the propositions file | keep-good = kept ∧ good / good; catch-bad = dropped ∧ bad / bad; the grade is a filter, not a faithfulness measurement |
| C10 No eval question or gold quote in the prompt (8-gram test); no book text | ✓ | 0 shared 8-grams between the prompt's template + example and 16 eval texts (96 distinct 8-grams); book text: check by hand (the privacy guard is not built yet) | write the few-shot example from outside your corpus; re-run this test whenever the prompt changes |
| C11 Your questions are mostly single-fact lookups, not compare or summarise | ✓ | 2 of 4 answerable questions need a relation between facts (from type, else wording): D-005, D-007 | propositions lose the relation between facts; check the types by hand |
| C12 The corpus is stable (re-indexing cost on change) | ? | each changed page costs 2 call(s) with grading batched; re-indexing all 33 pages = 66 calls | how often do your documents change? A weekly change multiplies the index cost |

✓ fine · ✗ problem found · ? check by hand.

## 8 Recommendation

Not decided yet: label at least 30 propositions with the labelling sheet (C5); run --dense with at least 10 labelled questions (arm (a) vs the plain chunks; now 0). The checks above say whether these propositions can be trusted, not whether they help.

Order of the rules: C2/C3 broken output → C5/C4 rewritten facts → C11 relation questions → no gain at a high cost (C1) → not enough evidence → no gain → adopt.

Lesson: `study/lessons/I4_propositions.html`. This report is a mechanism check on your data, not an evaluation result.
