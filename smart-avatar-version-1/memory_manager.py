# memory_manager.py
import sqlite3
import os
from langchain_core.messages import HumanMessage, AIMessage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "avatar_memory.db")
PROFILE_DB_PATH = os.path.join(DATA_DIR, "user_profile.db")  # ISOLATED IMMUNE PROFILE

def init_db():
    """Initializes the chat memory database and the separate user profile database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Standard Chat Log Database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            role TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

    # 2. Reset-Resistant User Profile Database
    conn_prof = sqlite3.connect(PROFILE_DB_PATH)
    cursor_prof = conn_prof.cursor()
    cursor_prof.execute('''
        CREATE TABLE IF NOT EXISTS profile_facts (
            fact_key TEXT PRIMARY KEY,
            fact_value TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn_prof.commit()
    conn_prof.close()

def save_message(role: str, content: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def load_memory_context(limit: int = 4):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()[::-1]
    conn.close()
    
    messages = []
    for role, content in rows:
        if role == "human":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            messages.append(AIMessage(content=content))
    return messages

# --- USER PROFILE PERSISTENCE ENGINE ---
def store_user_fact(key: str, value: str):
    """Saves a specific fact about the human into the immune database profile."""
    init_db()
    conn = sqlite3.connect(PROFILE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO profile_facts (fact_key, fact_value) VALUES (?, ?)", (key.lower().strip(), value.strip()))
    conn.commit()
    conn.close()

def compile_known_user_profile() -> str:
    """Compiles all stored facts about the user into a clean text block."""
    init_db()
    conn = sqlite3.connect(PROFILE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT fact_key, fact_value FROM profile_facts")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "You currently know nothing about this human user yet. Ask questions to find out their preferences!"
        
    profile_summary = "Absolute Facts Known About This Human User:\n"
    for key, value in rows:
        profile_summary += f"- {key}: {value}\n"
    return profile_summary

