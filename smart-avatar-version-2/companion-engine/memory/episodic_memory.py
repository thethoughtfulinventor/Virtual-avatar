import sqlite3
import os
from datetime import datetime


class EpisodicMemory:

    def __init__(self):

        self.db_path = (
            "data/memory/episodes.db"
        )

        os.makedirs(
            os.path.dirname(self.db_path),
            exist_ok=True
        )

        self._db = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")

        self._init_db()

    def _init_db(self):

        self._db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT    NOT NULL,
                summary   TEXT    NOT NULL
            )
        """)
        self._db.commit()

    def add_episode(self, summary):

        self._db.execute(
            "INSERT INTO episodes (timestamp, summary) "
            "VALUES (?, ?)",
            (datetime.now().isoformat(), summary)
        )
        self._db.commit()

    def get_recent(self, count=10):

        rows = self._db.execute(
            "SELECT timestamp, summary FROM episodes "
            "ORDER BY id DESC LIMIT ?",
            (count,)
        ).fetchall()

        return [
            {"timestamp": ts, "summary": s}
            for ts, s in reversed(rows)
        ]

    def clear(self):

        self._db.execute("DELETE FROM episodes")
        self._db.commit()