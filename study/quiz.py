"""Terminal quiz for the offline study kit. Same question files and answer log as the website.

Run from rag_learning/:
    uv run python study/quiz.py                 # show what is due, then pick a concept
    uv run python study/quiz.py R1              # quiz R1: first time all main items, later weakest first
    uv run python study/quiz.py R1 --mode pre   # also: all, interview
    uv run python study/quiz.py --due           # list due reviews only
    uv run python study/quiz.py --check         # check every question file against study/FORMAT.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

WIDTH = 92


def plain(md: str) -> str:
    """Markdown → readable terminal text."""
    s = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 [\2]", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", s)
    s = s.replace("`", "")
    return s.strip()


def say(text: str = "", indent: str = "") -> None:
    for para in plain(text).splitlines() or [""]:
        if para.startswith(("    ", "\t", "|")) or not para.strip():
            print(indent + para)
        else:
            print(textwrap.fill(para, WIDTH, initial_indent=indent, subsequent_indent=indent + "  "))


def ask_numbers(prompt: str, n: int) -> list[int]:
    while True:
        raw = input(prompt).replace(",", " ").split()
        try:
            picks = sorted({int(x) - 1 for x in raw})
        except ValueError:
            print("  Type numbers like: 1 3   (or just Enter for none)")
            continue
        if all(0 <= p < n for p in picks):
            return picks
        print(f"  Numbers must be between 1 and {n}.")


def ask_conf() -> int:
    while True:
        raw = input("How sure are you? 1 guessing · 2 fairly sure · 3 sure: ").strip()
        if raw in ("1", "2", "3"):
            return int(raw)


def run_question(q: dict, i: int, n: int) -> dict:
    print("\n" + "─" * WIDTH)
    tag = kit.TYPE_NAME.get(q["type"], q["type"]) + ("" if q["set"] == "main" else f" · {q['set']}")
    print(f"[{i}/{n}] {q['id']} · {tag}\n")
    say(q["question"])
    if q["template"]:
        print()
        say("Reply template: " + q["template"], "  ")
    print("\nWrite your answer (closed book). Finish with an empty line.")
    print("Commands on their own line:  ?h = next hint   ?idk = show the answer (scores 0)\n")
    lines, hint, assisted = [], 0, False
    while True:
        line = input("> " if not lines else "  ")
        cmd = line.strip().lower()
        if cmd == "?h":
            if hint < len(q["hints"]):
                hint += 1
                print(f"\n  Hint {hint} (max score now {kit.HINT_CAP[hint]}):")
                say(q["hints"][hint - 1], "    ")
                print()
            else:
                print("  No more hints.")
            continue
        if cmd == "?idk":
            assisted = True
            break
        if not line.strip():
            if lines:
                break
            continue
        lines.append(line)
    answer = "\n".join(lines)
    conf = None if assisted else ask_conf()
    a = q["answer"]
    print("\n── Model answer " + "─" * (WIDTH - 16))
    if a["preamble"]:
        say(a["preamble"], "  ")
        print()
    say(a["model"], "  ")
    key_hit = four_hit = wrong_hit = []
    if not assisted:
        print("\nKey points. Count only what you really wrote:")
        for k, t in enumerate(a["keys"], 1):
            say(f"{k}. {t}", "  ")
        key_hit = ask_numbers("Which did you have? (numbers, Enter = none): ", len(a["keys"]))
        if a["four"]:
            print("\nFor a 4, your answer also has:")
            for k, t in enumerate(a["four"], 1):
                say(f"{k}. {t}", "  ")
            four_hit = ask_numbers("Which? (numbers, Enter = none): ", len(a["four"]))
        if a["wrong"]:
            print("\nDid your answer say any of these?")
            for k, t in enumerate(a["wrong"], 1):
                say(f"{k}. {t}", "  ")
            wrong_hit = ask_numbers("Which? (numbers, Enter = none): ", len(a["wrong"]))
    score, why = kit.score_from_ticks(len(key_hit), len(a["keys"]), len(four_hit), len(a["four"]),
                                      len(wrong_hit), hint, assisted)
    print(f"\n  SCORE {score}/4: {why}")
    if score <= 2 and a["reread"]:
        say("Reread: " + a["reread"], "  ")
    now = dt.datetime.now()
    row = {
        "ts": now.isoformat(timespec="seconds"), "date": now.date().isoformat(),
        "qid": q["id"], "concept": q["concept"], "type": q["type"], "set": q["set"],
        "answer": answer, "confidence": conf, "hint_level": hint, "assisted": assisted,
        "key_hit": key_hit, "key_total": len(a["keys"]), "four_hit": four_hit, "four_total": len(a["four"]),
        "wrong_hit": wrong_hit, "wrong_text": [a["wrong"][w] for w in wrong_hit],
        "score": score, "why": why, "grader": "self", "mode": "cli",
    }
    kit.append_attempt(row)
    return row


def show_due() -> list[dict]:
    _, concepts = kit.concept_summaries()
    due = [c for c in concepts if c["schedule"] and c["schedule"]["due"]]
    if due:
        print("Due now:")
        for c in due:
            print(f"  {c['id']:6} {c['title']}  (next review was {c['schedule']['next_review']})")
    else:
        print("Nothing due.")
    ready = [c["id"] for c in concepts if c["q_count"]]
    print("Concepts with questions:", ", ".join(ready) if ready else "none yet")
    return due


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description="Terminal quiz for the study kit.")
    ap.add_argument("concept", nargs="?")
    ap.add_argument("--mode", default="next", choices=["next", "all", "pre", "interview"])
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        files = sorted(kit.QDIR.glob("*_questions.md"))
        bad = 0
        for p in files:
            problems = kit.lint_questions(p)
            print(f"{'OK  ' if not problems else 'FAIL'} {p.name}: {len(kit.parse_questions(p))} questions")
            for msg in problems:
                print("     -", msg)
            bad += bool(problems)
        print(f"{len(files) - bad}/{len(files)} files pass")
        sys.exit(1 if bad else 0)

    if args.due:
        show_due()
        return
    cid = args.concept
    if not cid:
        due = show_due()
        default = due[0]["id"] if due else ""
        cid = input(f"\nConcept to quiz{f' [{default}]' if default else ''}: ").strip() or default
        if not cid:
            return
    path = kit.QDIR / f"{cid}_questions.md"
    if not path.exists():
        print(f"No question file for {cid} yet ({kit.rel(path)}).")
        return
    qs = kit.pick_questions(kit.parse_questions(path), kit.load_attempts(), args.mode)
    if not qs:
        print("No questions in that set.")
        return
    print(f"\n{cid}: {len(qs)} questions ({args.mode}). Closed book. Ctrl+C stops; answers so far are saved.")
    rows = []
    try:
        for i, q in enumerate(qs, 1):
            rows.append(run_question(q, i, len(qs)))
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
    if rows:
        print("\n" + "═" * WIDTH)
        print(f"Saved {len(rows)} answers. Average {sum(r['score'] for r in rows) / len(rows):.1f}/4, lowest {min(r['score'] for r in rows)}.")
        sure_wrong = [r["qid"] for r in rows if r["confidence"] == 3 and r["score"] <= 1]
        if sure_wrong:
            print("Sure but wrong:", ", ".join(sure_wrong), "(check these first next time)")
        _, concepts = kit.concept_summaries()
        c = next((x for x in concepts if x["id"] == cid), None)
        if c and c["schedule"]:
            print(f"Next review of {cid}: {c['schedule']['next_review']} (interval {c['schedule']['interval']} days)")


if __name__ == "__main__":
    main()
