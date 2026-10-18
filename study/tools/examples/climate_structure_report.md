# Structure fit check

**What this is:** an automatic check of whether structure-aware chunking (cut at the document's own headings) works on these PDFs, and with what split level, measured on your own files.
**What this is not:** a retrieval evaluation. Whether the structure chunks retrieve better is an experiment (CE@k at fixed k and at equal budget, by bucket).

**Recommendation:** Typography route (size + bold) at split level L3: the deepest level whose median section >= 400 characters (median 1,033.5) (section 11). Checklist: S1 PASS S2 PASS S3 PASS S4 MANUAL S5 MANUAL S6 PASS S7 PASS S8 PASS S9 WARN S10 MANUAL S11 PASS.

Settings: cap 1,000 characters, no overlap inside a unit · split level auto · min-chars 400 · sample 10, seed 0 · eval set `climate_seed_spans.jsonl` · baseline v0 = per-page recursive 1000/200 · pymupdf 1.26.7, `page.get_text()`, pages joined with `"\n"`. No API call.
Documents: `Understanding_Climate_Change.pdf` (id `climate`, 33 page(s), 72,593 characters, snapshot_id `ea07572562ac`).

## 1 Fonts and body size

| Size | Bold | Characters | Share |
|---|---|---|---|
| 24.00 | yes | 28 | 0.0% |
| 18.00 | yes | 855 | 1.2% |
| 13.56 | yes | 1,666 | 2.4% |
| 12.00 | yes | 4,057 | 5.8% |
| 12.00 | no | 63,762 | 90.6% |
| 11.04 | no | 0 | 0.0% |

Body size: **12.0** (the size with the most characters: 67,819 of 70,368). Spans per size: 12.0 → 1,006, 13.56 → 68, 18.0 → 22, 24.0 → 1. Pages without a text layer: none.

## 2 Structure sources

- Outline (`get_toc()`): 0 entries (no outline).
- Tags: StructTreeRoot present; MarkInfo Marked true (read-only: this tool does not use the tags).
- Creator: Microsoft® Word 2021; producer: Microsoft® Word 2021.

## 3 Headings

Text lines 1,097 · all-bold lines 283 · bold lines with more than one span 0.

| Level | Font | Size only | Size + bold |
|---|---|---|---|
| L1 | 24.00 bold | 1 | 1 |
| L2 | 18.00 bold | 21 | 21 |
| L3 | 13.56 bold | 68 | 68 |
| L4 | 12.0 bold (body size) | 0 | 192 |
| all | | **90** | **282** |

Size only misses **192 of 282** (68.1%): bold lines at the body size.
Wrapped headings joined: 1: p.7 'Chapter 5: The Role of Technology in Climate Change Mitigation' (2 lines).
Bold lines removed by the filters (> 12 words or a final . ! ?): 0.
Lines repeated on >= 3 pages (never headings): 0.
Numbered headings: 21; numbering depth → level: 1 → L2 (consistent).

The headings size only misses (first 30 of 192; read them for S4):

- p.1 L4 Fossil Fuels
- p.1 L4 Coal
- p.2 L4 Oil
- p.2 L4 Natural Gas
- p.2 L4 Tropical Deforestation
- p.2 L4 Boreal Forests
- p.2 L4 Livestock Emissions
- p.3 L4 Rice Cultivation
- p.3 L4 Fertilizers
- p.3 L4 Heatwaves
- p.3 L4 Changing Seasons
- p.3 L4 Polar Ice Melt
- p.4 L4 Glacial Retreat
- p.4 L4 Coastal Erosion
- p.4 L4 Hurricanes and Typhoons
- p.4 L4 Droughts
- p.4 L4 Flooding
- p.4 L4 Coral Reefs
- p.5 L4 Marine Ecosystems
- p.5 L4 Solar Power
- p.5 L4 Wind Power
- p.5 L4 Hydroelectric Power
- p.5 L4 Building Efficiency
- p.6 L4 Transportation Efficiency
- p.6 L4 Industrial Efficiency
- p.6 L4 Reforestation Projects
- p.6 L4 Afforestation Initiatives
- p.6 L4 International Agreements
- p.6 L4 National Policies
- p.7 L4 Local Initiatives
- … 162 more (`--json` lists all headings)

## 4 Layout: columns and tables

- Two-column pages (text blocks of 40+ characters starting in both halves): none.
- Right-to-left jumps (a line in the right half followed by one in the left half): most on one page 0.
- Ruled tables (`find_tables()`): none.

## 5 Alignment and the outline

`dict` lines, each + `"\n"`, rebuild `get_text()` on **33 of 33** pages. Aligned **282 of 282** headings (cursor + find); 282 lie on their own page.

Repeated titles: **11** (the path, not the title, identifies a section).

| Title | Page | Level | Parent path |
|---|---|---|---|
| Carbon Capture and Utilization | 8 | L3 | Understanding Climate Change > Chapter 5: The Role of Technology in Climate Change Mitigation |
| Carbon Capture and Utilization | 23 | L3 | Understanding Climate Change > Chapter 15: Climate Change and Technology |
| Carbon Utilization | 8 | L4 | Understanding Climate Change > Chapter 5: The Role of Technology in Climate Change Mitigation > Carbon Capture and Utilization |
| Carbon Utilization | 23 | L4 | Understanding Climate Change > Chapter 15: Climate Change and Technology > Carbon Capture and Utilization |
| International Agreements | 6 | L4 | Understanding Climate Change > Chapter 4: Mitigation and Adaptation > Climate Policy |
| International Agreements | 23 | L3 | Understanding Climate Change > Chapter 16: Global Cooperation and Governance |
| International Collaboration | 10 | L3 | Understanding Climate Change > Chapter 6: Global and Local Climate Action |
| International Collaboration | 16 | L4 | Understanding Climate Change > Chapter 10: Climate Change and Human Health > Global Health Initiatives |
| Marine Ecosystems | 5 | L4 | Understanding Climate Change > Chapter 3: Effects of Climate Change > Ocean Acidification |
| Marine Ecosystems | 13 | L4 | Understanding Climate Change > Chapter 9: Climate Change and Biodiversity > Impact on Ecosystems |
| Nature-Based Solutions | 14 | L4 | Understanding Climate Change > Chapter 9: Climate Change and Biodiversity > Integrating Biodiversity and Climate Action |
| Nature-Based Solutions | 26 | L3 | Understanding Climate Change > Chapter 17: Building Climate Resilience |
| Paris Agreement | 10 | L4 | Understanding Climate Change > Chapter 6: Global and Local Climate Action > International Collaboration |
| Paris Agreement | 23 | L4 | Understanding Climate Change > Chapter 16: Global Cooperation and Governance > International Agreements |
| Policy and Governance | 12 | L3 | Understanding Climate Change > Chapter 8: Future Directions and Innovations |
| Policy and Governance | 18 | L4 | Understanding Climate Change > Chapter 12: The Path Forward > Taking Action |
| Research and Innovation | 7 | L3 | Understanding Climate Change > Chapter 4: Mitigation and Adaptation |
| Research and Innovation | 16 | L4 | Understanding Climate Change > Chapter 10: Climate Change and Human Health > Global Health Initiatives |
| Smart Grids | 8 | L4 | Understanding Climate Change > Chapter 5: The Role of Technology in Climate Change Mitigation > Energy Storage and Grid Management |
| Smart Grids | 22 | L4 | Understanding Climate Change > Chapter 15: Climate Change and Technology > Digital Technologies |
| Youth Engagement | 13 | L4 | Understanding Climate Change > Chapter 8: Future Directions and Innovations > Social and Cultural Change |
| Youth Engagement | 32 | L4 | Understanding Climate Change > Chapter 21: Climate Change and Cultural Shifts > Intergenerational Dialogue |

The outline down to the split level L3 (offset, page, section length; deeper headings counted):

```text
L1 Understanding Climate Change  @0  p.1  72,593 chars
  L2 Chapter 1: Introduction to Climate Change  @30  p.1  1,591 chars
    L3 Historical Context  @467  p.1  605 chars
    L3 Modern Observations  @1,072  p.1  549 chars
  L2 Chapter 2: Causes of Climate Change  @1,621  p.1  4,096 chars
    L3 Greenhouse Gases  @1,658  p.1  1,898 chars  (+4 deeper)
    L3 Deforestation  @3,556  p.2  987 chars  (+2 deeper)
    L3 Agriculture  @4,543  p.2  1,174 chars  (+3 deeper)
  L2 Chapter 3: Effects of Climate Change  @5,717  p.3  4,160 chars
    L3 Rising Temperatures  @5,904  p.3  831 chars  (+2 deeper)
    L3 Melting Ice and Rising Sea Levels  @6,735  p.3  1,111 chars  (+3 deeper)
    L3 Extreme Weather Events  @7,846  p.4  1,140 chars  (+3 deeper)
    L3 Ocean Acidification  @8,986  p.4  891 chars  (+2 deeper)
  L2 Chapter 4: Mitigation and Adaptation  @9,877  p.5  6,058 chars
    L3 Renewable Energy  @10,225  p.5  1,054 chars  (+3 deeper)
    L3 Energy Efficiency  @11,279  p.5  1,135 chars  (+3 deeper)
    L3 Reforestation and Afforestation  @12,414  p.6  881 chars  (+2 deeper)
    L3 Climate Policy  @13,295  p.6  1,210 chars  (+3 deeper)
    L3 Research and Innovation  @14,505  p.7  1,430 chars  (+3 deeper)
  L2 Chapter 5: The Role of Technology in Climate Change Mitigation  @15,935  p.7  4,620 chars
    L3 Advanced Renewable Energy Solutions  @16,000  p.7  1,007 chars  (+3 deeper)
    L3 Energy Storage and Grid Management  @17,007  p.8  935 chars  (+3 deeper)
    L3 Carbon Capture and Utilization  @17,942  p.8  654 chars  (+2 deeper)
    L3 Sustainable Transportation  @18,596  p.9  1,091 chars  (+3 deeper)
    L3 Sustainable Agriculture and Land Use  @19,687  p.9  868 chars  (+3 deeper)
  L2 Chapter 6: Global and Local Climate Action  @20,555  p.10  2,728 chars
    L3 International Collaboration  @20,599  p.10  695 chars  (+2 deeper)
    L3 National Strategies  @21,294  p.10  913 chars  (+3 deeper)
    L3 Local and Community Initiatives  @22,207  p.10  1,076 chars  (+3 deeper)
  L2 Chapter 7: The Economics of Climate Change  @23,283  p.11  1,744 chars
    L3 Costs of Inaction  @23,327  p.11  730 chars  (+2 deeper)
    L3 Benefits of Climate Action  @24,057  p.11  970 chars  (+3 deeper)
  L2 Chapter 8: Future Directions and Innovations  @25,027  p.12  3,423 chars
    L3 Emerging Technologies  @25,073  p.12  982 chars  (+3 deeper)
    L3 Policy and Governance  @26,055  p.12  1,081 chars  (+3 deeper)
    L3 Social and Cultural Change  @27,136  p.13  1,314 chars  (+3 deeper)
  L2 Chapter 9: Climate Change and Biodiversity  @28,450  p.13  3,083 chars
    L3 Impact on Ecosystems  @28,494  p.13  1,024 chars  (+3 deeper)
    L3 Conservation Strategies  @29,518  p.14  982 chars  (+3 deeper)
    L3 Integrating Biodiversity and Climate Action  @30,500  p.14  1,033 chars  (+3 deeper)
  L2 Chapter 10: Climate Change and Human Health  @31,533  p.15  3,336 chars
    L3 Health Impacts  @31,578  p.15  1,493 chars  (+4 deeper)
    L3 Health Adaptation Strategies  @33,071  p.15  1,087 chars  (+3 deeper)
    L3 Global Health Initiatives  @34,158  p.16  711 chars  (+2 deeper)
  L2 Chapter 11: Education and Advocacy  @34,869  p.16  3,025 chars
    L3 Climate Education  @34,905  p.16  1,014 chars  (+3 deeper)
    L3 Advocacy and Activism  @35,919  p.17  1,004 chars  (+3 deeper)
    L3 Media and Communication  @36,923  p.17  971 chars  (+3 deeper)
  L2 Chapter 12: The Path Forward  @37,894  p.17  3,334 chars
    L3 Vision for a Sustainable Future  @37,925  p.18  1,025 chars  (+3 deeper)
    L3 Taking Action  @38,950  p.18  950 chars  (+3 deeper)
    L3 Commitment to Future Generations  @39,900  p.18  1,328 chars  (+3 deeper)
  L2 Chapter 13: Climate Change and Social Justice  @41,228  p.19  3,416 chars
    L3 Climate Justice  @41,275  p.19  1,181 chars  (+3 deeper)
    L3 Indigenous Knowledge and Leadership  @42,456  p.20  1,113 chars  (+3 deeper)
    L3 Gender and Climate Change  @43,569  p.20  1,075 chars  (+3 deeper)
  L2 Chapter 14: Climate Change and the Economy  @44,644  p.20  3,166 chars
    L3 Economic Transformation  @44,688  p.20  1,034 chars  (+3 deeper)
    L3 Job Creation and Workforce Development  @45,722  p.21  1,056 chars  (+3 deeper)
    L3 Sustainable Business Practices  @46,778  p.21  1,032 chars  (+3 deeper)
  L2 Chapter 15: Climate Change and Technology  @47,810  p.22  3,116 chars
    L3 Clean Energy Technologies  @47,853  p.22  1,141 chars  (+3 deeper)
    L3 Digital Technologies  @48,994  p.22  997 chars  (+3 deeper)
    L3 Carbon Capture and Utilization  @49,991  p.23  935 chars  (+3 deeper)
  L2 Chapter 16: Global Cooperation and Governance  @50,926  p.23  4,235 chars
    L3 International Agreements  @50,973  p.23  1,073 chars  (+3 deeper)
    L3 Regional and National Initiatives  @52,046  p.24  1,061 chars  (+3 deeper)
    L3 Global Climate Finance  @53,107  p.24  1,005 chars  (+3 deeper)
    L3 Capacity Building and Technology Transfer  @54,112  p.25  1,049 chars  (+3 deeper)
  L2 Chapter 17: Building Climate Resilience  @55,161  p.25  4,108 chars
    L3 Resilient Infrastructure  @55,202  p.25  998 chars  (+3 deeper)
    L3 Community Resilience  @56,200  p.26  927 chars  (+3 deeper)
    L3 Nature-Based Solutions  @57,127  p.26  1,111 chars  (+3 deeper)
    L3 Innovative Adaptation Strategies  @58,238  p.27  1,031 chars  (+3 deeper)
  L2 Chapter 18: Moving Forward Together  @59,269  p.27  2,928 chars
    L3 Collective Action  @59,306  p.27  976 chars  (+3 deeper)
    L3 Hope and Inspiration  @60,282  p.27  941 chars  (+3 deeper)
    L3 Vision for the Future  @61,223  p.28  974 chars  (+3 deeper)
  L2 Chapter 19: Climate Change and Policy  @62,197  p.28  3,568 chars
    L3 Policy Development and Implementation  @62,236  p.28  1,223 chars  (+3 deeper)
    L3 International Climate Negotiations  @63,459  p.29  1,170 chars  (+3 deeper)
    L3 National and Local Leadership  @64,629  p.29  1,136 chars  (+3 deeper)
  L2 Chapter 20: Climate Change and Innovation  @65,765  p.30  3,323 chars
    L3 Technological Innovation  @65,808  p.30  1,111 chars  (+3 deeper)
    L3 Social Innovation  @66,919  p.30  1,107 chars  (+3 deeper)
    L3 Governance Innovation  @68,026  p.31  1,062 chars  (+3 deeper)
  L2 Chapter 21: Climate Change and Cultural Shifts  @69,088  p.31  3,505 chars
    L3 Changing Cultural Narratives  @69,136  p.31  1,078 chars  (+3 deeper)
    L3 Educational Initiatives  @70,214  p.32  1,044 chars  (+3 deeper)
    L3 Intergenerational Dialogue  @71,258  p.32  1,335 chars  (+3 deeper)
```

## 6 Chunks per split level

| Level | Sections | Length min / median / max | Mean | Median >= min-chars |
|---|---|---|---|---|
| L1 | 1 | 72,593 / 72,593 / 72,593 | 72,593.0 | yes |
| L2 | 21 | 1,591 / 3,336 / 6,058 | 3,455.4 | yes |
| L3 | 68 | 549 / 1,033.5 / 1,898 | 1,041.3 | yes |
| L4 | 192 | 243 / 334 / 636 | 336.5 | no |

Split level: **L3** (auto: the deepest level whose median section >= 400).

| Arm | Chunks | Length min / median / max | Mean | On 2+ pages | Units split | Merged | Under 400 | Over cap | Histogram (100-char bins) |
|---|---|---|---|---|---|---|---|---|---|
| v0 per-page 1000/200 | 97 | 393 / 935 / 1,000 | 857.9 | 0 | - | 0 | 1 | - | 0,0,0,1,0,9,13,5,3,66 |
| cross-page recursive 1000/200 | 92 | 755 / 962.5 / 999 | 954.8 | 41 | - | 0 | 0 | - | 0,0,0,0,0,0,0,1,1,90 |
| L1 | 73 | 767 / 1,000 / 1,000 | 994.4 | 32 | 1 | 0 | 0 | 0 | 0,0,0,0,0,0,0,1,1,71 |
| L2 | 86 | 644 / 843.5 / 1,000 | 844.1 | 29 | 21 | 0 | 0 | 0 | 0,0,0,0,0,0,9,27,17,33 |
| L2 + merge<400 | 86 | 644 / 843.5 / 1,000 | 844.1 | 29 | 21 | 0 | 0 | 0 | 0,0,0,0,0,0,9,27,17,33 |
| **L3** | 117 | 187 / 619 / 997 | 620.5 | 27 | 46 | 0 | 19 | 0 | 0,1,0,18,16,18,29,15,6,14 |
| L3 + merge<400 | 117 | 187 / 619 / 997 | 620.5 | 27 | 46 | 0 | 19 | 0 | 0,1,0,18,16,18,29,15,6,14 |
| L4 | 209 | 187 / 338 / 636 | 347.3 | 24 | 0 | 0 | 184 | 0 | 0,1,40,143,19,2,4,0,0,0 |
| L4 + merge<400 | 139 | 187 / 545 / 772 | 522.3 | 25 | 0 | 70 | 44 | 0 | 0,1,7,36,19,17,34,25,0,0 |
| L3, size-only headings | 117 | 187 / 619 / 997 | 620.5 | 27 | 46 | 0 | 19 | 0 | 0,1,0,18,16,18,29,15,6,14 |

v0 and the cross-page control are per-page / whole-text recursive 1000/200 (with overlap), for comparison. Structure arms have no overlap; a merged chunk joins small sibling units.

At L3, the size-only headings give **the same chunks** as size + bold.

Invariants (round trip `doc_text[a:b] == text`, cap, gaps, crossing a split-level boundary, page segments):

| Arm | Round trip | Cap | Gaps | Crossing | Segments |
|---|---|---|---|---|---|
| L1 | 0 | 0 | 0 | 0 | 0 |
| L2 | 0 | 0 | 0 | 0 | 0 |
| L2 + merge<400 | 0 | 0 | 0 | 0 | 0 |
| L3 | 0 | 0 | 0 | 0 | 0 |
| L3 + merge<400 | 0 | 0 | 0 | 0 | 0 |
| L4 | 0 | 0 | 0 | 0 | 0 |
| L4 + merge<400 | 0 | 0 | 0 | 0 | 0 |
| L3, size-only headings | 0 | 0 | 0 | 0 | 0 |

## 7 Page breaks

Orphaned headings (a page ends in a heading): **16**: 1->2, 2->3, 3->4, 4->5, 5->6, 6->7, 7->8, 8->9, 10->11, 11->12, 17->18, 18->19, 20->21, 27->28, 30->31, 31->32.
Mid-sentence page cuts (no end mark, next page starts lower case): **8**: 12->13, 14->15, 15->16, 16->17, 21->22, 22->23, 24->25, 28->29.
Page breaks not ending in . ! ? : or a quote: 24 of 32.

Kept whole in one chunk (heading + first body character; the last character before a cut + the first after):

| Arm | Orphans kept with their body | Cuts kept whole |
|---|---|---|
| v0 per-page 1000/200 | 0 of 16 | 0 of 8 |
| cross-page recursive 1000/200 | 16 of 16 | 8 of 8 |
| L1 | 16 of 16 | 8 of 8 |
| L2 | 16 of 16 | 8 of 8 |
| L2 + merge<400 | 16 of 16 | 8 of 8 |
| L3 | 16 of 16 | 8 of 8 |
| L3 + merge<400 | 16 of 16 | 8 of 8 |
| L4 | 16 of 16 | 8 of 8 |
| L4 + merge<400 | 16 of 16 | 8 of 8 |
| L3, size-only headings | 16 of 16 | 8 of 8 |

## 8 Eval set

8 answerable item(s) on this document; 2 unanswerable skipped. Single-segment quotes that match the snapshot: 11 of 12.

| Item | Category | Groups | Pages | straddles_v0 | crosses_page | Whole in an L3 chunk |
|---|---|---|---|---|---|---|
| D-001 | exact-term | 1 | 3 | no | no | yes |
| D-002 | factual-single-span | 1 | 10 | no | no | yes |
| D-003 | factual-single-span | 1 | 23 | no | no | yes |
| D-004 | exact-term | 1 | 8, 23 | no | no | yes |
| D-005 | multi-span | 2 | 2 | no | no | yes |
| D-006 | vocabulary-mismatch | 2 | 8 | no | no | yes |
| D-007 | multi-hop | 2 | 10, 29 | no | no | yes |
| D-008 | exact-term | 1 | 24 | no | no | yes |

**straddles_v0: 0 of 8 · crosses_page: 0 of 8.** straddles_v0 = some evidence group has no alternative that lies inside one v0 chunk; crosses_page = an alternative's evidence runs over a page break. These are the items structure chunking can change.

## 9 Inspection sample

10 random L3 chunks (`random.Random(0).sample`), with the automatic pre-check. The text and the verdict boxes are in the inspection sheet (`--sheet`).

| Chunk | [a, b) | Chars | Pages | Piece | Path | Starts at heading | Ends at sentence |
|---|---|---|---|---|---|---|---|
| 5 | [3,556, 4,543) | 987 | 2 | 1/1 | Understanding Climate Change > Chapter 2: Causes of Climate Change > Deforestation | yes | yes |
| 33 | [21,294, 22,207) | 913 | 10 | 1/1 | Understanding Climate Change > Chapter 6: Global and Local Climate Action > National Strategies | yes | yes |
| 49 | [31,533, 32,348) | 815 | 15 | 1/2 | Understanding Climate Change > Chapter 10: Climate Change and Human Health > Health Impacts | yes | yes |
| 51 | [33,071, 33,769) | 698 | 15, 16 | 1/2 | Understanding Climate Change > Chapter 10: Climate Change and Human Health > Health Adaptation Strategies | yes | yes |
| 53 | [34,158, 34,869) | 711 | 16 | 1/1 | Understanding Climate Change > Chapter 10: Climate Change and Human Health > Global Health Initiatives | yes | yes |
| 62 | [39,900, 40,609) | 709 | 18, 19 | 1/2 | Understanding Climate Change > Chapter 12: The Path Forward > Commitment to Future Generations | yes | yes |
| 65 | [41,727, 42,456) | 729 | 19 | 2/2 | Understanding Climate Change > Chapter 13: Climate Change and Social Justice > Climate Justice | yes | yes |
| 97 | [60,282, 61,223) | 941 | 27, 28 | 1/1 | Understanding Climate Change > Chapter 18: Moving Forward Together > Hope and Inspiration | yes | yes |
| 108 | [67,316, 68,026) | 710 | 30, 31 | 2/2 | Understanding Climate Change > Chapter 20: Climate Change and Innovation > Social Innovation | yes | yes |
| 113 | [70,214, 70,603) | 389 | 32 | 1/2 | Understanding Climate Change > Chapter 21: Climate Change and Cultural Shifts > Educational Initiatives | yes | yes |

## 10 Checklist

| Check | Verdict | Evidence | How to check |
|---|---|---|---|
| S1 Text layer on every page (no scans) | PASS | 33 of 33 pages have a text layer | Count non-space characters per page; a page with none, or with an image and under 50, has no usable text layer. Open it: a scan needs OCR or a layout parser (S2) before any structure can be read. |
| S2 Body size is clear (one size holds >= 50% of characters) | PASS | body size 12.0: 67,819 of 70,368 characters (96.4%) | Read the font histogram (section 1): the body size should dominate. If two sizes share the text, levels by size rank are unreliable. |
| S3 At least two heading levels; a plausible heading count | PASS | 282 headings on 33 page(s) (8.5 per page), 4 level(s): L1 1, L2 21, L3 68, L4 192; numbered headings 21, numbering depth -> level 1->L2 (consistent) | Read the per-level counts (section 3): between 1 heading per 3 pages and 15 per page; if headings are numbered, the numbering depth should map to one level each. |
| S4 Size only vs size + bold: the difference is small or explained | MANUAL | size only 90, size + bold 282: size only misses 192 of 282 (68.1%); at L3 size only gives the same chunks; read the list in section 3 | Read the list of bold body-size headings size-only misses (section 3): real sub-headings, or bold phrases that are not headings? Size + bold keeps them; size only would merge them into the body. |
| S5 Outline (get_toc) present and matching the headings (>= 90%) | MANUAL | no outline (get_toc() = []); tagged (StructTreeRoot, MarkInfo Marked true); compare a few tagged headings by eye | Compare the outline titles with the detected headings; if they match, the outline is the cleaner source. Without an outline, a tagged PDF can be compared by eye in a viewer's tag panel. |
| S6 Every heading aligns to an exact snapshot offset | PASS | aligned 282 of 282; dict lines rebuild get_text() on 33 of 33 pages | Every heading line must be found in doc_text with a moving cursor (section 5); one miss stops the build (fail closed). Check that dict lines rebuild get_text() on every page. |
| S7 Single column, or columns handled before detection (C1) | PASS | two-column pages: none; most right-to-left jumps on a page: 0 | Two-column pages (long blocks in both halves) and right-to-left jumps (section 4); open one page by eye. Fix reading order (C1 column clipping) before trusting headings or chunks. |
| S8 No running headers or footers detected as headings | PASS | 0 line(s) repeat on >= 3 pages and are excluded | Lines on >= 3 pages are excluded; also look for headings that repeat with only a number changed (page numbers) and for headings at the very top or bottom of every page. |
| S9 Chunk sizes: none over the cap, < 10% under the minimum | WARN | L3: 117 chunks, 187/619/997 characters; over the cap 1000: 0; under 400: 19 (16.2%); with merge: 19 of 117 (16.2%); invariant violations 0; tokens not counted here | Chunk statistics at the chosen split level (section 6); count tokens with your embedder's tokenizer (embed_fit_check.py) so no chunk passes its limit. |
| S10 10 random chunks pass the inspection sheet | MANUAL | automatic pre-check: 10 of 10 start at a heading or a clean continuation and end at a sentence (chunks 5, 33, 49, 51, 53, 62, 65, 97, 108, 113); paths and content need your eye | Fill the sheet (--sheet): each chunk starts at a heading or a clean continuation, has the right path, and ends at a sentence unless the cap forced the cut. 8 of 10 or better before measuring. |
| S11 Tables detected and kept whole, or flagged for C7/S2 | PASS | find_tables(): no ruled table found | find_tables() counts ruled tables per page (section 4); open those pages and check that a table is not cut across chunks. Tables without ruling lines are not found: glance at the pages. |

PASS fine · WARN look before you rely on it · FAIL fix first · MANUAL needs your eye (the evidence helps).

## 11 Recommendation

Typography route (size + bold) at split level L3: the deepest level whose median section >= 400 characters (median 1,033.5).

- Read the bold body-size headings: size-only detection (pymupdf4llm-style) would miss them.
- Duplicate titles found (11): keep `section_path`; consider I5 headers.
- 19 of 117 chunks are under 400 characters (17 of them are pieces of split sections, which merge cannot join): accept them, or compare a shallower level or a larger cap.
- Fill the inspection sheet; fewer than 8 of 10 passing means do not measure yet.
- Eval set: 0 of 8 items straddle a v0 chunk or cross a page, so a retrieval comparison cannot show what structure chunking fixes; add such items (M1) and expect "inconclusive" until then.

Order of the rules: S1 text layer → S7 reading order → S6 alignment → S5 outline → S2–S4 typography → unclear.


Lesson: `study/lessons/I2_structure_chunking.html`. This report checks whether the structure can be recovered and what the chunks look like; it is not a retrieval result.
