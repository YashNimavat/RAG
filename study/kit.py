"""Shared core of the offline study kit: concepts, question files, scoring, schedule.

Used by study/app/server.py (the website) and study/quiz.py (the terminal quiz).
Standard library only. File formats: study/FORMAT.md. Rules: 05 §4.2 (rubrics),
05 CR-05 (hint caps), 05 §5.2 (interval ladder).
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # rag_learning/
BOOK_DIR = ROOT.parent / "RAG_Made_Simple_The_Complete_Visual_Guide"
PLAN = ROOT / "02_RAG_MASTER_LEARNING_PLAN.md"
TRACKER = ROOT / "progress" / "concept_tracker.csv"
# Tests point these at a scratch folder so the real progress files stay untouched.
_DATA = Path(os.environ.get("STUDY_KIT_DATA", ROOT / "progress"))
ATTEMPTS = _DATA / "study_attempts.jsonl"
STATE = _DATA / "study_state.json"
QDIR = Path(os.environ.get("STUDY_KIT_QDIR", ROOT / "study" / "questions"))
RDIR = ROOT / "study" / "reading"

LADDER = [1, 3, 7, 14, 30, 60]
HINT_CAP = {0: 4, 1: 3, 2: 2, 3: 1}
TICKS = ("read_short", "read_full", "book", "lab")
SCHEDULED_SETS = ("main", "review", "interview")
TYPE_NAME = {"R": "Recall", "A": "Application", "T": "Transfer"}


def today() -> dt.date:
    return dt.date.today()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:                       # a test folder outside the workspace
        return f"study/{path.parent.name}/{path.name}"


# ---------------------------------------------------------------- concepts

_PHASE_RE = re.compile(r"^### Phase (\d+) — (.+?)\s*$")
_CARD_RE = re.compile(r"^#### (\S+) — (.+?) · (.+?)\s*$")
_FIELD_RE = re.compile(r"\*\*(Pre|Failure|Book|Lab|Proj):\*\*\s*(.*?)(?=\s+·\s+\*\*[A-Z][A-Za-z]*:\*\*|$)")


def load_plan() -> tuple[list[dict], list[dict]]:
    """Phases and concept cards, in curriculum order, from 02 §3."""
    phases, cards, cur, pending = [], [], None, None
    for line in PLAN.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 4."):
            break
        if pending and line.startswith((" ", "\t")) and line.strip():
            piece = re.sub(r"^[-*]\s+", "", line.strip()).rstrip(";").strip()
            sep = " " if cur[pending].endswith(":") else "; "
            cur[pending] = f"{cur[pending]}{sep}{piece}" if cur[pending] else piece
            continue
        if line.strip():
            pending = None
        m = _PHASE_RE.match(line)
        if m:
            phases.append({"n": int(m.group(1)), "name": m.group(2)})
            continue
        m = _CARD_RE.match(line)
        if m and phases:
            tier = re.match(r"[EUS](?:/[EUS])?", m.group(3))
            cur = {"id": m.group(1), "title": m.group(2), "tier": tier.group(0) if tier else "",
                   "phase": phases[-1]["n"], "pre": "", "failure": "", "book": "", "lab": "", "proj": ""}
            cards.append(cur)
            continue
        if cur and line.startswith("- **"):
            for key, val in _FIELD_RE.findall(line):
                cur[key.lower()] = val.strip()
                if not val.strip() or val.strip().endswith(":"):
                    pending = key.lower()      # the value continues in the indented list below
    return phases, cards


def load_tracker() -> dict[str, dict]:
    if not TRACKER.exists():
        return {}
    with TRACKER.open(encoding="utf-8", newline="") as f:
        return {row["concept_id"]: row for row in csv.DictReader(f)}


_TOOL_HINT = {"P1": "token_budget", "P2": "qrels", "P3": "bm25", "P4": "embed_fit", "I6": "question_augment"}               # apply-it tools are named after the technique, not the concept id


def concept_files(cid: str) -> dict:
    full = sorted((ROOT / "concepts").glob(f"{cid}_*.md"))
    if cid == "C2":
        full = [ROOT / "07_SAMPLE_LESSON.md"]
    short = sorted(RDIR.glob(f"{cid}_*.md"))
    qfile = QDIR / f"{cid}_questions.md"
    labs = sorted((ROOT / "labs").glob(f"{cid}_*.ipynb")) + sorted((ROOT / "labs").glob(f"{cid}_*.py"))
    visual = sorted((ROOT / "study" / "lessons").glob(f"{cid}_*.html"))
    notebooks = sorted((ROOT / "study" / "notebooks").glob(f"{cid}_*.ipynb"))
    tools = sorted((ROOT / "study" / "tools").glob(f"{cid.lower()}_*.py")) + sorted((ROOT / "study" / "tools").glob(f"*{_TOOL_HINT.get(cid, '#')}*.py"))
    return {
        "visual": visual[0].name if visual else None,
        "notebook": rel(notebooks[0]) if notebooks else None,
        "tool": rel(tools[0]) if tools else None,
        "full": rel(full[0]) if full else None,
        "short": rel(short[0]) if short else None,
        "questions": rel(qfile) if qfile.exists() else None,
        "labs": [rel(p) for p in labs],
    }


# ---------------------------------------------------------------- questions

_Q_START = re.compile(r"<!--\s*q\s+(.*?)\s*-->")
_Q_END = re.compile(r"<!--\s*/q\s*-->")
_ATTR = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')
_DETAILS = re.compile(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", re.S)
_CHECK = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+(.*)$")
_LABEL = re.compile(r"^\*\*([^*]+)\*\*(.*)$")


def _attrs(text: str) -> dict:
    return {k: (a if a else b) for k, a, b in _ATTR.findall(text)}


def _section_key(label: str) -> str | None:
    label = label.strip().rstrip(":").strip().lower()
    for prefix, key in (("model answer", "model"), ("key points", "keys"), ("for a 4", "four"),
                        ("common wrong", "wrong"), ("if you missed", "reread")):
        if label.startswith(prefix):
            return key
    return None


def _parse_answer(body: str) -> dict:
    out = {"preamble": [], "model": [], "keys": [], "four": [], "wrong": [], "reread": []}
    key = "preamble"
    for line in body.strip("\n").splitlines():
        m = _LABEL.match(line.strip())
        sk = _section_key(m.group(1)) if m else None
        if sk:
            key = sk
            rest = m.group(2).strip()
            if key in ("model", "reread", "preamble") and rest:
                out[key].append(rest.lstrip(":").strip())
            continue
        if key in ("keys", "four", "wrong"):
            c = _CHECK.match(line)
            if c:
                out[key].append(c.group(1).strip())
            elif line.strip() and out[key] and line.startswith((" ", "\t")):
                out[key][-1] += " " + line.strip()
            continue
        out[key].append(line)
    for k in ("preamble", "model", "reread"):
        out[k] = "\n".join(out[k]).strip()
    return out


def parse_questions(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    cid = path.name.split("_questions")[0]
    questions = []
    for m in _Q_START.finditer(text):
        end = _Q_END.search(text, m.end())
        block = text[m.end(): end.start() if end else len(text)]
        a = _attrs(m.group(1))
        title = re.search(r"^###\s+(.+)$", block, re.M)
        first_details = block.find("<details>")
        head = block[: first_details if first_details >= 0 else len(block)]
        qm = re.search(r"\*\*Question:\*\*\s*(.*?)(?=\*\*Reply template:\*\*|\Z)", head, re.S)
        rt = re.search(r"\*\*Reply template:\*\*\s*(.*)", head, re.S)
        hints, answer = [], None
        for dm in _DETAILS.finditer(block):
            summary, inner = dm.group(1).strip(), dm.group(2)
            if summary.lower().startswith("hint"):
                hints.append(inner.strip())
            elif summary.lower().startswith("show answer"):
                answer = _parse_answer(inner)
        q = {
            "id": a.get("id", ""), "type": a.get("type", "R").upper(), "set": a.get("set", "main"),
            "concept": a.get("concept", cid), "source": a.get("source", ""),
            "title": title.group(1).strip() if title else a.get("id", ""),
            "question": qm.group(1).strip() if qm else head.strip(),
            "template": rt.group(1).strip() if rt else "",
            "hints": hints[:3],
            "answer": answer or _parse_answer(""),
            "file": rel(path),
        }
        questions.append(q)
    return questions


def lint_questions(path: Path) -> list[str]:
    """Format problems that would break the website or the quiz (FORMAT.md §2.3)."""
    problems, seen = [], set()
    qs = parse_questions(path)
    if not qs:
        problems.append("no <!-- q ... --> blocks found")
    for q in qs:
        where = q["id"] or "(no id)"
        if not q["id"]:
            problems.append(f"{where}: missing id=")
        if q["id"] in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(q["id"])
        if q["type"] not in TYPE_NAME:
            problems.append(f"{where}: type must be R, A or T")
        if q["set"] not in ("pre", "main", "review", "interview"):
            problems.append(f"{where}: set must be pre, main, review or interview")
        if len(q["hints"]) < 2:
            problems.append(f"{where}: needs Hint 1 and Hint 2")
        ans = q["answer"]
        if not ans["model"]:
            problems.append(f"{where}: no **Model answer:**")
        if not 2 <= len(ans["keys"]) <= 5:
            problems.append(f"{where}: {len(ans['keys'])} key points (need 2-5 '- [ ]' items)")
        if not ans["four"]:
            problems.append(f"{where}: no 'For a 4, also:' points")
        if not ans["wrong"]:
            problems.append(f"{where}: no common wrong answers")
        if not ans["reread"]:
            problems.append(f"{where}: no 'If you missed it, reread:' line")
    return problems


def all_questions() -> dict[str, list[dict]]:
    return {p.name.split("_questions")[0]: parse_questions(p) for p in sorted(QDIR.glob("*_questions.md"))}


# ---------------------------------------------------------------- attempts, state

def load_attempts() -> list[dict]:
    if not ATTEMPTS.exists():
        return []
    rows = []
    for line in ATTEMPTS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def append_attempt(row: dict) -> None:
    ATTEMPTS.parent.mkdir(parents=True, exist_ok=True)
    with ATTEMPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"concepts": {}}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def set_tick(state: dict, cid: str, field: str, on: bool) -> dict:
    if field not in TICKS:
        raise ValueError(f"unknown tick {field}")
    c = state.setdefault("concepts", {}).setdefault(cid, {})
    c[field] = today().isoformat() if on else None
    return c


# ---------------------------------------------------------------- scoring

def score_from_ticks(key_hit: int, key_total: int, four_hit: int, four_total: int,
                     wrong_hit: int, hint_level: int, assisted: bool) -> tuple[int, str]:
    """FORMAT.md §2.4. Returns (score, one-line reason)."""
    if assisted:
        return 0, "answer opened without an attempt (assisted) → 0"
    if key_hit <= 0:
        base, why = 0, "no key point"
    elif key_hit < key_total / 2:
        base, why = 1, f"{key_hit}/{key_total} key points (under half)"
    elif key_hit < key_total:
        base, why = 2, f"{key_hit}/{key_total} key points"
    elif four_total and four_hit >= four_total:
        base, why = 4, "all key points + the 'for a 4' points"
    else:
        base, why = 3, "all key points"
    if wrong_hit:
        if base > 1:
            why += "; but a common wrong answer → max 1"
        base = min(base, 1)
    cap = HINT_CAP.get(hint_level, 1)
    if base > cap:
        why += f"; hint {hint_level} seen → max {cap}"
        base = cap
    return base, why


# ---------------------------------------------------------------- schedule

def _step_up(interval: int) -> int:
    for v in LADDER:
        if v > interval:
            return v
    return LADDER[-1]


def concept_schedule(cid: str, attempts: list[dict], ticks: dict, tier: str = "E") -> dict | None:
    """05 §5.2 recomputed from the log: lowest score of each review day sets the next step.

    The day the concept is first read (or first quizzed) is the concept session; answers
    on that same day do not move the schedule (05 §2.4)."""
    read_dates = [ticks.get(k) for k in ("read_short", "read_full") if ticks.get(k)]
    days: dict[str, int] = {}
    for a in attempts:
        if a.get("concept") == cid and a.get("set") in SCHEDULED_SETS:
            d = a["date"]
            days[d] = min(days.get(d, 4), int(a.get("score", 0)))
    if not read_dates and not days:
        return None
    start = min(read_dates) if read_dates else min(days)
    interval, last, history = 1, start, []
    for d in sorted(days):
        if d <= start:
            continue
        s = days[d]
        before = interval
        interval = _step_up(interval) if s >= 3 else (interval if s == 2 else 1)
        if tier.startswith("S"):
            interval = min(interval, 30)
        last = d
        history.append({"date": d, "lowest": s, "from": before, "to": interval})
    nxt = dt.date.fromisoformat(last) + dt.timedelta(days=interval)
    return {"start": start, "last_review": last, "interval": interval, "next_review": nxt.isoformat(),
            "due": nxt <= today(), "overdue_days": max(0, (today() - nxt).days), "history": history}


def last_by_question(attempts: list[dict]) -> dict[str, dict]:
    last = {}
    for a in attempts:
        last[a["qid"]] = a
    return last


def self_level(cid: str, attempts: list[dict], ticks: dict, schedule: dict | None) -> int:
    """Rough self-checked mastery level after 05 §4.3 (no lab or code scores offline)."""
    mine = [a for a in attempts if a.get("concept") == cid and a.get("set") != "pre"]
    if not mine:
        return 0
    level = 1
    read_dates = [ticks.get(k) for k in ("read_short", "read_full") if ticks.get(k)]
    start = min(read_dates) if read_dates else min(a["date"] for a in mine)
    r_days = {a["date"] for a in mine if a["type"] == "R" and a["score"] >= 3}
    if len(r_days) >= 2 and any(d > start for d in r_days):
        level = 2
    a_items = {a["qid"] for a in mine if a["type"] == "A" and a["score"] >= 3}
    if level == 2 and len(a_items) >= 2:
        level = 3
    if level == 3 and any(a["type"] == "T" and a["score"] >= 3 for a in mine):
        level = 4
    if level == 4 and schedule and schedule["interval"] >= 60:
        level = 5
    return level


def pick_questions(questions: list[dict], attempts: list[dict], mode: str = "next", n: int = 5) -> list[dict]:
    if mode in ("pre", "interview"):
        return [q for q in questions if q["set"] == mode]
    pool = [q for q in questions if q["set"] in ("main", "review")]
    if mode == "all":
        return pool
    last = last_by_question([a for a in attempts if a.get("concept") in {q["concept"] for q in questions}])
    if not any(q["id"] in last for q in pool):
        return [q for q in pool if q["set"] == "main"]
    weak = sorted((q for q in pool if q["id"] in last and last[q["id"]]["score"] <= 2),
                  key=lambda q: (last[q["id"]]["score"], last[q["id"]]["ts"]))
    never = [q for q in pool if q["id"] not in last]
    rest = sorted((q for q in pool if q["id"] in last and last[q["id"]]["score"] > 2),
                  key=lambda q: last[q["id"]]["ts"])
    pick = (weak + never + rest)[:n]
    # 05 §5.1: at least 1 item in 3 must be Application or Transfer.
    need = max(1, round(len(pick) / 3)) - sum(q["type"] in "AT" for q in pick)
    spare = [q for q in weak + never + rest if q not in pick and q["type"] in "AT"]
    for q in spare[:max(0, need)]:
        drop = next((p for p in reversed(pick) if p["type"] == "R"), None)
        if drop:
            pick[pick.index(drop)] = q
    return pick


# ---------------------------------------------------------------- stats

def stats(attempts: list[dict]) -> dict:
    scored = [a for a in attempts if not a.get("assisted")]

    def agg(rows):
        n = len(rows)
        return {"n": n, "mean": round(sum(r["score"] for r in rows) / n, 2) if n else None,
                "good": round(sum(r["score"] >= 3 for r in rows) / n, 2) if n else None}

    by_conf = {str(c): agg([a for a in scored if a.get("confidence") == c]) for c in (1, 2, 3)}
    by_type = {t: agg([a for a in scored if a.get("type") == t]) for t in "RAT"}
    by_hint = {str(h): sum(a.get("hint_level", 0) == h for a in attempts) for h in range(4)}
    per_concept = defaultdict(list)
    for a in attempts:
        per_concept[a["concept"]].append(a)
    concepts = {c: {**agg(rows), "last": rows[-1]["date"]} for c, rows in per_concept.items()}
    sure_wrong = [a for a in scored if a.get("confidence") == 3 and a["score"] <= 1]
    sure_shaky = [a for a in scored if a.get("confidence") == 3 and a["score"] == 2]
    mistakes = Counter()
    mc = Counter()
    for a in attempts:
        for w in a.get("wrong_text", []):
            mistakes[(a["concept"], w)] += 1
            for tag in re.findall(r"MC-\d{3}", w):
                mc[tag] += 1
    days = defaultdict(list)
    for a in attempts:
        days[a["date"]].append(a["score"])
    activity = [{"date": d, "n": len(s), "mean": round(sum(s) / len(s), 2)} for d, s in sorted(days.items())]
    last = last_by_question(attempts)
    weakest = sorted((a for a in last.values() if a["score"] <= 2), key=lambda a: (a["score"], a["ts"]))
    return {
        "total": len(attempts), "assisted": sum(bool(a.get("assisted")) for a in attempts),
        "overall": agg(scored), "by_conf": by_conf, "by_type": by_type, "by_hint": by_hint,
        "concepts": concepts, "sure_wrong": sure_wrong[-50:], "sure_shaky_n": len(sure_shaky),
        "mistakes": [{"concept": c, "text": t, "n": n} for (c, t), n in mistakes.most_common(30)],
        "mc": dict(mc), "activity": activity, "weakest": weakest[:30],
    }


# ---------------------------------------------------------------- overview

def concept_summaries(attempts: list[dict] | None = None, state: dict | None = None) -> tuple[list[dict], list[dict]]:
    phases, cards = load_plan()
    tracker = load_tracker()
    attempts = load_attempts() if attempts is None else attempts
    state = load_state() if state is None else state
    qbank = all_questions()
    out = []
    for c in cards:
        cid = c["id"]
        ticks = state.get("concepts", {}).get(cid, {})
        mine = [a for a in attempts if a.get("concept") == cid]
        sched = concept_schedule(cid, attempts, ticks, c["tier"])
        qs = qbank.get(cid, [])
        out.append({
            **c, **concept_files(cid), "ticks": {k: ticks.get(k) for k in TICKS},
            "q_count": len(qs), "q_sets": dict(Counter(q["set"] for q in qs)),
            "attempts": len(mine),
            "mean": round(sum(a["score"] for a in mine) / len(mine), 2) if mine else None,
            "last_score": mine[-1]["score"] if mine else None,
            "schedule": sched, "level": self_level(cid, attempts, ticks, sched),
            "tutor_status": tracker.get(cid, {}).get("status", ""),
            "tutor_next_review": tracker.get(cid, {}).get("next_review", ""),
        })
    return phases, out
