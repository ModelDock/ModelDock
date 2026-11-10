"""
ModelDock Studio - System Resource Monitor
Monitors self-process memory and CPU footprint, host RAM, and GPU VRAM with near-zero overhead.
"""

import os
import time
import subprocess
import psutil
from typing import Dict, Any, Optional

_CACHED_GPU_INFO: Optional[Dict[str, Any]] = None
_LAST_GPU_QUERY_TIME: float = 0.0


def get_gpu_metrics() -> Dict[str, Any]:
    """Query NVIDIA GPU metrics via nvidia-smi with a 3-second cache to avoid query overhead."""
    global _CACHED_GPU_INFO, _LAST_GPU_QUERY_TIME
    now = time.time()
    if _CACHED_GPU_INFO is not None and (now - _LAST_GPU_QUERY_TIME) < 3.0:
        return _CACHED_GPU_INFO

    gpu_data = {
        "available": False,
        "name": "N/A",
        "total_vram_mb": 0,
        "used_vram_mb": 0,
        "free_vram_mb": 0,
        "vram_percent": 0.0,
        "gpu_util_percent": 0.0,
        "temperature_c": 0,
    }

    try:
        # Run fast nvidia-smi query
        res = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2.0,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if res.returncode == 0 and res.stdout.strip():
            line = res.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                total_mb = float(parts[1])
                used_mb = float(parts[2])
                free_mb = float(parts[3])
                pct = round((used_mb / total_mb * 100), 1) if total_mb > 0 else 0.0
                gpu_data.update(
                    {
                        "available": True,
                        "name": parts[0],
                        "total_vram_mb": round(total_mb),
                        "used_vram_mb": round(used_mb),
                        "free_vram_mb": round(free_mb),
                        "vram_percent": pct,
                        "gpu_util_percent": float(parts[4]),
                        "temperature_c": int(parts[5]),
                    }
                )
    except Exception:
        # GPU query failed or nvidia-smi not available
        pass

    _CACHED_GPU_INFO = gpu_data
    _LAST_GPU_QUERY_TIME = now
    return gpu_data


def get_full_system_status() -> Dict[str, Any]:
    """
    Returns full telemetry:
    - Software's own RAM (RSS) and CPU footprint
    - System Host RAM and CPU
    - GPU VRAM & Compute
    """
    try:
        current_process = psutil.Process(os.getpid())
        proc_mem_mb = round(current_process.memory_info().rss / (1024 * 1024), 1)
        proc_cpu = round(current_process.cpu_percent(interval=None), 1)
    except Exception:
        proc_mem_mb = 0.0
        proc_cpu = 0.0

    sys_mem = psutil.virtual_memory()
    total_sys_gb = round(sys_mem.total / (1024**3), 2)
    used_sys_gb = round(sys_mem.used / (1024**3), 2)
    free_sys_gb = round(sys_mem.available / (1024**3), 2)
    sys_mem_pct = sys_mem.percent

    sys_cpu_pct = psutil.cpu_percent(interval=None)

    gpu = get_gpu_metrics()

    return {
        "software": {
            "name": "ModelDock Studio",
            "ram_mb": proc_mem_mb,
            "cpu_percent": proc_cpu,
            "status": "Running Ultra-Lean (Zero Bloat)",
        },
        "host": {
            "total_ram_gb": total_sys_gb,
            "used_ram_gb": used_sys_gb,
            "free_ram_gb": free_sys_gb,
            "ram_percent": sys_mem_pct,
            "cpu_percent": sys_cpu_pct,
            "cpu_count": psutil.cpu_count(logical=True),
        },
        "gpu": gpu,
    }
