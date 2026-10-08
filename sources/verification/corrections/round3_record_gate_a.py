"""Record Gate A = GRANTED WITH FIXES (Codex re-review 2, 2026-10-08) and the R2-01/R2-02 fixes.
Run from the workspace root: python -I sources/verification/corrections/round3_record_gate_a.py"""
import pathlib, re

LOG = "reviews/CORRECTIONS_LOG_2026-10-08.md"
REV2 = "reviews/CODEX_REREVIEW2_2026-10-08.md"


def edit(fn, pairs, regex=False):
    p = pathlib.Path(fn)
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    t = raw.decode("utf-8").replace("\r\n", "\n")
    for a, b in pairs:
        if regex:
            t2, n = re.subn(a, b, t, count=1)
        else:
            n = t.count(a)
            t2 = t.replace(a, b)
        assert n == 1, (fn, n, a[:80])
        t = t2
        print("ok", fn, ascii(a[:50]))
    if crlf:
        t = t.replace("\n", "\r\n")
    p.write_bytes(t.encode("utf-8"))


GRANT = ("**Current state: GRANTED WITH FIXES** by Codex re-review 2 on 2026-10-08 ([report](" + REV2 + ")). "
         "The two Minor fixes it required (R2-01 manifest nested-field validation; R2-02 undefined-κ bootstrap guard) were applied the same day, "
         "and the acceptance suite passes 145/145 ([corrections log](" + LOG + "#round-3)). Gates B and C remain ungranted.")
edit("08_GAP_ANALYSIS_AND_DECISIONS.md", [
    (re.escape("**Current state:** design approval pending Codex re-review 2 after the round-2 (R-01…R-07) fixes."),
     GRANT.replace("\\", "\\\\")),
    (r"- \[ \] C-1\. (.*?) \*Ready for re-confirmation at Codex re-review 2\.\*",
     r"- [x] C-1. \1 (Codex re-review 2, 2026-10-08: confirmed within the correction scope)"),
    (r"- \[ \] DEC-1b\. ", "- [x] DEC-1b. "),
    (r"- \[ \] V-1\. ", "- [x] V-1. "),
    (r"- \[ \] V-4\. ", "- [x] V-4. "),
    (r"- \[ \] P-1\. ", "- [x] P-1. "),
], regex=True)

# append the reviewer confirmation note right after the Gate A heading paragraph
p = pathlib.Path("08_GAP_ANALYSIS_AND_DECISIONS.md")
raw = p.read_bytes(); crlf = b"\r\n" in raw
t = raw.decode("utf-8").replace("\r\n", "\n")
note = ("\n\n> Gate A ticks added 2026-10-08 from Codex re-review 2 §6: C-1 confirmed within the correction scope; "
        "DEC-1b confirmed (D-17 reviewer confirmation: Codex, 2026-10-08); V-1 specification approved; V-4 confirmed at design level; "
        "P-1 exemplar approved for the corrected design. The helper fixes Codex attached to DEC-1b/V-1 (R2-01) and V-4 (R2-02) are applied. "
        "See [corrections log](" + LOG + "#round-3).")
i = t.find(GRANT)
j = t.find("\n", i)
t = t[:j] + note + t[j:]
if crlf:
    t = t.replace("\n", "\r\n")
p.write_bytes(t.encode("utf-8"))
print("ok 08 note")
