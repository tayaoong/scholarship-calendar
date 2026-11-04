"""SQLite 저장소. 모든 출처(청년정책, 보조금24, 학교 공지)를 한 테이블에 통일된 형태로 저장."""
import hashlib
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,      -- youth | gov24 | school
    school      TEXT,               -- 학교 공지일 때만 (예: ajou)
    title       TEXT NOT NULL,
    url         TEXT,
    deadline    TEXT,               -- YYYY-MM-DD, 모르면 NULL
    period_raw  TEXT,               -- 원문 신청기간 문자열
    region      TEXT,
    amount      TEXT,
    eligibility TEXT,
    docs        TEXT,               -- JSON 배열 (필요 서류)
    summary     TEXT,               -- 쉬운 말 요약
    confidence  TEXT,               -- high | medium | low (AI 추출 신뢰도)
    fetched_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_deadline ON items(deadline);
"""

FIELDS = ["id", "source", "school", "title", "url", "deadline", "period_raw", "region",
          "amount", "eligibility", "docs", "summary", "confidence", "fetched_at"]


def make_id(source: str, key: str) -> str:
    return source + ":" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


class Store:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def has(self, item_id: str) -> bool:
        return self.conn.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone() is not None

    def upsert(self, item: dict) -> None:
        row = {k: item.get(k) for k in FIELDS}
        if isinstance(row["docs"], (list, tuple)):
            row["docs"] = json.dumps(row["docs"], ensure_ascii=False)
        row["fetched_at"] = row["fetched_at"] or datetime.now().isoformat(timespec="seconds")
        cols = ",".join(FIELDS)
        qs = ",".join("?" for _ in FIELDS)
        updates = ",".join(f"{k}=excluded.{k}" for k in FIELDS if k != "id")
        self.conn.execute(
            f"INSERT INTO items ({cols}) VALUES ({qs}) ON CONFLICT(id) DO UPDATE SET {updates}",
            [row[k] for k in FIELDS],
        )
        self.conn.commit()

    def feed(self, today: date | None = None, include_undated: bool = True) -> list[dict]:
        """마감 안 지난 항목을 마감 임박 순으로. 마감일 모르는 건 맨 뒤."""
        today_s = (today or date.today()).isoformat()
        sql = "SELECT * FROM items WHERE deadline >= ?"
        if include_undated:
            sql += " OR deadline IS NULL"
        sql += " ORDER BY deadline IS NULL, deadline ASC, title ASC"
        out = []
        for r in self.conn.execute(sql, (today_s,)):
            d = dict(r)
            d["docs"] = json.loads(d["docs"]) if d["docs"] else []
            out.append(d)
        return out
