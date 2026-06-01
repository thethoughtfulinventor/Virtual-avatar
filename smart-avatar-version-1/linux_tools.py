# linux_tools.py
import subprocess
import os
from datetime import datetime
from ddgs import DDGS

def send_desktop_notification(title: str, text: str):
    """Triggers a native Linux desktop notification using notify-send."""
    try:
        subprocess.Popen([
            "notify-send", 
            "-a", title, 
            "-i", "dialog-information", 
            title, 
            text
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Notification error: {e}")

def get_live_system_context() -> str:
    """Queries absolute physical hardware specs and storage usage metrics from the system bus."""
    now = datetime.now()
    friendly_time = now.strftime("%I:%M %p")
    m_d_y = now.strftime("%B %d, %Y")
    weekday = now.strftime("%A")
    
    cpu_name = "Generic Linux CPU"
    gpu_name = "NVIDIA Graphics Card"
    total_ram = "16 GB"
    storage_total = "Unknown"
    storage_used = "Unknown"
    storage_free = "Unknown"
    storage_percent = "0%"
    
    try:
        # 1. Pull the exact marketing name string from your CPU architecture bus
        cpu_name = subprocess.check_output("lscpu | grep 'Model name' | cut -d: -f2", shell=True).decode().strip()
        cpu_name = " ".join(cpu_name.split())
        
        # 2. Pull the exact marketing name string from your NVIDIA driver stack
        gpu_name = subprocess.check_output("nvidia-smi --query-gpu=name --format=csv,noheader", shell=True).decode().strip()
        
        # 3. Pull total physical RAM capacity
        total_ram = subprocess.check_output("free -h | awk 'NR==2{print $2}'", shell=True).decode().strip()
        
        # 4. Gather absolute Storage Usage Data across all active partitions
        df_line = subprocess.check_output("df -h --total | grep 'total'", shell=True).decode().strip().split()
        if len(df_line) >= 5:
            storage_total = df_line[1]    
            storage_used = df_line[2]     
            storage_free = df_line[3]     
            storage_percent = df_line[4]  
    except Exception:
        pass
        
    return (
        f"Live System Clock: {friendly_time}\n"
        f"Live System Date: {m_d_y}\n"
        f"Live System Weekday: {weekday}\n"
        f"Physical Hardware Build Metrics -> "
        f"CPU Model: {cpu_name} | "
        f"GPU Model: {gpu_name} | "
        f"Total Installed RAM: {total_ram}\n"
        f"Real-Time Hard Drive Storage Metrics -> "
        f"Total Drive Capacity: {storage_total} | "
        f"Space Active Used: {storage_used} | "
        f"Space Remaining Free: {storage_free} | "
        f"Total Storage Percent Utilization: {storage_percent}"
    )

def execute_web_search(query: str) -> str:
    """Scrapes DuckDuckGo search indexes and live wire news metrics natively without warnings."""
    clean_query = query.lower().strip()
    
    try:
        with DDGS() as ddgs:
            # 1. Target live daily news feeds if media parameters are requested
            if any(n in clean_query for n in ["news", "headline", "headlines", "story", "cnn", "articles"]):
                search_term = clean_query.replace("tell me what", "").replace("is there", "").strip()
                news_results = list(ddgs.news(search_term, max_results=3))
                
                if news_results:
                    context = "\n[ Live Internet News Wire Findings - READ THESE ACCURATE CURRENT STORIES ]\n"
                    for n in news_results:
                        context += f"Headline: {n.get('title', '')}\nSummary: {n.get('body', '')}\nLink URL: {n.get('url', '')}\n\n"
                    return context

            # 2. Inject search engine operators if weather statistics are called
            if any(w in clean_query for w in ["weather", "temp", "temperature", "forecast"]):
                clean_query = f"current hourly weather forecast temperature conditions today {clean_query}"
                
            # 3. Standard Fallback text index scraper
            results = list(ddgs.text(clean_query, max_results=3))
            if not results:
                return "Web Search executed but yielded zero matching data nodes."
                
            context = "\n[ Live Internet Search Results Context ]\n"
            for r in results:
                context += f"Title: {r.get('title', '')}\nSnippet: {r.get('body', '')}\n\n"
            return context
        
    except Exception as e:
        return f"Web Search subsystem network timeout error: {str(e)}"

def read_companion_source_file(filename: str) -> str:
    """Reads project python code or configuration text scripts safely to provide codebase visibility to the AI."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.normpath(os.path.join(base_dir, filename.strip()))
    
    # Secure Sandbox Constraint: Blocks traversal injections outside of the smart-avatar project tree folder
    if not target_path.startswith(base_dir):
        return "Access Denied: Path traversal security lock blocked operations outside of smart-avatar work directories."
        
    try:
        if os.path.exists(target_path):
            with open(target_path, "r") as f:
                return f"\n[ Source Code Codebase Context: {filename} ]\n" + f.read()
        return f"File Error: The file script path '{filename}' could not be resolved or located on disk."
    except Exception as e:
        return f"File system read operation failed: {str(e)}"

def execute_linux_tool(intent_tag: str) -> str:
    """Runs a shell utility unlinked from the primary python thread state."""
    try:
        if intent_tag == "OPEN_TERMINAL":
            terminal_options = ["konsole"]
            
            for term in terminal_options:
                if os.system(f"which {term} > /dev/null 2>&1") == 0:
                    subprocess.Popen(
                        ["dbus-run-session", "--", term], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        close_fds=True,
                        start_new_session=True
                    )
                    return f"System Action Success: Forced Wayland window draw for '{term}'."
                    
            # Fallback console string if Konsole binary path target slips
            subprocess.Popen(["bash", "-c", "ptyxis || alacritty || kgx"], close_fds=True, start_new_session=True)
            return "System Action Success: Attempted fallback thread sequence."
            
        elif intent_tag == "SYSTEM_STATS":
            cpu = subprocess.check_output("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", shell=True).decode().strip()
            mem = subprocess.check_output("free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2 }'", shell=True).decode().strip()
            
            gpu_core = "0%"
            gpu_vram = "0%"
            try:
                gpu_core = subprocess.check_output("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits", shell=True).decode().strip() + "%"
                vram_used = subprocess.check_output("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True).decode().strip()
                vram_total = subprocess.check_output("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits", shell=True).decode().strip()
                gpu_vram = f"{vram_used}MB / {vram_total}MB"
            except Exception:
                gpu_core = "Driver Unlinked"
                gpu_vram = "Offline"
                
            return f"System Stats -> CPU Load: {cpu}%, RAM Usage: {mem}, GPU Load: {gpu_core}, VRAM Usage: {gpu_vram}"
            
        # Real-world storage/directory path auditor utility macro mapping
        elif intent_tag == "LIST_DIRECTORY":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            files = os.listdir(base_dir)
            data_files = os.listdir(data_dir) if os.path.exists(data_dir) else []
            return f"Project Root Files: {files} | Data Directory Files: {data_files}"

        elif intent_tag == "CLEAN_DOWNLOADS":
            os.system("find ~/Downloads -type f -empty -delete")
            return "Cleaned up completely empty files inside the Downloads directory."
            
    except Exception as e:
        return f"System execution failed: {str(e)}"
    
    return "Unknown instruction tag."

