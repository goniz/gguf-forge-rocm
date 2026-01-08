"""
System monitoring utilities for GGUF Forge.
Provides real-time CPU, memory, and disk I/O metrics.
"""

import shutil
import time
import psutil
from typing import Dict, Any, Optional, Tuple

_io_counters_cache: Optional[Tuple[float, Dict[str, int]]] = None
_last_update_time: float = 0


def get_system_metrics(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get current system metrics.

    Args:
        path: Optional path for disk space monitoring (defaults to CACHE_DIR)

    Returns:
        Dict with: cpu_percent, memory_percent, disk_free_gb, disk_read_mbps, disk_write_mbps
    """
    global _io_counters_cache, _last_update_time

    cpu_percent = psutil.cpu_percent(interval=0.1)

    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    if path:
        disk_usage = shutil.disk_usage(path)
        disk_free_gb = round(disk_usage.free / (1024**3), 1)
    else:
        disk_free_gb = 0.0

    current_time = time.time()
    counters = psutil.disk_io_counters()

    if counters is not None and _io_counters_cache is not None:
        prev_time, prev_counters = _io_counters_cache
        time_delta = current_time - prev_time

        if time_delta > 0:
            read_bytes = counters.read_bytes - prev_counters["read_bytes"]
            write_bytes = counters.write_bytes - prev_counters["write_bytes"]
            disk_read_mbps = round((read_bytes / (1024**2)) / time_delta, 1)
            disk_write_mbps = round((write_bytes / (1024**2)) / time_delta, 1)
        else:
            disk_read_mbps = 0.0
            disk_write_mbps = 0.0
    else:
        disk_read_mbps = 0.0
        disk_write_mbps = 0.0

    if counters is not None:
        _io_counters_cache = (
            current_time,
            {"read_bytes": counters.read_bytes, "write_bytes": counters.write_bytes},
        )
    _last_update_time = current_time

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_free_gb": disk_free_gb,
        "disk_read_mbps": disk_read_mbps,
        "disk_write_mbps": disk_write_mbps,
    }


def reset_io_cache():
    """Reset the I/O counters cache. Call this when starting fresh measurements."""
    global _io_counters_cache, _last_update_time
    _io_counters_cache = None
    _last_update_time = 0
