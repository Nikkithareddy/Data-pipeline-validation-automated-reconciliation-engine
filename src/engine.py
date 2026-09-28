"""Loads SQL check files, runs them, and returns structured results."""
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
HEADER = re.compile(r"^--\s*@check\s+(\w+)\s*\|\s*([^|]+)\|\s*(.+)$")


@dataclass
class Check:
    check_id: str
    category: str
    name: str
    sql: str
    detail_sql: str = ""


@dataclass
class Result:
    check: Check
    actual: float
    expected: float = 0
    executed_at: str = ""
    details: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.actual == self.expected


def load_checks(*files: str) -> list[Check]:
    checks: list[Check] = []
    for fname in files:
        current, buf, mode = None, {"sql": [], "detail": []}, "sql"

        def flush():
            if current:
                checks.append(Check(*current, " ".join(buf["sql"]).strip(), " ".join(buf["detail"]).strip()))

        for line in (SQL_DIR / fname).read_text().splitlines():
            m = HEADER.match(line.strip())
            if m:
                flush()
                current = (m.group(1).strip(), m.group(2).strip(), m.group(3).strip())
                buf, mode = {"sql": [], "detail": []}, "sql"
            elif line.strip() == "-- @detail":
                mode = "detail"
            elif current and line.strip() and not line.strip().startswith("--"):
                buf[mode].append(line.strip())
        flush()
    return checks


def run_checks(conn: sqlite3.Connection, checks: list[Check], detail_limit: int = 20) -> list[Result]:
    results = []
    for c in checks:
        actual = conn.execute(c.sql.rstrip(";")).fetchone()[0] or 0
        res = Result(c, actual, executed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not res.passed and c.detail_sql:
            cur = conn.execute(c.detail_sql.rstrip(";") + f" LIMIT {detail_limit}")
            res.details = [[d[0] for d in cur.description]] + [list(r) for r in cur.fetchall()]
        results.append(res)
    return results


def apply_cleanup(conn: sqlite3.Connection) -> None:
    conn.executescript((SQL_DIR / "cleanup.sql").read_text())
    conn.commit()
