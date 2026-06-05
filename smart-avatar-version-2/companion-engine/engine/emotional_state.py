import sqlite3
import os
from datetime import datetime


class EmotionalState:
    """
    Persistent emotional state for a single character.

    v2 fixes
    --------
    1. _apply_time_decay now calls save() after modifying
       state so the decayed values are persisted immediately.
       Previously, decay was applied in memory on every load
       but never written back until the next interaction —
       meaning a session with no interactions would always
       re-apply the same decay on the next launch.

    2. Added a `_decay_applied` flag so that if multiple
       EmotionalState objects are created for the same
       character in one session (e.g. rapid character
       switching), decay is only applied once per load.

    3. State keys are validated against DEFAULTS on load
       so schema additions don't crash older DB files.
    """

    DEFAULTS = {
        "mood":       0.6,
        "energy":     0.8,
        "engagement": 0.6,
        "patience":   0.8,
        "curiosity":  0.6,
    }

    def __init__(self, character_name: str):
        character_dir = os.path.join(
            "data", "characters", character_name
        )
        os.makedirs(character_dir, exist_ok=True)

        self.db_path = os.path.join(
            character_dir, "emotional_state.db"
        )

        print(
            "[Emotion ABSOLUTE]",
            os.path.abspath(self.db_path)
        )

        self._db = sqlite3.connect(
            self.db_path, check_same_thread=False
        )
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")

        self.state:      dict[str, float] = {}
        self.last_saved: str | None       = None
        self._decay_applied               = False

        self._init_db()
        self._load()

    # --------------------------------------------------
    # Setup
    # --------------------------------------------------

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
            loaded = {k: v for k, v in rows}
            # Merge with defaults so new keys are always present
            self.state = {**self.DEFAULTS, **loaded}
        else:
            self.state = dict(self.DEFAULTS)

        meta = self._db.execute(
            "SELECT value FROM meta WHERE key = 'last_saved'"
        ).fetchone()
        self.last_saved = meta[0] if meta else None

        print(
            f"[Emotion LOAD] "
            f"{self.db_path}"
        )

        print(
            f"[Emotion LOAD STATE] "
            f"{self.state}"
        )

        self._apply_time_based_recovery()
        self.save()  # important: persist recovered state immediately

    def _apply_time_decay(self):
        """
        Recover energy and patience based on elapsed time
        since the last session.

        FIX: now saves the post-decay state so the same
        decay isn't re-applied on the next load.
        """
        if self._decay_applied or not self.last_saved:
            return

        self._decay_applied = True

        try:
            last = datetime.fromisoformat(self.last_saved)
            elapsed_hours = (
                (datetime.now() - last).total_seconds() / 3600
            )

            if elapsed_hours >= 6:
                # Full rest recovery
                self.state["energy"]   = min(1.0, self.state["energy"]   + 0.4)
                self.state["patience"] = min(1.0, self.state["patience"] + 0.3)
                self.save()   # FIX: persist immediately

            elif elapsed_hours >= 1:
                # Partial recovery
                self.state["energy"]   = min(1.0, self.state["energy"]   + 0.1)
                self.state["patience"] = min(1.0, self.state["patience"] + 0.1)
                self.save()   # FIX: persist immediately

        except Exception:
            pass

    # --------------------------------------------------
    # Persistence
    # --------------------------------------------------

    def save(self):
        print(
            f"[Emotion SAVE] "
            f"{self.db_path}"
        )
        print(
            f"[Emotion SAVE STATE] "
            f"{self.state}"
        )
        now = datetime.now().isoformat()
        self._apply_time_based_recovery()
        self.last_saved = now

        for key, value in self.state.items():
            self._db.execute(
                "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
                (key, value),
            )

        self._db.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_saved', ?)",
            (now,),
        )
        self._db.commit()
        rows = self._db.execute(
            "SELECT key, value FROM state"
        ).fetchall()

        print("[Emotion VERIFY]", rows)

    # --------------------------------------------------
    # State mutation
    # --------------------------------------------------

    def apply_delta(self, deltas: dict):

        print(
            f"[Emotion BEFORE] "
            f"{self.db_path} "
            f"{self.state}"
        )

        for key, delta in deltas.items():
            if key in self.state:
                self.state[key] = max(
                    0.0,
                    min(1.0, self.state[key] + delta)
                )

        print(
            f"[Emotion AFTER] "
            f"{self.db_path} "
            f"{self.state}"
        )

        self.save()

    # --------------------------------------------------
    # Queries
    # --------------------------------------------------

    def get_dominant(self) -> str:
        mood       = self.state["mood"]
        energy     = self.state["energy"]
        engagement = self.state["engagement"]
        patience   = self.state["patience"]
        curiosity  = self.state["curiosity"]

        # Checked in priority order
        if energy   < 0.3: return "tired"
        if patience < 0.3: return "frustrated"
        if curiosity  > 0.75 and engagement > 0.6: return "curious"
        if mood       > 0.7  and energy     > 0.6: return "happy"
        if engagement > 0.7:                        return "focused"
        if engagement < 0.3:                        return "bored"
        if mood       < 0.3:                        return "sad"
        return "neutral"

    def get_all(self) -> dict:
        return dict(self.state)

    def get(self, key: str) -> float | None:
        return self.state.get(key)
    
    def _apply_time_based_recovery(self):
        """
        Slowly returns emotions toward character-specific baselines
        based on time elapsed since last save.
        """

        if not self.last_saved:
            return

        try:
            last = datetime.fromisoformat(self.last_saved)
            now = datetime.now()

            hours_elapsed = (now - last).total_seconds() / 3600

            if hours_elapsed <= 0:
                return

            # pull baselines from character JSON (inject this later)
            baselines = getattr(self, "baselines", self.DEFAULTS)

            # recovery strength scales with time, but caps out
            recovery_rate = min(0.25, hours_elapsed * 0.02)

            for key in self.state:
                baseline = baselines.get(key, self.DEFAULTS.get(key, 0.5))

                current = self.state[key]

                # “spring toward baseline”
                self.state[key] = current + (baseline - current) * recovery_rate

                # clamp immediately
                self.state[key] = max(0.0, min(1.0, self.state[key]))

        except Exception as e:
            print(f"[Emotion RECOVERY ERROR] {e}")