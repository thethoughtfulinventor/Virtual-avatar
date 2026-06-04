import sqlite3
import os
from datetime import datetime


class RecentContext:

    def __init__(self, max_entries=50):

        self.max_entries = max_entries

        self.db_path = (
            "data/memory/recent_context.db"
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
            CREATE TABLE IF NOT EXISTS context (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT    NOT NULL,
                content   TEXT    NOT NULL,
                character TEXT,
                ts        TEXT    NOT NULL
            )
        """)
        self._db.commit()

    def add(self, role, content, character=None):

        self._db.execute(
            "INSERT INTO context "
            "(role, content, character, ts) "
            "VALUES (?, ?, ?, ?)",
            (
                role,
                content,
                character,
                datetime.now().isoformat()
            )
        )

        # Trim to max_entries so the table
        # never grows unbounded
        self._db.execute("""
            DELETE FROM context
            WHERE id NOT IN (
                SELECT id FROM context
                ORDER BY id DESC
                LIMIT ?
            )
        """, (self.max_entries,))

        self._db.commit()

    def get_recent(self, count=10):

        rows = self._db.execute(
            "SELECT role, content, character "
            "FROM context "
            "ORDER BY id DESC LIMIT ?",
            (count,)
        ).fetchall()

        result = []

        for role, content, character in reversed(rows):

            entry = {
                "role": role,
                "content": content
            }

            if character:
                entry["character"] = character

            result.append(entry)

        return result

    def keep_last(self, n):
        """
        Trim context so only the n most
        recent entries remain. Used by
        MemoryManager.compress_context()
        after storing an episode summary.
        """

        self._db.execute("""
            DELETE FROM context
            WHERE id NOT IN (
                SELECT id FROM context
                ORDER BY id DESC
                LIMIT ?
            )
        """, (n,))
        self._db.commit()

    def count(self):
        """
        Returns total number of stored entries.
        Avoids fetching all rows just to check length.
        """

        row = self._db.execute(
            "SELECT COUNT(*) FROM context"
        ).fetchone()

        return row[0] if row else 0

    def clear(self):

        self._db.execute("DELETE FROM context")
        self._db.commit()