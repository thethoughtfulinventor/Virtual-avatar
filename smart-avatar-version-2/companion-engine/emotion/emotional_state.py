import sqlite3
import os
from datetime import datetime


class EmotionalState:
    """
    Persistent emotional state for a single character.
    Cleaned version: single recovery system, no duplicate decay logic.
    """

    DEFAULTS = {
        "mood": 0.6,
        "energy": 0.8,
        "engagement": 0.6,
        "patience": 0.8,
        "curiosity": 0.6,
    }

    # --------------------------------------------------
    # init
    # --------------------------------------------------

    def __init__(self, character_name: str):
        self.character_dir = os.path.join("data", "characters", character_name)
        os.makedirs(self.character_dir, exist_ok=True)

        self.db_path = os.path.join(self.character_dir, "emotional_state.db")

        self._db = sqlite3.connect(self.db_path, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")

        self.state: dict[str, float] = dict(self.DEFAULTS)
        self.last_saved: str | None = None

        self._init_db()
        self._load()

    # --------------------------------------------------
    # DB setup
    # --------------------------------------------------

    def _init_db(self):
        self._db.executescript("""
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
        self._db.commit()

    # --------------------------------------------------
    # load
    # --------------------------------------------------

    def _load(self):
        rows = self._db.execute("SELECT key, value FROM state").fetchall()
        self.state = {**self.DEFAULTS, **dict(rows)} if rows else dict(self.DEFAULTS)

        meta = self._db.execute(
            "SELECT value FROM meta WHERE key='last_saved'"
        ).fetchone()

        self.last_saved = meta[0] if meta else None

        self._apply_time_recovery()
        self.save(persist_recovery=False)

    # --------------------------------------------------
    # time system (ONLY ONE)
    # --------------------------------------------------

    def _apply_time_recovery(self):
        """
        Single unified time-based recovery system.
        Replaces both decay + recovery logic.
        """
        if not self.last_saved:
            return

        try:
            last = datetime.fromisoformat(self.last_saved)
            hours = (datetime.now() - last).total_seconds() / 3600

            if hours <= 0:
                return

            # baseline system (future hook for JSON personality tuning)
            baselines = getattr(self, "baselines", self.DEFAULTS)

            # recovery curve (smooth + capped)
            rate = min(0.25, hours * 0.02)

            for k in self.state:
                baseline = baselines.get(k, self.DEFAULTS[k])
                current = self.state[k]

                self.state[k] = current + (baseline - current) * rate
                self.state[k] = max(0.0, min(1.0, self.state[k]))

        except Exception as e:
            print(f"[Emotion RECOVERY ERROR] {e}")

    # --------------------------------------------------
    # persistence
    # --------------------------------------------------

    def save(self, persist_recovery: bool = True):
        """
        Saves state to DB.

        persist_recovery=False prevents double recovery on load.
        """
        if persist_recovery:
            self._apply_time_recovery()

        now = datetime.now().isoformat()
        self.last_saved = now

        self._db.executemany(
            "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
            self.state.items(),
        )

        self._db.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_saved', ?)",
            (now,),
        )

        self._db.commit()

    # --------------------------------------------------
    # mutation
    # --------------------------------------------------

    def apply_delta(self, deltas: dict[str, float]):
        for k, d in deltas.items():
            if k in self.state:
                self.state[k] = max(0.0, min(1.0, self.state[k] + d))

        self.save()

    # --------------------------------------------------
    # queries
    # --------------------------------------------------

    def get_dominant(self) -> str:
        s = self.state

        if s["energy"] < 0.3:
            return "tired"
        if s["patience"] < 0.3:
            return "frustrated"
        if s["curiosity"] > 0.75 and s["engagement"] > 0.6:
            return "curious"
        if s["mood"] > 0.7 and s["energy"] > 0.6:
            return "happy"
        if s["engagement"] > 0.7:
            return "focused"
        if s["engagement"] < 0.3:
            return "bored"
        if s["mood"] < 0.3:
            return "sad"
        return "neutral"

    def get_all(self):
        return dict(self.state)

    def get(self, key: str):
        return self.state.get(key)