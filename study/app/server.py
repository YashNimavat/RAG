"""Local study website: reading, quizzes, progress and calibration. Works offline.

Run from rag_learning/:
    uv run python study/app/server.py            # opens http://127.0.0.1:8765
    uv run python study/app/server.py --no-browser --port 8800

Standard library only. Listens on 127.0.0.1, so nothing is reachable from other machines.
Writes only progress/study_attempts.jsonl and progress/study_state.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import mimetypes
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import kit  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
mimetypes.add_type("font/woff2", ".woff2")           # lessons bundle their reading fonts
DOC_SUFFIXES = {".md", ".png", ".jpg", ".jpeg", ".gif", ".svg"}
BLOCKED_PARTS = {".venv", ".git", "AI Eval", "__pycache__"}
LOCK = threading.Lock()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _doc_path(relpath: str) -> Path | None:
    p = (kit.ROOT / relpath).resolve()
    if not _inside(p, kit.ROOT) or p.suffix.lower() not in DOC_SUFFIXES or not p.is_file():
        return None
    if BLOCKED_PARTS & set(p.relative_to(kit.ROOT.resolve()).parts):
        return None
    return p


def _find_question(qid: str, concept: str) -> dict | None:
    path = kit.QDIR / f"{concept}_questions.md"
    if not path.exists():
        return None
    return next((q for q in kit.parse_questions(path) if q["id"] == qid), None)


def overview() -> dict:
    attempts, state = kit.load_attempts(), kit.load_state()
    phases, concepts = kit.concept_summaries(attempts, state)
    st = kit.stats(attempts)
    due = [c for c in concepts if c["schedule"] and c["schedule"]["due"]]
    due.sort(key=lambda c: (-c["schedule"]["overdue_days"], "EUS".find(c["tier"][:1] or "E")))
    started = [c for c in concepts if any(c["ticks"].values()) or c["attempts"]]
    # "Next new concept": first one in curriculum order that has study material and is untouched.
    fresh = next((c for c in concepts if c["phase"] >= 1 and (c["short"] or c["full"])
                  and not any(c["ticks"].values()) and not c["attempts"]), None)
    return {
        "today": kit.today().isoformat(), "root": str(kit.ROOT), "phases": phases, "concepts": concepts,
        "due": [c["id"] for c in due], "next_new": fresh["id"] if fresh else None,
        "tiles": {
            "concepts_total": sum(c["phase"] >= 1 for c in concepts),
            "with_reading": sum(bool(c["short"] or c["full"]) for c in concepts),
            "with_questions": sum(c["q_count"] > 0 for c in concepts),
            "started": len(started),
            "read": sum(bool(c["ticks"]["read_short"] or c["ticks"]["read_full"]) for c in concepts),
            "answers": st["total"], "mean": st["overall"]["mean"], "good": st["overall"]["good"],
            "due": len(due), "sure_wrong": len(st["sure_wrong"]),
        },
    }


def concept_detail(cid: str) -> dict | None:
    attempts, state = kit.load_attempts(), kit.load_state()
    _, concepts = kit.concept_summaries(attempts, state)
    c = next((x for x in concepts if x["id"] == cid), None)
    if not c:
        return None
    qpath = kit.QDIR / f"{cid}_questions.md"
    qs = kit.parse_questions(qpath) if qpath.exists() else []
    mine = [a for a in attempts if a.get("concept") == cid]
    last = kit.last_by_question(mine)
    return {**c, "questions": qs, "history": mine[-200:],
            "last": {k: {"score": v["score"], "date": v["date"], "confidence": v.get("confidence")}
                     for k, v in last.items()}}


def quiz(cid: str, mode: str) -> dict:
    path = kit.QDIR / f"{cid}_questions.md"
    if not path.exists():
        return {"questions": [], "mode": mode}
    qs = kit.parse_questions(path)
    return {"questions": kit.pick_questions(qs, kit.load_attempts(), mode), "mode": mode}


def save_attempt(body: dict) -> dict:
    q = _find_question(str(body.get("qid", "")), str(body.get("concept", "")))
    if not q:
        raise ValueError("unknown question")
    ans = q["answer"]

    def picks(name, n):
        return sorted({int(i) for i in body.get(name, []) if 0 <= int(i) < n})

    key_hit, four_hit = picks("key_hit", len(ans["keys"])), picks("four_hit", len(ans["four"]))
    wrong_hit = picks("wrong_hit", len(ans["wrong"]))
    hint = max(0, min(3, int(body.get("hint_level", 0))))
    assisted = bool(body.get("assisted"))
    conf = body.get("confidence")
    conf = int(conf) if conf in (1, 2, 3, "1", "2", "3") else None
    # The server recomputes the score from the ticks (FORMAT.md §2.4); the page cannot set it.
    score, why = kit.score_from_ticks(len(key_hit), len(ans["keys"]), len(four_hit), len(ans["four"]),
                                      len(wrong_hit), hint, assisted)
    now = dt.datetime.now()
    row = {
        "ts": now.isoformat(timespec="seconds"), "date": now.date().isoformat(),
        "qid": q["id"], "concept": q["concept"], "type": q["type"], "set": q["set"],
        "answer": str(body.get("answer", ""))[:20000], "confidence": conf, "hint_level": hint,
        "assisted": assisted, "key_hit": key_hit, "key_total": len(ans["keys"]),
        "four_hit": four_hit, "four_total": len(ans["four"]), "wrong_hit": wrong_hit,
        "wrong_text": [ans["wrong"][i] for i in wrong_hit], "score": score, "why": why,
        "grader": "self", "mode": "web",
    }
    with LOCK:
        kit.append_attempt(row)
    return row


def tick(body: dict) -> dict:
    with LOCK:
        state = kit.load_state()
        c = kit.set_tick(state, str(body["concept"]), str(body["field"]), bool(body.get("on")))
        kit.save_state(state)
    return c


class Handler(BaseHTTPRequestHandler):
    server_version = "StudyKit/1"

    def log_message(self, fmt, *args):  # quiet console
        pass

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status: int = 200) -> None:
        self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _file(self, path: Path) -> None:
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix == ".md":
            ctype = "text/markdown"
        if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self._send(200, path.read_bytes(), ctype)

    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        qs = {k: v[0] for k, v in parse_qs(url.query).items()}
        route = unquote(url.path)
        try:
            if route in ("/", "/index.html"):
                return self._file(STATIC / "index.html")
            if route.startswith("/static/"):
                p = (STATIC / route[len("/static/"):]).resolve()
                if _inside(p, STATIC) and p.is_file():
                    return self._file(p)
            if route.startswith("/lesson/"):
                lessons = kit.ROOT / "study" / "lessons"
                p = (lessons / route[len("/lesson/"):]).resolve()
                if _inside(p, lessons) and p.suffix.lower() in (".html", ".woff2") and p.is_file():
                    return self._file(p)
            if route.startswith("/book/"):
                p = (kit.BOOK_DIR / route[len("/book/"):]).resolve()
                if _inside(p, kit.BOOK_DIR) and p.suffix.lower() == ".pdf" and p.is_file():
                    return self._file(p)
            if route == "/api/overview":
                return self._json(overview())
            if route == "/api/concept":
                d = concept_detail(qs.get("id", ""))
                return self._json(d) if d else self._json({"error": "unknown concept"}, 404)
            if route == "/api/quiz":
                return self._json(quiz(qs.get("id", ""), qs.get("mode", "next")))
            if route == "/api/stats":
                return self._json(kit.stats(kit.load_attempts()))
            if route == "/api/doc":
                p = _doc_path(qs.get("path", ""))
                if p:
                    return self._file(p)
            if route == "/api/lint":
                return self._json({p.name: kit.lint_questions(p) for p in sorted(kit.QDIR.glob("*_questions.md"))})
            if route == "/api/export":
                return self._json({"attempts": kit.load_attempts(), "state": kit.load_state()})
            self._json({"error": "not found"}, 404)
        except Exception as exc:  # keep the page alive; show the reason
            self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)

    def do_POST(self):  # noqa: N802
        route = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n) or b"{}")
            if route == "/api/attempt":
                return self._json(save_attempt(body))
            if route == "/api/tick":
                return self._json(tick(body))
            self._json({"error": "not found"}, 404)
        except Exception as exc:
            self._json({"error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.BAD_REQUEST)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Study kit running at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
