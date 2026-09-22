"""
MedGuard - Genuine On-Device Network Call Monitor
Intercepts low-level network calls (sockets, urllib, requests) to verify
that 0 external network calls are made during application execution.
"""
import logging
import socket
import threading
from typing import Optional

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_network_request_count = 0
_monitoring_active = False
_orig_socket_connect = socket.socket.connect


def _monitored_connect(self, address):
    global _network_request_count
    # Allow local loopback IPC (127.0.0.1 or ::1 or localhost) used by Streamlit/WebRTC internally
    host = ""
    if isinstance(address, tuple) and len(address) > 0:
        host = str(address[0])
    elif isinstance(address, str):
        host = address

    is_loopback = host in ("127.0.0.1", "localhost", "::1", "0.0.0.0")

    if not is_loopback:
        with _lock:
            _network_request_count += 1
        logger.warning(f"External network call detected to {address}!")

    return _orig_socket_connect(self, address)


def start_network_monitor() -> None:
    """Installs low-level socket monkeypatch to track external network requests."""
    global _monitoring_active
    with _lock:
        if not _monitoring_active:
            socket.socket.connect = _monitored_connect
            _monitoring_active = True


def get_network_request_count() -> int:
    """Returns the total count of external network requests detected during this session."""
    with _lock:
        return _network_request_count


def reset_network_counter() -> None:
    """Resets the session network request counter to zero."""
    global _network_request_count
    with _lock:
        _network_request_count = 0


# Start network monitoring upon module import
start_network_monitor()
