import sqlite3
import os
from datetime import datetime


class ProjectManager:

    def __init__(self):

        self.db_path = (
            "data/memory/projects.db"
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
            CREATE TABLE IF NOT EXISTS projects (
                name         TEXT PRIMARY KEY,
                status       TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        self._db.commit()

    def create_project(self, name):

        self._db.execute(
            "INSERT OR REPLACE INTO projects "
            "(name, status, last_updated) "
            "VALUES (?, ?, ?)",
            (name, "active", datetime.now().isoformat())
        )
        self._db.commit()

    def get_project(self, name):

        row = self._db.execute(
            "SELECT status, last_updated "
            "FROM projects WHERE name = ?",
            (name,)
        ).fetchone()

        if row:
            return {
                "status": row[0],
                "last_updated": row[1]
            }

        return None

    def list_projects(self):

        rows = self._db.execute(
            "SELECT name FROM projects "
            "ORDER BY name"
        ).fetchall()

        return [r[0] for r in rows]

    def update_project(self, name, field, value):

        # Whitelist prevents SQL injection
        # through the field parameter
        allowed = {"status", "last_updated"}

        if field not in allowed:
            return

        self._db.execute(
            f"UPDATE projects "
            f"SET {field} = ?, last_updated = ? "
            f"WHERE name = ?",
            (value, datetime.now().isoformat(), name)
        )
        self._db.commit()