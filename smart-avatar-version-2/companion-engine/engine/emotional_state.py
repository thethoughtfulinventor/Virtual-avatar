import sqlite3
import os
from datetime import datetime


class EmotionalState:

    DEFAULTS = {
        "mood":       0.6,
        "energy":     0.8,
        "engagement": 0.6,
        "patience":   0.8,
        "curiosity":  0.6
    }

    def __init__(self, character_name):

        character_dir = os.path.join(
            "data",
            "characters",
            character_name
        )

        os.makedirs(character_dir, exist_ok=True)

        self.db_path = os.path.join(
            character_dir,
            "emotional_state.db"
        )

        self._db = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")

        self.state = {}
        self.last_saved = None

        self._init_db()
        self._load()

    def _init_db(self):

        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS state (
                key   TEXT PRIMARY KEY,
                value REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self._db.commit()

    def _load(self):

        rows = self._db.execute(
            "SELECT key, value FROM state"
        ).fetchall()

        if rows:
            self.state = {k: v for k, v in rows}
        else:
            self.state = dict(self.DEFAULTS)

        meta = self._db.execute(
            "SELECT value FROM meta "
            "WHERE key = 'last_saved'"
        ).fetchone()

        self.last_saved = meta[0] if meta else None

        self._apply_time_decay()

    def _apply_time_decay(self):

        if not self.last_saved:
            return

        try:

            last = datetime.fromisoformat(
                self.last_saved
            )

            elapsed_hours = (
                datetime.now() - last
            ).total_seconds() / 3600

            # 6+ hours — full rest recovery
            if elapsed_hours >= 6:

                self.state["energy"] = min(
                    1.0,
                    self.state["energy"] + 0.4
                )

                self.state["patience"] = min(
                    1.0,
                    self.state["patience"] + 0.3
                )

            # 1+ hour — partial recovery
            elif elapsed_hours >= 1:

                self.state["energy"] = min(
                    1.0,
                    self.state["energy"] + 0.1
                )

                self.state["patience"] = min(
                    1.0,
                    self.state["patience"] + 0.1
                )

        except Exception:
            pass

    def save(self):

        now = datetime.now().isoformat()
        self.last_saved = now

        for key, value in self.state.items():
            self._db.execute(
                "INSERT OR REPLACE INTO state "
                "(key, value) VALUES (?, ?)",
                (key, value)
            )

        self._db.execute(
            "INSERT OR REPLACE INTO meta "
            "(key, value) VALUES ('last_saved', ?)",
            (now,)
        )

        self._db.commit()

    def apply_delta(self, deltas):

        for key, delta in deltas.items():

            if key in self.state:

                self.state[key] = max(
                    0.0,
                    min(
                        1.0,
                        self.state[key] + delta
                    )
                )

        self.save()

    def get_dominant(self):

        mood       = self.state["mood"]
        energy     = self.state["energy"]
        engagement = self.state["engagement"]
        patience   = self.state["patience"]
        curiosity  = self.state["curiosity"]

        # Energy checked first —
        # too tired to feel anything else
        if energy < 0.3:
            return "tired"

        # Patience checked second —
        # frustration overrides positive states
        if patience < 0.3:
            return "frustrated"

        # Positive compound states
        if curiosity > 0.75 and engagement > 0.6:
            return "curious"

        if mood > 0.7 and energy > 0.6:
            return "happy"

        if engagement > 0.7:
            return "focused"

        # Low states
        if engagement < 0.3:
            return "bored"

        if mood < 0.3:
            return "sad"

        return "neutral"

    def get_all(self):

        return dict(self.state)

    def get(self, key):

        return self.state.get(key)