import sqlite3
import os


class UserProfile:

    def __init__(self):

        self.db_path = (
            "data/memory/user_profile.db"
        )

        self.data = {}

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
        self._load()

    def _init_db(self):

        self._db.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self._db.commit()

    def _load(self):

        rows = self._db.execute(
            "SELECT key, value FROM profile"
        ).fetchall()

        self.data = {k: v for k, v in rows}

    def set_fact(self, key, value):

        self.data[key] = value

        self._db.execute(
            "INSERT OR REPLACE INTO profile "
            "(key, value) VALUES (?, ?)",
            (key, value)
        )
        self._db.commit()

    def get_fact(self, key):

        return self.data.get(key)

    def remove_fact(self, key):

        if key in self.data:

            del self.data[key]

            self._db.execute(
                "DELETE FROM profile WHERE key = ?",
                (key,)
            )
            self._db.commit()