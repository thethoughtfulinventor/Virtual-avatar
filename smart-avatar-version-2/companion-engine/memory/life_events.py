import sqlite3
import os
from datetime import datetime


class LifeEvents:

    def __init__(self):

        self.db_path = (
            "data/memory/life_events.db"
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
            CREATE TABLE IF NOT EXISTS life_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                description TEXT    NOT NULL
            )
        """)
        self._db.commit()

    def add_event(self, description):

        self._db.execute(
            "INSERT INTO life_events "
            "(timestamp, description) VALUES (?, ?)",
            (datetime.now().isoformat(), description)
        )
        self._db.commit()

    def get_events(self):

        rows = self._db.execute(
            "SELECT timestamp, description "
            "FROM life_events ORDER BY id"
        ).fetchall()

        return [
            {"timestamp": ts, "description": desc}
            for ts, desc in rows
        ]