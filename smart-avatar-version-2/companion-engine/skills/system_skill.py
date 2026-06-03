import subprocess
from datetime import datetime
from tools.base_tool import BaseTool


class SystemStatsTool(BaseTool):
    """
    Returns live system statistics.

    Use when the user asks about CPU, RAM,
    GPU, storage, or system performance.
    """

    name = "system_stats"
    description = (
        "Returns live system stats: CPU, RAM, "
        "GPU, and storage usage. Use when the "
        "user asks about system performance or "
        "hardware. No args required."
    )

    def run(self, args, context):

        lines = [
            f"System snapshot — "
            f"{datetime.now().strftime('%I:%M %p')}"
        ]

        # CPU
        try:
            cpu = subprocess.check_output(
                "top -bn1 | grep 'Cpu(s)' "
                "| awk '{print $2}'",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()
            lines.append(f"CPU: {cpu}%")
        except Exception:
            lines.append("CPU: unavailable")

        # RAM
        try:
            mem = subprocess.check_output(
                "free -h | awk 'NR==2"
                "{printf \"%s / %s\", $3, $2}'",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()
            lines.append(f"RAM: {mem}")
        except Exception:
            lines.append("RAM: unavailable")

        # GPU — silent skip if no NVIDIA driver
        try:
            load = subprocess.check_output(
                "nvidia-smi --query-gpu=utilization.gpu "
                "--format=csv,noheader,nounits",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()

            used = subprocess.check_output(
                "nvidia-smi --query-gpu=memory.used "
                "--format=csv,noheader,nounits",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()

            total = subprocess.check_output(
                "nvidia-smi --query-gpu=memory.total "
                "--format=csv,noheader,nounits",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()

            lines.append(f"GPU: {load}%")
            lines.append(f"VRAM: {used} / {total} MB")

        except Exception:
            pass

        # Storage
        try:
            df = subprocess.check_output(
                "df -h --total | tail -1",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip().split()

            if len(df) >= 5:
                lines.append(
                    f"Storage: {df[2]} / {df[1]} "
                    f"({df[4]}) — {df[3]} free"
                )

        except Exception:
            lines.append("Storage: unavailable")

        return "\n".join(lines)