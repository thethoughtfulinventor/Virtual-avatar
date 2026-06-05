import subprocess
from datetime import datetime
from tools.base_tool import BaseTool


class SystemStatsTool(BaseTool):
    """
    Returns live system statistics.

    GPU/VRAM data is sourced from the CudaManager that was
    registered with ServiceManager at startup, avoiding a
    second nvidia-smi subprocess call on every invocation.

    CPU, RAM, and storage still use subprocess because those
    values change continuously and cannot be cached from startup.
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

        # --- CPU ---
        try:
            cpu = subprocess.check_output(
                "top -bn1 | grep 'Cpu(s)' "
                "| awk '{print $2}'",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode().strip()
            lines.append(f"CPU: {cpu}%")
        except Exception:
            lines.append("CPU: unavailable")

        # --- RAM ---
        try:
            mem = subprocess.check_output(
                "free -h | awk 'NR==2"
                "{printf \"%s / %s\", $3, $2}'",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode().strip()
            lines.append(f"RAM: {mem}")
        except Exception:
            lines.append("RAM: unavailable")

        # --- GPU / VRAM — via CudaManager if available ---
        cuda_manager = context.get("cuda")

        if cuda_manager and cuda_manager.is_available():
            # Re-query live utilisation and memory in a single call
            # rather than reusing the cached startup snapshot, since
            # GPU load changes every second during inference.
            lines += self._live_gpu_stats(cuda_manager)
        else:
            # CudaManager not in context or no GPU — try nvidia-smi
            # directly as a last resort so the tool still works in
            # isolation (e.g. unit tests, manual invocations).
            lines += self._fallback_gpu_stats()

        # --- Storage ---
        try:
            df = subprocess.check_output(
                "df -h --total | tail -1",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode().strip().split()

            if len(df) >= 5:
                lines.append(
                    f"Storage: {df[2]} / {df[1]} "
                    f"({df[4]}) — {df[3]} free"
                )
        except Exception:
            lines.append("Storage: unavailable")

        return "\n".join(lines)

    # ----------------------------------------------------------
    # GPU stat helpers
    # ----------------------------------------------------------

    def _live_gpu_stats(self, cuda_manager) -> list[str]:
        """
        Query live GPU utilisation and memory via a fresh
        nvidia-smi call.  Uses the same CSV format as
        CudaManager so output is consistent.
        """
        try:
            raw = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.used,"
                    "memory.total,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode().strip()

            lines = []
            for line in raw.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 5:
                    continue
                idx, name, used, total, util = parts[:5]
                lines.append(
                    f"GPU {idx} ({name}): "
                    f"{util}% util | "
                    f"VRAM: {used}/{total} MB"
                )
            return lines if lines else ["GPU: data unavailable"]

        except Exception:
            # Fall through to the startup snapshot as a last resort
            result = []
            for dev in cuda_manager.status.devices:
                result.append(
                    f"GPU {dev.index} ({dev.name}): "
                    f"VRAM: {dev.vram_used_mb}/{dev.vram_total_mb} MB "
                    f"(cached snapshot)"
                )
            return result or ["GPU: data unavailable"]

    def _fallback_gpu_stats(self) -> list[str]:
        """
        Called when CudaManager is not available in context.
        Attempts a direct nvidia-smi probe; silently skips on
        systems without an NVIDIA driver.
        """
        try:
            load = subprocess.check_output(
                "nvidia-smi --query-gpu=utilization.gpu "
                "--format=csv,noheader,nounits",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode().strip()

            used = subprocess.check_output(
                "nvidia-smi --query-gpu=memory.used "
                "--format=csv,noheader,nounits",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode().strip()

            total = subprocess.check_output(
                "nvidia-smi --query-gpu=memory.total "
                "--format=csv,noheader,nounits",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode().strip()

            return [
                f"GPU: {load}%",
                f"VRAM: {used} / {total} MB",
            ]

        except Exception:
            return []   # No GPU / no driver — silently omit