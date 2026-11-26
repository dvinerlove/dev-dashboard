"""Persistence of runs/issues in SQLite (state.db, WAL). No secrets — they are not in the DB."""
import os
import random
import sqlite3
import threading
import time

DB = os.path.join(__import__("backend").DATA_DIR, "state.db")
_KEEP_RUNS = 50     # per service/project
_KEEP_ISSUES = 200  # total

_con = None
_lock = threading.Lock()  # check_same_thread=False + single connection → serialize writes


def _c():
    global _con
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if _con is None:
        _con = sqlite3.connect(DB, check_same_thread=False)
        _con.execute("PRAGMA journal_mode=WAL")
        _con.execute("PRAGMA busy_timeout=2000")  # writers from different threads
        _con.execute("CREATE TABLE IF NOT EXISTS runs"
                     "(name TEXT, t0 REAL, t1 REAL, exit TEXT)")
        _con.execute("CREATE INDEX IF NOT EXISTS runs_name ON runs(name)")
        _con.execute("CREATE TABLE IF NOT EXISTS issues"
                     "(t REAL, kind TEXT, name TEXT, text TEXT, count INT)")
        _con.execute("CREATE TABLE IF NOT EXISTS remote_probes"
                     "(name TEXT, t REAL, up INT)")
        _con.execute("CREATE INDEX IF NOT EXISTS remote_probes_name"
                     " ON remote_probes(name)")
    return _con


def save_run(name, r):
    """r — dict {t0,t1,exit}; a repeated call updates by _rid."""
    c = _c()
    with _lock:
        if r.get("_rid"):
            c.execute("UPDATE runs SET t1=?, exit=? WHERE rowid=?",
                      (r["t1"], r["exit"], r["_rid"]))
        else:
            cur = c.execute("INSERT INTO runs VALUES(?,?,?,?)",
                            (name, r["t0"], r["t1"], r["exit"]))
            r["_rid"] = cur.lastrowid
            c.execute("DELETE FROM runs WHERE name=? AND rowid NOT IN"
                      "(SELECT rowid FROM runs WHERE name=? ORDER BY t0 DESC LIMIT ?)",
                      (name, name, _KEEP_RUNS))
        c.commit()


def save_issue(it):
    c = _c()
    with _lock:
        if it.get("_rid"):
            c.execute("UPDATE issues SET count=? WHERE rowid=?",
                      (it.get("count", 1), it["_rid"]))
        else:
            cur = c.execute("INSERT INTO issues VALUES(?,?,?,?,?)",
                            (it["t"], it["kind"], it["name"], it["text"],
                             it.get("count", 1)))
            it["_rid"] = cur.lastrowid
            c.execute("DELETE FROM issues WHERE rowid NOT IN"
                      "(SELECT rowid FROM issues ORDER BY t DESC LIMIT ?)",
                      (_KEEP_ISSUES,))
        c.commit()


def clear_issues():
    c = _c()
    with _lock:
        c.execute("DELETE FROM issues")
        c.commit()


def load():
    """-> (runs {name: [dict]}, issues [dict]) in ascending time order."""
    c = _c()
    runs = {}
    for name, t0, t1, ex, rid in c.execute(
            "SELECT name,t0,t1,exit,rowid FROM runs ORDER BY t0"):
        runs.setdefault(name, []).append(
            {"t0": t0, "t1": t1, "exit": ex, "_rid": rid})
    issues = [{"t": t, "kind": k, "name": n, "text": x, "count": cnt, "_rid": rid}
              for t, k, n, x, cnt, rid in c.execute(
                  "SELECT t,kind,name,text,count,rowid FROM issues ORDER BY t")]
    return runs, issues


def remote_probe(name, up):
    """One availability sample of a remote monitor. ~2% of calls also prune
    samples older than 48h — amortized cleanup, no separate timer."""
    c = _c()
    with _lock:
        c.execute("INSERT INTO remote_probes VALUES(?,?,?)",
                  (name, time.time(), 1 if up else 0))
        if random.random() < 0.02:
            c.execute("DELETE FROM remote_probes WHERE t<?",
                      (time.time() - 48 * 3600,))
        c.commit()


def uptime_pct(name, hours=24):
    """% of up-samples for the remote in the last `hours` hours.
    None — fewer than 3 samples, the number would be noise."""
    n, ups = _c().execute(
        "SELECT COUNT(*), COALESCE(SUM(up),0) FROM remote_probes"
        " WHERE name=? AND t>?",
        (name, time.time() - hours * 3600)).fetchone()
    return ups / n * 100 if n >= 3 else None
