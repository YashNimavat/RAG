"""Write the O1 diagnostic records (2026-10-08) in the formats defined in 05 §6.1–§6.4 and §5.5.
Run from the workspace root: python -I sources/verification/phase0/write_o1_records.py
Refuses to overwrite existing progress files."""
import csv, io, pathlib, re

D = "2026-10-08"
NEXT1 = "2026-10-09"
root = pathlib.Path(".")

# ---- 1. concept rows from 02 card headings ------------------------------------------------------------
plan = (root / "02_RAG_MASTER_LEARNING_PLAN.md").read_text(encoding="utf-8")
rows = []
for m in re.finditer(r"^#### ((?:I-CMP)|[OPCMIRQXVDASK]\d) — (.+?) · ([EUS](?:/[EUS])?)", plan, flags=re.M):
    cid, title, tier = m.group(1), m.group(2).strip(), m.group(3)
    rows.append((cid, title, tier.split("/")[0] if tier != "S/U" else "S"))
assert len(rows) == 56, len(rows)
PHASE = {"O": 0, "P": 1, "C": 2, "M": 3, "I": 4, "R": 5, "Q": 6, "X": 7, "V": 8, "D": 9, "A": 10, "S": 11, "K": 12}
TECH = re.compile(r"^(I\d|I-CMP|R\d|Q\d|X\d|V[123]|A\d|S\d)$")

HEADER = ["concept_id", "title", "phase", "priority", "status", "first_studied", "exposed_on", "last_reviewed",
          "next_review", "review_interval_days", "recall_score_last", "recall_accuracy_rolling", "application_score",
          "transfer_score", "coding_independence_0_3", "debugging_0_3", "experiment_status", "misconceptions_open",
          "reinforcement_flag", "evidence_links"]

# ---- 2. O1 results mapped to concepts (05 §8.3 step 3) -------------------------------------------------
# score >= 3 -> exposed, +3 days; score 2 -> exposed, interval 1; <= 1 -> not_started (+ Phase-1 priority for P-concepts)
o1 = {  # concept: (best O1 score, item ids, application_score, transfer_score)
    "P1": (1, "O1-Q01", "", ""), "P4": (0, "O1-Q02;O1-TR1", "0", ""), "P3": (1, "O1-Q03", "", ""),
    "P6": (0, "O1-Q04", "0", ""), "C2": (1, "O1-Q05;O1-REC", "", ""), "C3": (1, "O1-Q05", "", ""),
    "C4": (0, "O1-Q06;O1-TR1;O1-TR2", "0", ""), "P5": (0, "O1-Q06", "0", ""), "P7": (1, "O1-Q07", "", ""),
    "C5": (1, "O1-Q07", "", ""), "M2": (2, "O1-Q08", "", "2"), "M3": (2, "O1-Q08", "", "2"),
    "R1": (2, "O1-Q09", "2", ""), "R3": (0, "O1-Q10", "", ""), "V2": (1, "O1-Q11", "", "1"),
    "A2": (1, "O1-Q11", "", "1"), "M5": (2, "O1-Q12", "", "2"), "R2": (1, "O1-Q12", "", ""),
    "I5": (1, "O1-Q12", "", ""), "D4": (1, "O1-Q12", "", ""), "O1": (None, "O1-REC", "", ""),
}
mcs = {"P1": "MC-001", "P4": "MC-002", "C4": "MC-002;MC-005", "C5": "MC-003", "P7": "MC-003;MC-004",
       "V2": "MC-006", "A2": "MC-006"}
legacy = {  # 05 §8.3 step 4: recorded, never scored
    **{c: "legacy:ch1-selfrated-2.33-weak" for c in ("C1", "C2", "C3", "C4", "C5", "C6")},
    "A2": "legacy:my-way-executed", "V2": "legacy:my-way-executed", "Q1": "legacy:my-way-executed",
    "I3": "legacy:vai-chunking_lab", "R3": "legacy:vai-L22", "R1": "legacy:vai-L23",
    "M2": "legacy:vai-L27-L29-L44", "M3": "legacy:vai-L27-L29-L44", "D1": "legacy:vai-L30",
}
legacy["C2"] += ";legacy:vai-chunking_lab"

out = io.StringIO()
w = csv.writer(out, lineterminator="\n")
w.writerow(HEADER)
for cid, title, tier in rows:
    phase = PHASE[cid[0]] if cid != "I-CMP" else 4
    status, first, nxt, interval = "not_started", "", "", ""
    score, items, app, trn = o1.get(cid, (None, "", "", ""))
    if cid == "O1":
        status, first = "exposed", D
    elif score is not None and score >= 3:
        status, first, nxt, interval = "exposed", D, "2026-10-11", "3"
    elif score == 2:
        status, first, nxt, interval = "exposed", D, NEXT1, "1"
    ev = []
    if items:
        ev += [f"log:{D}#{i}" for i in items.split(";")]
    if cid == "O1":
        ev.append(f"reviews/reconstructions/{D}_phase0.md")
    if cid in legacy:
        ev += legacy[cid].split(";")
    reinforce = "1" if (cid[0] == "P" and score is not None and score <= 1) else "0"
    w.writerow([cid, title, phase, tier, status, first, "", "", nxt, interval, "", "", app, trn, "", "",
                "not_planned" if TECH.match(cid) else "na", mcs.get(cid, ""), reinforce, ";".join(ev)])

files = {
    "progress/concept_tracker.csv": out.getvalue(),
}
for path, text in files.items():
    p = root / path
    assert not p.exists(), f"refusing to overwrite {p}"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    print("wrote", p, len(text.splitlines()), "lines")
