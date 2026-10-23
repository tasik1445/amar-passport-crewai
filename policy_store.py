"""Prepare and read the offline, SQL-backed cache of published fee data."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RULES_FILE = ROOT / "data" / "rules_2026.json"
DEFAULT_CACHE = ROOT / "data" / "passport_cache.db"


def load_seed():
    return json.loads(RULES_FILE.read_text(encoding="utf-8"))


def ensure_cache(path: Path | str = DEFAULT_CACHE) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    seed = load_seed()
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE IF NOT EXISTS fees (pages INTEGER NOT NULL, validity INTEGER NOT NULL, delivery TEXT NOT NULL, total_bdt INTEGER NOT NULL, PRIMARY KEY(pages,validity,delivery))")
        con.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        for pages, by_year in seed["fees_2026"].items():
            for years, by_speed in by_year.items():
                for speed, amount in by_speed.items():
                    con.execute("INSERT OR REPLACE INTO fees VALUES (?, ?, ?, ?)", (int(pages.split('_')[0]), int(years.split('_')[0]), speed, amount))
        for key in ("title", "last_official_fee_page_update", "last_official_instruction_update"):
            con.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", (key, str(seed[key])))
    return path


def cache_fees(path: Path | str = DEFAULT_CACHE) -> dict:
    path = ensure_cache(path)
    with sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True) as con:
        rows = con.execute("SELECT pages, validity, delivery, total_bdt FROM fees").fetchall()
    return {(pages, years, speed): int(amount) for pages, years, speed, amount in rows}
