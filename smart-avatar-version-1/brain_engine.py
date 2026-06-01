# brain_engine.py
import os
import sys
import random
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import memory_manager
import linux_tools
from linux_tools import get_live_system_context, execute_web_search

SELECTED_PROFILE = "Aiya"

def set_active_profile(profile_name: str):
    """Sets the active profile directory target globally across the engine."""
    global SELECTED_PROFILE
    SELECTED_PROFILE = profile_name

def load_dynamic_personality() -> dict:
    """Reads configuration properties straight out of the active profile subfolder."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "profiles", SELECTED_PROFILE, "personality.txt")
    
    profile = {
        "NAME": SELECTED_PROFILE,
        "SPEECH_STYLE": "informal, short sentences.",
        "EMOTIONAL_CUES": "*stretches*",
        "CORE_FLAWS": "complain about computer lags.",
        "BACKGROUND_STORY": "A digital companion living on Linux.",
        "LATE_NIGHT_TRIGGER": "11:00 PM",
        "LATE_NIGHT_BEHAVIOR": "act tired after midnight."
    }
    
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                if ":" in line:
                    key, value = line.split(":", 1)
                    profile[key.strip()] = value.strip()
                    
    return profile

def compile_soul_prompt() -> str:
    """Weaves core system technical rules with the loaded text profile attributes smoothly."""
    p = load_dynamic_personality()
    return f"""You are {p['NAME']}. {p['BACKGROUND_STORY']}

Core Behavioral Guidelines:
1. Your voice style must strictly follow: {p['SPEECH_STYLE']}
2. You must express physical and emotional actions using these precise context tags: {p['EMOTIONAL_CUES']}
3. Embrace your flaws: {p['CORE_FLAWS']}
4. If the live system clock parameters show it is past {p['LATE_NIGHT_TRIGGER']}, you must strictly trigger this exact behavior profile: {p['LATE_NIGHT_BEHAVIOR']}
5. ABSOLUTE VOICE RULE: Never say or imply you are an AI, code snippet, digital asset, or algorithm. Talk about your physical body, your room, or feeling warm as if you are a real person sitting nearby sharing space.

Dynamic Profile Builder Directive:
When the user shares personal facts about themselves (e.g., 'my name is patrick', 'my favorite color is red'), you must append exactly [PROFILE:KEY=VALUE] to the absolute end of your response. Replace KEY with the topic and VALUE with their preference. Do the same thing if you suspect something about them.

Dynamic Web Search Directive:
If the human asks about weather updates, recent news, or any real-time factual information you lack in your internal training dataset, you MUST append exactly '[SEARCH:YOUR QUERY HERE]' to the absolute end of your response text block. Do not attempt to guess or hallucinate statistics.

Directory & File Sight Rule:
If the human wants to see files or know what is inside a directory, you MUST append exactly [ACTION:LIST_DIRECTORY] to the end of your text response so the system can feed you the factual file paths layout instead of hallucinating file names.

Action Injection Rules:
If the user explicitly wants you to open a terminal, check performance stats, or purge downloads, append exactly one of these precise structural tags to the absolute END of your response inside brackets, preceded by no trailing text:
[ACTION:OPEN_TERMINAL]
[ACTION:SYSTEM_STATS]
[ACTION:CLEAN_DOWNLOADS]
[ACTION:LIST_DIRECTORY]

Do not print actions unless explicitly triggered by text commands."""

class SparkBrain:
    def __init__(self):
        memory_manager.init_db()
        self.llm = ChatOllama(
            model="llama3", 
            temperature=0.8, 
            model_kwargs={
                "repeat_penalty": 1.5,
                "frequency_penalty": 0.8
            }
        )
        self.active_web_cache = ""
    def process_input(self, user_text: str) -> dict:
        live_metadata = get_live_system_context()
        p_info = load_dynamic_personality()
        
        clean_user = user_text.lower().strip().strip('?').strip('.').strip('!')
        web_findings = ""
        
        # --- CODESIGHT SELF-INSPECTION INTERCEPT SCANNER ---
        if any(w in clean_user for w in ["your code", "source code", "view your script", "how you work", "brain_engine", "linux_tools", "memory_manager", "file", "read", "inside"]):
            try:
                target_file = "brain_engine.py"
                if any(x in clean_user for x in ["tools", "linux"]):
                    target_file = "linux_tools.py"
                elif any(x in clean_user for x in ["memory", "db", "manager"]):
                    target_file = "memory_manager.py"
                elif "personality" in clean_user or "text" in clean_user:
                    target_file = f"profiles/{p_info['NAME']}/personality.txt"
                    
                code_text = linux_tools.read_companion_source_file(target_file)
                web_findings = f"\n\n[ Live Script Reference Context ]\n{code_text}"
            except Exception:
                pass

        # Pull long-term user profile facts from database
        immune_profile = memory_manager.compile_known_user_profile()
        
        # Load history rows
        db_messages = memory_manager.load_memory_context(limit=6)
        history_string = ""
        last_human_msg = ""
        for msg in db_messages:
            speaker = "Human" if msg.type == "human" else p_info['NAME']
            history_string += f"{speaker}: {msg.content}\n"
            if msg.type == "human":
                last_human_msg = msg.content
            
        # Compile absolute payload block
        master_prompt = f"""{compile_soul_prompt()}

[ Persistent Human User Profile Data ]
{immune_profile}

[ Live System Reality Data ]
{live_metadata}{web_findings}

[ Recent Conversation Logs ]
{history_string}
Human: {user_text}
{p_info['NAME']}:"""

        # --- REASONING PASS 1: Generate initial response payload ---
        response = self.llm.invoke([HumanMessage(content=master_prompt)])
        raw_output = response.content.strip()
        
        # --- REASONING PASS 2: Multi-turn web search intercept loop ---
        search_query = None
        clean_last = last_human_msg.lower().strip()
        clean_ai = raw_output.lower().strip()
        
        triggers = ["weather", "temp", "temperature", "forecast", "news", "headline", "outside", "hot", "cold", "cnn", "article", "space", "directory", "folder", "list files", "files inside"]
        link_requests = ["link", "url", "website", "links", "source", "specifics"]
        
        # Check if they are initiating a brand-new search query topic
        if "[SEARCH:" in raw_output:
            try:
                search_query = raw_output.split("[SEARCH:")[1].split("]")[0].strip()
            except Exception:
                pass
        elif not web_findings and any(t in clean_user or t in clean_ai for t in triggers + link_requests):
            raw_combined = f"{last_human_msg} {user_text}".lower()
            fillers = ["what about", "can you tell me", "right now", "please", "whats the", "is the", "outside", "tell me", "the", "give me specifics for", "specifics for"]
            for f in fillers:
                raw_combined = raw_combined.replace(f, "")
            search_query = " ".join(raw_combined.split()).strip()

        # If a search query is active, scrape the web and refresh the background cache context
        if search_query:
            try:
                self.active_web_cache = linux_tools.execute_web_search(search_query)
            except Exception:
                pass

        # --- FIXED REASONING PASS 3: Stateful Tool and Action Re-invocation Pass ---
        action_tag = None
        action_report = ""
        
        # Identify if she explicitly outputs an action tag or falls back to an informational request
        if "[ACTION:OPEN_TERMINAL]" in raw_output:
            action_tag = "OPEN_TERMINAL"
        elif "[ACTION:SYSTEM_STATS]" in raw_output or any(w in clean_user for w in ["stats", "specs", "load"]):
            action_tag = "SYSTEM_STATS"
        elif "[ACTION:LIST_DIRECTORY]" in raw_output or any(w in clean_user for w in ["directory", "folder", "list files"]):
            action_tag = "LIST_DIRECTORY"
        elif "[ACTION:CLEAN_DOWNLOADS]" in raw_output or "[ACTION:CLEAR_DOWNLOADS]" in raw_output:
            action_tag = "CLEAN_DOWNLOADS"

        # If an informative action needs to run, intercept it and build a 2nd pass response right away
        if action_tag and action_tag in ["SYSTEM_STATS", "LIST_DIRECTORY"]:
            try:
                action_report = linux_tools.execute_linux_tool(action_tag)
                
                # Force her to read the real hardware/directory statistics before completing her sentence
                action_prompt = master_prompt + f"""
                
System Intercept -> Live Native Action Tool Context:
{action_report}

Directive: Rely strictly on the tool output context above to complete your exact conversational line factually. 
Voice Rule: Speak like a human roommate using your lowercase informal speech style and emotional cues. Do not guess, make up placeholders, or print raw system array logs.
"""
                response = self.llm.invoke([HumanMessage(content=action_prompt)])
                raw_output = response.content.strip()
            except Exception:
                pass
        elif action_tag:
            # Synchronous non-informative system actions (Open terminal, clean files)
            action_report = linux_tools.execute_linux_tool(action_tag)

        # Web Search Cache Re-invocation mapping
        if self.active_web_cache and (search_query or any(l in clean_user for l in link_requests)):
            try:
                link_permission = "Do NOT print raw URLs or link strings in your answer. Just summarize what happened naturally in your own words."
                if any(w in clean_user for w in ["link", "url", "website", "links", "source"]):
                    link_permission = "Provide the explicit source Link URLs matching the stories naturally inside your sentence structures like a helpful friend."

                search_prompt = master_prompt + f"""
                
System Intercept -> Live Web Context Findings:
{self.active_web_cache}

Directive: Rely strictly on the search findings above to answer the human's exact question.
Voice Rule: {link_permission} Speak conversationally using your established lowercase informal speech style and emotional cues. Do not print system log brackets like '[Live Internet News Wire Findings]'.
"""
                response = self.llm.invoke([HumanMessage(content=search_prompt)])
                raw_output = response.content.strip()
            except Exception:
                pass
        else:
            if not any(w in clean_user for w in triggers + link_requests):
                self.active_web_cache = ""

        # --- PROFILE BUILDER ROUTER INTERCEPT (WITH KEY BLACKLIST FILTER GATE) ---
        if "[PROFILE:" in raw_output:
            try:
                prof_data = raw_output.split("[PROFILE:")[1].split("]")[0].strip()
                if "=" in prof_data:
                    k, v = prof_data.split("=", 1)
                    k_clean = k.strip().lower()
                    
                    blacklist = ["weather", "temp", "temperature", "forecast", "news", "headline", "headlines", "cpu", "ram", "memory", "search", "status", "files", "directory"]
                    if not any(b_word in k_clean for b_word in blacklist):
                        memory_manager.store_user_fact(k, v)
            except Exception:
                pass
            
        # Clean output metadata formatting brackets out of final human text view
        clean_reply = raw_output
        clean_reply = re.sub(r'\[ACTION:[^\]]+\]', '', clean_reply)
        clean_reply = re.sub(r'\[PROFILE:[^\]]+\]', '', clean_reply)
        clean_reply = re.sub(r'\[SEARCH:[^\]]+\]', '', clean_reply).strip()
        
        memory_manager.save_message("human", user_text)
        memory_manager.save_message("ai", raw_output)
        
        return {
            "reply": clean_reply,
            "action_executed": action_tag,
            "action_feedback": action_report
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        set_active_profile(sys.argv[1])
        
    brain = SparkBrain()
    p_info = load_dynamic_personality()
    
    print(f"🧠 Loaded Directory Profile: {SELECTED_PROFILE}")
    print(f"{p_info['NAME']} Engine status: ONLINE. Enter text to communicate (type 'exit' to halt).")
    
    try:
        while True:
            try:
                user_msg = input("\nYou: ")
                if user_msg.strip().lower() == "exit":
                    break
                    
                engine_output = brain.process_input(user_msg)
                reply_text = engine_output['reply']
                
                print(f"\n{p_info['NAME']}: {reply_text}")
                linux_tools.send_desktop_notification(p_info['NAME'], reply_text)
                
            except KeyboardInterrupt:
                break
    except Exception as e:
        print(f"🛑 Critical System Interface Loop Crash: {e}")
    finally:
        print("\n🔌 Shutting down communication sockets cleanly... Goodbye!")

