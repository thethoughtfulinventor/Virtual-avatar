#!/usr/bin/env python3
"""
migrate.py — Import existing JSON memory files into SQLite.

Run ONCE from the companion-engine directory before starting
the engine with the new SQL storage:

    python3 migrate.py

After confirming everything looks correct you can delete
the old .json files listed at the end of the output.
"""

import json
import os
import sys
from datetime import datetime


def _read_json(path):
    """Return parsed JSON or None if file missing/unreadable."""
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            content = f.read().strip()
        return json.loads(content) if content else None
    except Exception as e:
        print(f"  ⚠  Could not read {path}: {e}")
        return None


# ----------------------------------------------------------
# Individual migrators
# ----------------------------------------------------------

def migrate_user_profile():
    data = _read_json("data/memory/user_profile.json")
    if data is None:
        print("  user_profile.json  — not found, skipping")
        return 0
    from memory.user_profile import UserProfile
    profile = UserProfile()
    for key, value in data.items():
        profile.set_fact(key, str(value))
    print(f"  user_profile.json  — {len(data)} facts migrated")
    return len(data)


def migrate_episodes():
    data = _read_json("data/memory/episodes.json")
    if not data:
        print("  episodes.json      — not found / empty, skipping")
        return 0
    from memory.episodic_memory import EpisodicMemory
    em = EpisodicMemory()
    for ep in data:
        ts = ep.get("timestamp", datetime.now().isoformat())
        summary = ep.get("summary", "").strip()
        if summary:
            em._db.execute(
                "INSERT INTO episodes (timestamp, summary) VALUES (?, ?)",
                (ts, summary)
            )
    em._db.commit()
    print(f"  episodes.json      — {len(data)} episodes migrated")
    return len(data)


def migrate_recent_context():
    data = _read_json("data/memory/recent_context.json")
    if not data:
        print("  recent_context.json — not found / empty, skipping")
        return 0
    from memory.recent_context import RecentContext
    rc = RecentContext()
    ts = datetime.now().isoformat()
    for entry in data:
        rc._db.execute(
            "INSERT INTO context (role, content, character, ts) "
            "VALUES (?, ?, ?, ?)",
            (
                entry.get("role", "user"),
                entry.get("content", ""),
                entry.get("character"),
                ts
            )
        )
    rc._db.commit()
    print(f"  recent_context.json — {len(data)} entries migrated")
    return len(data)


def migrate_projects():
    data = _read_json("data/memory/projects.json")
    if not data:
        print("  projects.json      — not found / empty, skipping")
        return 0
    from memory.project_manager import ProjectManager
    pm = ProjectManager()
    for name, proj in data.items():
        pm._db.execute(
            "INSERT OR REPLACE INTO projects "
            "(name, status, last_updated) VALUES (?, ?, ?)",
            (
                name,
                proj.get("status", "active"),
                proj.get("last_updated", datetime.now().isoformat())
            )
        )
    pm._db.commit()
    print(f"  projects.json      — {len(data)} projects migrated")
    return len(data)


def migrate_life_events():
    data = _read_json("data/memory/life_events.json")
    if not data:
        print("  life_events.json   — not found / empty, skipping")
        return 0
    from memory.life_events import LifeEvents
    le = LifeEvents()
    for event in data:
        le._db.execute(
            "INSERT INTO life_events (timestamp, description) VALUES (?, ?)",
            (
                event.get("timestamp", datetime.now().isoformat()),
                event.get("description", "")
            )
        )
    le._db.commit()
    print(f"  life_events.json   — {len(data)} events migrated")
    return len(data)


def migrate_emotional_states():
    chars_dir = "data/characters"
    if not os.path.exists(chars_dir):
        print("  emotional states   — no characters directory, skipping")
        return 0

    count = 0
    from emotion.emotional_state import EmotionalState

    for char_name in sorted(os.listdir(chars_dir)):
        json_path = os.path.join(
            chars_dir, char_name, "emotional_state.json"
        )
        if not os.path.exists(json_path):
            continue

        data = _read_json(json_path)
        if not data:
            continue

        es = EmotionalState(char_name)
        state = data.get("state", {})

        for key, value in state.items():
            if key in es.state:
                es.state[key] = float(value)

        last_saved = data.get("last_saved")
        if last_saved:
            es.last_saved = last_saved

        es.save()
        print(
            f"  {char_name}/emotional_state.json "
            f"— migrated"
        )
        count += 1

    return count


# ----------------------------------------------------------
# Entry point
# ----------------------------------------------------------

if __name__ == "__main__":

    print("=" * 52)
    print("  JSON → SQLite Migration")
    print("=" * 52)

    if not os.path.exists("main.py"):
        print(
            "\nError: run this from the "
            "companion-engine directory.\n"
            "  cd companion-engine && python3 migrate.py"
        )
        sys.exit(1)

    print()
    total = 0
    total += migrate_user_profile()
    total += migrate_episodes()
    total += migrate_recent_context()
    total += migrate_projects()
    total += migrate_life_events()
    total += migrate_emotional_states()

    print()
    print(f"Done — {total} records written to SQLite.")
    print()
    print(
        "Once you're satisfied the data looks correct,\n"
        "you can remove the old JSON files:\n\n"
        "  data/memory/user_profile.json\n"
        "  data/memory/episodes.json\n"
        "  data/memory/recent_context.json\n"
        "  data/memory/projects.json\n"
        "  data/memory/life_events.json\n"
        "  data/characters/*/emotional_state.json"
    )