"""
cuda_manager.py — CUDA / GPU detection and environment setup.

Detection uses a two-stage nvidia-smi probe so it works across
the full range of driver versions:

  Stage 1 — Full query including cuda_version (drivers ≥390).
  Stage 2 — Reduced query without cuda_version for older drivers;
             CUDA version sourced from nvcc or filesystem fallbacks.

Exit-code handling is explicit so "no GPU" (codes 6/15) is
distinguished from "bad argument" (code 2) and produces a more
useful message.

The resulting CudaStatus is registered with ServiceManager so
every subsystem can read GPU state without additional subprocesses.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field


# ------------------------------------------------------------------
# Data types
# ------------------------------------------------------------------

@dataclass
class GpuDevice:
    """Snapshot of a single GPU at detection time."""
    index:           int
    name:            str
    vram_total_mb:   int
    vram_free_mb:    int
    utilization_pct: int
    temperature_c:   int

    @property
    def vram_used_mb(self) -> int:
        return self.vram_total_mb - self.vram_free_mb

    @property
    def vram_pct(self) -> float:
        if self.vram_total_mb == 0:
            return 0.0
        return self.vram_used_mb / self.vram_total_mb * 100


@dataclass
class CudaStatus:
    available:        bool
    driver_version:   str | None
    cuda_version:     str | None
    devices:          list[GpuDevice] = field(default_factory=list)
    ollama_using_gpu: bool = False
    fallback_reason:  str | None = None   # set when available=False


# ------------------------------------------------------------------
# Manager
# ------------------------------------------------------------------

class CudaManager:
    """
    Detects NVIDIA CUDA at engine startup.

    Usage
    -----
        cuda = CudaManager()
        cuda.print_status()
        service_manager.register("cuda", cuda)

    Must be created BEFORE Brain/OllamaClient so that
    _configure_environment() sets CUDA_VISIBLE_DEVICES before
    the Ollama HTTP client makes its first connection.
    """

    # Stage 1: full query — requires driver ≥ ~390 for cuda_version
    _QUERY_FULL = ",".join([
        "index", "name", "driver_version", "cuda_version",
        "memory.total", "memory.free", "utilization.gpu", "temperature.gpu",
    ])

    # Stage 2: reduced query — works on all driver versions that
    # support --query-gpu at all (driver ≥ 340 or so)
    _QUERY_REDUCED = ",".join([
        "index", "name", "driver_version",
        "memory.total", "memory.free", "utilization.gpu", "temperature.gpu",
    ])

    # nvidia-smi exit codes that mean "no GPU present" rather than
    # "bad arguments".  Varies by driver version; cover known values.
    _NO_GPU_EXIT_CODES: frozenset[int] = frozenset({6, 15})

    _SMI_TIMEOUT = 5   # seconds

    def __init__(self) -> None:
        self.status: CudaStatus = self._detect()

    # ----------------------------------------------------------
    # Detection pipeline
    # ----------------------------------------------------------

    def _detect(self) -> CudaStatus:
        if not shutil.which("nvidia-smi"):
            return self._unavailable("nvidia-smi not found in PATH")

        # Quick sanity-check: does nvidia-smi see any GPUs at all?
        gpu_list = self._list_gpus()
        if gpu_list is None:
            return self._unavailable("No NVIDIA GPU detected by nvidia-smi")

        # Stage 1 — try the full query with cuda_version
        raw, has_cuda_col = self._run_query(self._QUERY_FULL, cols=8)

        if raw is None:
            # Stage 2 — older driver; cuda_version not supported
            raw, _ = self._run_query(self._QUERY_REDUCED, cols=7)
            has_cuda_col = False

        if raw is None:
            return self._unavailable(
                "nvidia-smi --query-gpu failed on both full and reduced queries"
            )

        devices, driver_version, cuda_version = self._parse(raw, has_cuda_col)

        if not devices:
            return self._unavailable("nvidia-smi returned no parseable device data")

        # If stage 1 didn't give cuda_version, try alternative sources
        if not cuda_version:
            cuda_version = self._detect_cuda_version()

        ollama_gpu = self._check_ollama_gpu_usage()
        self._configure_environment()

        return CudaStatus(
            available=True,
            driver_version=driver_version,
            cuda_version=cuda_version,
            devices=devices,
            ollama_using_gpu=ollama_gpu,
            fallback_reason=None,
        )

    # ----------------------------------------------------------
    # nvidia-smi helpers
    # ----------------------------------------------------------

    def _list_gpus(self) -> list[str] | None:
        """
        Run `nvidia-smi -L` to get a plain list of GPUs.
        This is the most compatible nvidia-smi command and works
        on every driver version that has the tool.

        Returns a list of GPU name strings, or None if no GPUs
        are found or the command fails.
        """
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "-L"],
                stderr=subprocess.DEVNULL,
                timeout=self._SMI_TIMEOUT,
            ).decode().strip()
            lines = [l for l in out.splitlines() if l.strip()]
            return lines if lines else None

        except subprocess.CalledProcessError as e:
            if e.returncode in self._NO_GPU_EXIT_CODES:
                return None   # genuinely no GPU
            # Unexpected exit code — still treat as no GPU but log it
            print(f"[CUDA] nvidia-smi -L exit {e.returncode} — no GPU assumed")
            return None

        except subprocess.TimeoutExpired:
            print("[CUDA] nvidia-smi -L timed out")
            return None

        except Exception:
            return None

    def _run_query(
        self, query: str, cols: int
    ) -> tuple[str | None, bool]:
        """
        Run `nvidia-smi --query-gpu=<query> --format=csv,...`.

        Returns (raw_stdout, True) on success.
        Returns (None, False) on CalledProcessError (e.g. unsupported field)
        or any other failure.

        `cols` is the expected minimum column count and is used only
        to distinguish a bad result from an empty one — parsing happens
        in _parse().
        """
        try:
            raw = subprocess.check_output(
                [
                    "nvidia-smi",
                    f"--query-gpu={query}",
                    "--format=csv,noheader,nounits",
                ],
                stderr=subprocess.DEVNULL,
                timeout=self._SMI_TIMEOUT,
            ).decode().strip()
            return (raw if raw else None), True

        except subprocess.CalledProcessError:
            # Likely an unsupported field in the query string.
            # Caller will retry with a reduced query.
            return None, False

        except subprocess.TimeoutExpired:
            print("[CUDA] nvidia-smi --query-gpu timed out")
            return None, False

        except Exception as e:
            print(f"[CUDA] nvidia-smi --query-gpu unexpected error: {e}")
            return None, False

    def _parse(
        self, raw: str, has_cuda_col: bool
    ) -> tuple[list[GpuDevice], str | None, str | None]:
        """
        Parse multi-GPU CSV output.

        Column order:
          Full (has_cuda_col=True):
            idx, name, driver, cuda, total, free, util, temp
          Reduced (has_cuda_col=False):
            idx, name, driver, total, free, util, temp
        """
        devices: list[GpuDevice] = []
        driver_version: str | None = None
        cuda_version:   str | None = None
        min_cols = 8 if has_cuda_col else 7

        for line in raw.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < min_cols:
                continue

            try:
                if has_cuda_col:
                    idx, name, drv, cuda, total, free, util, temp = parts[:8]
                    cuda_version = cuda_version or (
                        cuda if cuda not in ("N/A", "[N/A]", "") else None
                    )
                else:
                    idx, name, drv, total, free, util, temp = parts[:7]

                driver_version = driver_version or (
                    drv if drv not in ("N/A", "[N/A]", "") else None
                )

                devices.append(GpuDevice(
                    index           = int(idx),
                    name            = name,
                    vram_total_mb   = int(total),
                    vram_free_mb    = int(free),
                    utilization_pct = int(util),
                    temperature_c   = int(temp),
                ))

            except (ValueError, TypeError):
                continue   # skip malformed rows

        return devices, driver_version, cuda_version

    # ----------------------------------------------------------
    # CUDA version — alternative detection
    # ----------------------------------------------------------

    def _detect_cuda_version(self) -> str | None:
        """
        Try to get the CUDA runtime version when nvidia-smi's
        cuda_version field is unavailable (older drivers).

        Tries in order:
          1. nvcc --version  (most reliable when CUDA toolkit installed)
          2. /usr/local/cuda/version.txt
          3. /usr/local/cuda/version.json
        """
        # 1. nvcc
        if shutil.which("nvcc"):
            try:
                out = subprocess.check_output(
                    ["nvcc", "--version"],
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                ).decode()
                m = re.search(r"release\s+([\d.]+)", out, re.IGNORECASE)
                if m:
                    return m.group(1)
            except Exception:
                pass

        # 2. version.txt
        txt_path = "/usr/local/cuda/version.txt"
        if os.path.isfile(txt_path):
            try:
                content = open(txt_path).read()
                m = re.search(r"([\d.]+)", content)
                if m:
                    return m.group(1)
            except Exception:
                pass

        # 3. version.json  (CUDA 11.4+)
        json_path = "/usr/local/cuda/version.json"
        if os.path.isfile(json_path):
            try:
                import json
                data = json.load(open(json_path))
                return data.get("cuda", {}).get("version")
            except Exception:
                pass

        return None

    # ----------------------------------------------------------
    # Ollama GPU check
    # ----------------------------------------------------------

    def _check_ollama_gpu_usage(self) -> bool:
        """
        Check whether Ollama is currently consuming GPU memory
        using nvidia-smi pmon (process monitor).
        Informational only — returns False on any error.
        """
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "pmon", "-c", "1", "-s", "m"],
                stderr=subprocess.DEVNULL,
                timeout=self._SMI_TIMEOUT,
            ).decode()
            return "ollama" in out.lower()
        except Exception:
            return False

    # ----------------------------------------------------------
    # Environment
    # ----------------------------------------------------------

    def _configure_environment(self) -> None:
        """
        Set env vars that help Ollama and CUDA libraries find the GPU.
        Only sets variables that aren't already defined so user
        overrides in the shell are always respected.
        """
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
        os.environ.setdefault(
            "PYTORCH_CUDA_ALLOC_CONF",
            "max_split_size_mb:512",
        )

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    @staticmethod
    def _unavailable(reason: str) -> CudaStatus:
        return CudaStatus(
            available=False,
            driver_version=None,
            cuda_version=None,
            devices=[],
            ollama_using_gpu=False,
            fallback_reason=reason,
        )

    def _check_ollama_gpu_usage(self) -> bool:
        """
        Check whether an Ollama process is currently consuming
        GPU memory using nvidia-smi pmon (process monitor).

        Returns False on any error — this check is informational only.
        """
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "pmon", "-c", "1", "-s", "m"],
                stderr=subprocess.DEVNULL,
                timeout=self._SMI_TIMEOUT,
            ).decode()
            return "ollama" in out.lower()
        except Exception:
            return False

    def _configure_environment(self) -> None:
        """
        Set environment variables that help Ollama and CUDA
        libraries auto-discover the GPU.

        Rules:
        - Only sets variables not already defined (respects user overrides).
        - CUDA_VISIBLE_DEVICES: tells CUDA which GPUs are usable.
        - PYTORCH_CUDA_ALLOC_CONF: reduces fragmentation if torch is used later.
        - Does NOT touch OLLAMA_GPU_LAYERS — Ollama auto-selects based on
          available VRAM and is usually better at this than a static value.
        """
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
        os.environ.setdefault(
            "PYTORCH_CUDA_ALLOC_CONF",
            "max_split_size_mb:512",
        )

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    @staticmethod
    def _unavailable(reason: str) -> CudaStatus:
        return CudaStatus(
            available=False,
            driver_version=None,
            cuda_version=None,
            devices=[],
            ollama_using_gpu=False,
            fallback_reason=reason,
        )

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def print_status(self) -> None:
        """Print a human-readable startup banner to stdout."""
        s = self.status

        if not s.available:
            print(f"[CUDA] Not available — {s.fallback_reason}")
            print("[CUDA] Falling back to CPU inference")
            return

        print(
            f"[CUDA] Driver: {s.driver_version or 'unknown'}"
            f"  |  CUDA: {s.cuda_version or 'unknown'}"
        )

        for dev in s.devices:
            print(
                f"[CUDA] GPU {dev.index}: {dev.name}"
                f"  |  VRAM: {dev.vram_used_mb}/{dev.vram_total_mb} MB"
                f"  |  Util: {dev.utilization_pct}%"
                f"  |  Temp: {dev.temperature_c}°C"
            )

        if s.ollama_using_gpu:
            print("[CUDA] Ollama: actively using GPU ✓")
        else:
            print(
                "[CUDA] Ollama: GPU not yet active "
                "(layers will load on first inference)"
            )

        # Warn if VRAM is already tight before the model loads
        free = self.vram_free_mb()
        from llm.model_config import ModelConfig
        if free < ModelConfig.MIN_VRAM_MB:
            print(
                f"[CUDA] Warning: only {free} MB free VRAM — "
                f"model may partially offload to CPU "
                f"(recommend ≥{ModelConfig.MIN_VRAM_MB} MB free)"
            )

    # --- Convenience accessors ---

    def is_available(self) -> bool:
        """True if at least one CUDA-capable GPU was detected."""
        return self.status.available

    def primary_device(self) -> GpuDevice | None:
        """The first detected GPU, or None."""
        return self.status.devices[0] if self.status.devices else None

    def vram_free_mb(self) -> int:
        """Total free VRAM across all detected devices."""
        return sum(d.vram_free_mb for d in self.status.devices)

    def vram_total_mb(self) -> int:
        """Total VRAM across all detected devices."""
        return sum(d.vram_total_mb for d in self.status.devices)