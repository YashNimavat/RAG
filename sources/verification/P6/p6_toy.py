"""P6 toy data (made up for the lesson; NOT a result about any real retriever).

Ten toy chunks about climate, three toy queries with graded qrels (2 = sufficient, 1 = partial),
one toy ranking per query, and small extra cases for the lesson's Parts B, D and J.
"""

CHUNKS = {
    "c1": "sea-level rise and coastal flooding",
    "c2": "a short history of climate science",
    "c3": "carbon dioxide and methane trap heat (the greenhouse effect)",
    "c4": "the goals of the Paris Agreement",
    "c5": "weather versus climate: definitions",
    "c6": "cutting forests releases stored carbon",
    "c7": "water vapour amplifies warming (a feedback)",
    "c8": "the falling cost of renewable energy",
    "c9": "ozone and nitrous oxide, mentioned briefly",
    "c10": "forests as carbon sinks",
}

QUERIES = {
    "Q1": "Which gases trap heat in the atmosphere?",
    "Q2": "What does the Paris Agreement aim for?",
    "Q3": "How does cutting forests add CO2 to the air?",
}

QRELS = {                       # chunk -> grade; any chunk not listed is grade 0
    "Q1": {"c3": 2, "c7": 1, "c9": 1},
    "Q2": {"c4": 2},
    "Q3": {"c6": 2, "c10": 1},
}

RANKINGS = {                    # toy retriever output, best first (all 10 chunks)
    "Q1": ["c5", "c3", "c8", "c7", "c1", "c2", "c9", "c4", "c6", "c10"],
    "Q2": ["c4", "c2", "c1", "c3", "c5", "c6", "c7", "c8", "c9", "c10"],
    "Q3": ["c1", "c8", "c2", "c10", "c6", "c3", "c4", "c5", "c7", "c9"],
}

# Part D.6: MRR and nDCG disagree (binary; three relevant chunks d1-d3; n* are not relevant)
QD = {"d1": 1, "d2": 1, "d3": 1}
QD_A = ["d1", "n1", "n2", "n3", "n4"]
QD_B = ["n1", "d1", "d2", "d3", "n2"]

# Part D.6: same first hit, different grades (h = sufficient, p = partial)
QG = {"h": 2, "p": 1}
QG_A = ["p", "h", "n1", "n2", "n3"]
QG_B = ["h", "p", "n1", "n2", "n3"]

# Part B: the same five chunks in a good and a poor order (Ch22 p.7/19 figure idea)
QS = {"a": 1, "b": 1}
QS_GOOD = ["a", "b", "x", "y", "z"]
QS_POOR = ["x", "y", "a", "z", "b"]

# Part D.5: nDCG@k can FALL as k grows (b is relevant but never retrieved)
QF = {"a": 1, "b": 1}
QF_RANK = ["a", "x", "y", "z", "w"]

# Part D.7 preview: Recall@k vs CE@k. Chunks e2 and e3 overlap and both hold group G1's whole span;
# e6 holds group G2's span. Binary qrels mark every chunk that overlaps evidence.
QE = {"e2": 1, "e3": 1, "e6": 1}
QE_GROUPS = [{"e2", "e3"}, {"e6"}]
QE_RANK = ["e2", "e3", "e1", "e6", "e4"]

# 06 §7.3 toy (replicated to check 06's table): G1 inside c3, G2 inside c7
T06_QRELS_BIN = {"c3": 1, "c7": 1}
T06_QRELS_GRADED = {"c3": 2, "c7": 1}
T06_RANK = ["c5", "c3", "c9", "c7", "c1"]
T06_GROUPS = [{"c3"}, {"c7"}]

# Part J1: a short result list (only 3 chunks returned) scored at k = 5
J1_RANK = ["c3", "c5", "c7"]
# Part J2: a ranking that finds only the partial chunk c7 for Q1
J2_RANK = ["c7", "c5", "c8", "c1", "c2"]
