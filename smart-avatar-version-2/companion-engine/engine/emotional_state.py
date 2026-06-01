import json
import os
from datetime import datetime
 
 
class EmotionalState:
 
    DEFAULTS = {
        "mood": 0.6,
        "energy": 0.8,
        "engagement": 0.6,
        "patience": 0.8,
        "curiosity": 0.6
    }
 
    def __init__(
        self,
        character_name
    ):
 
        character_dir = os.path.join(
            "data",
            "characters",
            character_name
        )
 
        os.makedirs(
            character_dir,
            exist_ok=True
        )
 
        self.file_path = os.path.join(
            character_dir,
            "emotional_state.json"
        )
 
        self.state = {}
 
        self.last_saved = None
 
        self.load()
 
    def load(self):
 
        if os.path.exists(
            self.file_path
        ):
 
            try:
 
                with open(
                    self.file_path,
                    "r"
                ) as f:
 
                    content = (
                        f.read().strip()
                    )
 
                    if content:
 
                        data = json.loads(
                            content
                        )
 
                        self.state = data.get(
                            "state",
                            dict(self.DEFAULTS)
                        )
 
                        self.last_saved = (
                            data.get("last_saved")
                        )
 
                        self._apply_time_decay()
 
                        return
 
            except Exception:
 
                pass
 
        self.state = dict(self.DEFAULTS)
 
        self.last_saved = None
 
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
 
            # 6+ hours - full rest recovery
            if elapsed_hours >= 6:
 
                self.state["energy"] = min(
                    1.0,
                    self.state["energy"] + 0.4
                )
 
                self.state["patience"] = min(
                    1.0,
                    self.state["patience"] + 0.3
                )
 
            # 1+ hour - partial recovery
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
 
        data = {
            "state": self.state,
            "last_saved": (
                datetime.now().isoformat()
            )
        }
 
        with open(
            self.file_path,
            "w"
        ) as f:
 
            json.dump(
                data,
                f,
                indent=4
            )
 
    def apply_delta(
        self,
        deltas
    ):
 
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
 
        mood = self.state["mood"]
        energy = self.state["energy"]
        engagement = self.state["engagement"]
        patience = self.state["patience"]
        curiosity = self.state["curiosity"]
 
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
 
    def get(
        self,
        key
    ):
 
        return self.state.get(key)
 