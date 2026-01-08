"""
System monitoring utilities for GGUF Forge.
Provides real-time CPU, memory, and disk I/O metrics.
"""

import shutil
import subprocess
import time
import psutil
from typing import Dict, Any, Optional, Tuple

_io_counters_cache: Optional[Tuple[float, Dict[str, int]]] = None
_net_io_counters_cache: Optional[Tuple[float, Dict[str, int]]] = None
_default_interface: Optional[str] = None
_last_update_time: float = 0


def get_system_metrics(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get current system metrics.

    Args:
        path: Optional path for disk space monitoring (defaults to CACHE_DIR)

    Returns:
        Dict with: cpu_percent, memory_percent, disk_free_gb, disk_read_mbps, disk_write_mbps,
                   net_rx_mbps, net_tx_mbps
    """
    global _io_counters_cache, _net_io_counters_cache, _last_update_time

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

    net_rx_mbps = 0.0
    net_tx_mbps = 0.0

    net_interface = _get_default_network_interface()
    if net_interface:
        net_io = psutil.net_io_counters(pernic=True)
        if net_io and net_interface in net_io:
            net_counters = net_io[net_interface]
            if _net_io_counters_cache is not None:
                prev_time, prev_counters = _net_io_counters_cache
                time_delta = current_time - prev_time

                if time_delta > 0:
                    rx_bytes = net_counters.bytes_recv - prev_counters["bytes_recv"]
                    tx_bytes = net_counters.bytes_sent - prev_counters["bytes_sent"]
                    net_rx_mbps = round((rx_bytes / (1024**2)) / time_delta, 1)
                    net_tx_mbps = round((tx_bytes / (1024**2)) / time_delta, 1)

            _net_io_counters_cache = (
                current_time,
                {
                    "bytes_recv": net_counters.bytes_recv,
                    "bytes_sent": net_counters.bytes_sent,
                },
            )

    _last_update_time = current_time

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_free_gb": disk_free_gb,
        "disk_read_mbps": disk_read_mbps,
        "disk_write_mbps": disk_write_mbps,
        "net_rx_mbps": net_rx_mbps,
        "net_tx_mbps": net_tx_mbps,
    }


def _get_default_network_interface() -> Optional[str]:
    """
    Get the network interface used for the default gateway.

    Uses 'ip route get 8.8.8.8' to determine the interface that routes
    to the default gateway (outbound traffic).

    Returns:
        Network interface name (e.g., 'eth0', 'wlan0') or None if not found
    """
    global _default_interface

    if _default_interface is not None:
        return _default_interface

    try:
        result = subprocess.run(
            ["ip", "route", "get", "8.8.8.8"], capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            for part in output.split():
                if part.startswith("dev"):
                    _default_interface = part.split()[1]
                    return _default_interface
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
        pass

    return None


def reset_io_cache():
    """Reset the I/O counters cache. Call this when starting fresh measurements."""
    global _io_counters_cache, _net_io_counters_cache, _last_update_time
    _io_counters_cache = None
    _net_io_counters_cache = None
    _last_update_time = 0
