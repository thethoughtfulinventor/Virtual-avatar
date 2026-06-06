"""
cuda_manager.py — CUDA / GPU detection and environment setup.
Simplified + deduplicated version (architecture preserved).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field


# --------------------------------------------------
# Data models
# --------------------------------------------------

@dataclass
class GpuDevice:
    index: int
    name: str
    vram_total_mb: int
    vram_free_mb: int
    utilization_pct: int
    temperature_c: int

    @property
    def vram_used_mb(self) -> int:
        return self.vram_total_mb - self.vram_free_mb

    @property
    def vram_pct(self) -> float:
        return (self.vram_used_mb / self.vram_total_mb * 100) if self.vram_total_mb else 0.0


@dataclass
class CudaStatus:
    available: bool
    driver_version: str | None
    cuda_version: str | None
    devices: list[GpuDevice] = field(default_factory=list)
    ollama_using_gpu: bool = False
    fallback_reason: str | None = None


# --------------------------------------------------
# Manager
# --------------------------------------------------

class CudaManager:
    _SMI_TIMEOUT = 5

    _QUERY_FULL = ",".join([
        "index", "name", "driver_version", "cuda_version",
        "memory.total", "memory.free", "utilization.gpu", "temperature.gpu",
    ])

    _QUERY_REDUCED = ",".join([
        "index", "name", "driver_version",
        "memory.total", "memory.free", "utilization.gpu", "temperature.gpu",
    ])

    _NA = {"N/A", "[N/A]", ""}

    _NO_GPU_EXIT_CODES = {6, 15}

    # ----------------------------
    # lifecycle
    # ----------------------------

    def __init__(self):
        self.status = self._detect()
        self._configure_environment()

    # ----------------------------
    # detection pipeline
    # ----------------------------

    def _detect(self) -> CudaStatus:
        if not shutil.which("nvidia-smi"):
            return self._fail("nvidia-smi not found")

        if not self._list_gpus():
            return self._fail("No NVIDIA GPU detected")

        raw, has_cuda = self._run_query(self._QUERY_FULL)

        if raw is None:
            raw, has_cuda = self._run_query(self._QUERY_REDUCED)

        if raw is None:
            return self._fail("nvidia-smi query failed")

        devices, driver, cuda = self._parse(raw, has_cuda)

        if not devices:
            return self._fail("No parseable GPU data")

        return CudaStatus(
            available=True,
            driver_version=driver,
            cuda_version=cuda or self._detect_cuda_version(),
            devices=devices,
            ollama_using_gpu=self._check_ollama_gpu_usage(),
        )

    # ----------------------------
    # nvidia-smi helpers
    # ----------------------------

    def _list_gpus(self):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "-L"],
                stderr=subprocess.DEVNULL,
                timeout=self._SMI_TIMEOUT,
            ).decode().strip()
            return out.splitlines() or None
        except Exception:
            return None

    def _run_query(self, query: str):
        try:
            out = subprocess.check_output(
                [
                    "nvidia-smi",
                    f"--query-gpu={query}",
                    "--format=csv,noheader,nounits",
                ],
                stderr=subprocess.DEVNULL,
                timeout=self._SMI_TIMEOUT,
            ).decode().strip()

            return (out or None, True)

        except subprocess.CalledProcessError:
            return None, False
        except Exception:
            return None, False

    def _parse(self, raw: str, has_cuda: bool):
        devices = []
        driver = None
        cuda = None

        for line in raw.splitlines():
            p = [x.strip() for x in line.split(",")]

            try:
                if has_cuda and len(p) >= 8:
                    idx, name, drv, cu, total, free, util, temp = p[:8]
                    cuda = cuda or (cu if cu not in self._NA else None)
                elif len(p) >= 7:
                    idx, name, drv, total, free, util, temp = p[:7]
                else:
                    continue

                driver = driver or (drv if drv not in self._NA else None)

                devices.append(GpuDevice(
                    index=int(idx),
                    name=name,
                    vram_total_mb=int(total),
                    vram_free_mb=int(free),
                    utilization_pct=int(util),
                    temperature_c=int(temp),
                ))

            except Exception:
                continue

        return devices, driver, cuda

    # ----------------------------
    # CUDA fallback detection
    # ----------------------------

    def _detect_cuda_version(self):
        try:
            if shutil.which("nvcc"):
                out = subprocess.check_output(
                    ["nvcc", "--version"],
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                ).decode()
                m = re.search(r"release\s+([\d.]+)", out)
                if m:
                    return m.group(1)
        except Exception:
            pass

        try:
            path = "/usr/local/cuda/version.txt"
            if os.path.exists(path):
                return re.search(r"([\d.]+)", open(path).read()).group(1)
        except Exception:
            pass

        return None

    # ----------------------------
    # ollama + environment
    # ----------------------------

    def _check_ollama_gpu_usage(self):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "pmon", "-c", "1", "-s", "m"],
                stderr=subprocess.DEVNULL,
                timeout=self._SMI_TIMEOUT,
            ).decode().lower()

            return "ollama" in out
        except Exception:
            return False

    def _configure_environment(self):
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512")

    # ----------------------------
    # utilities
    # ----------------------------

    def _fail(self, reason: str) -> CudaStatus:
        return CudaStatus(
            available=False,
            driver_version=None,
            cuda_version=None,
            devices=[],
            fallback_reason=reason,
        )

    # ----------------------------
    # public API
    # ----------------------------

    def print_status(self):
        s = self.status

        if not s.available:
            print(f"[CUDA] unavailable: {s.fallback_reason}")
            return

        print(f"[CUDA] Driver {s.driver_version} | CUDA {s.cuda_version}")

        for d in s.devices:
            print(
                f"[CUDA] GPU {d.index} {d.name} "
                f"| VRAM {d.vram_used_mb}/{d.vram_total_mb} MB "
                f"| {d.utilization_pct}% | {d.temperature_c}°C"
            )

        print("[CUDA] Ollama GPU:", "active" if s.ollama_using_gpu else "idle")

    def is_available(self) -> bool:
        return self.status.available

    def primary_device(self):
        return self.status.devices[0] if self.status.devices else None

    def vram_free_mb(self) -> int:
        return sum(d.vram_free_mb for d in self.status.devices)

    def vram_total_mb(self) -> int:
        return sum(d.vram_total_mb for d in self.status.devices)