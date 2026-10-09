"""Coach re-check for the C7 seed in sources/coach/transfer_seed_bank.md (written 2026-10-09).

Claim to check: on the repo's side corpus data/customers-100.csv, an exact pandas filter for
'Chile' matches 1 row and 'chile' matches 0, and listing the column's distinct values first shows why.

Read only: the CSV is opened for reading; nothing in upstream/ is written, imported or run.
No network, no API call, no .env. Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python -I sources/verification/coach/coach_c7_chile_check.py \
        "$B/upstream/RAG_Techniques/data/customers-100.csv" \
        > sources/verification/coach/out_coach_c7_chile_check.txt
"""
import hashlib
import importlib.metadata as md
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")   # -I ignores PYTHONIOENCODING

CSV = sys.argv[1]
N_OK = N_BAD = 0


def check(label, ok, detail=""):
    global N_OK, N_BAD
    N_OK += bool(ok)
    N_BAD += not ok
    print(f"{'PASS' if ok else 'FAIL'} {label}" + (f"  [{detail}]" if detail else ""))


print("python", sys.version.split()[0], "| pandas", md.version("pandas"))
print("csv sha256", hashlib.sha256(open(CSV, "rb").read()).hexdigest())
df = pd.read_csv(CSV)
print(f"rows={len(df)} columns={list(df.columns)}")

exact = int((df["Country"] == "Chile").sum())
lower = int((df["Country"] == "chile").sum())
folded = int((df["Country"].str.casefold() == "chile").sum())
distinct = sorted(df["Country"].unique())
print(f"df[df.Country == 'Chile'] -> {exact} row(s); == 'chile' -> {lower}; casefold == 'chile' -> {folded}")
print(f"distinct Country values: {len(distinct)}; values containing 'chil' (any case): "
      f"{[c for c in distinct if 'chil' in c.casefold()]}")
print("the matching row (Index, Country):", df.loc[df["Country"] == "Chile", ["Index", "Country"]].values.tolist())

check("100 data rows", len(df) == 100, str(len(df)))
check("'Chile' matches exactly 1 row", exact == 1, str(exact))
check("'chile' matches 0 rows", lower == 0, str(lower))
check("a case-folded filter finds the 1 row", folded == 1, str(folded))
check("'Chile' is in the distinct-values list", "Chile" in distinct)
print(f"\nRESULT: {N_OK} PASS, {N_BAD} FAIL")
