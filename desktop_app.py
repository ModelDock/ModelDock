"""
ModelDock Studio - Native Windows Desktop Application
Wraps the ultra-lightweight FastAPI engine into a native Windows Desktop GUI window using Microsoft Edge WebView2.
Uses ~35-45 MB RAM total, 0% CPU idle, zero Electron overhead.
"""

import os
import sys

# Ensure UTF-8 output encoding across Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import time
import socket
import threading
from typing import Optional
from pathlib import Path

# Add project root to path
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

# Ensure hardware acceleration environment variables
os.environ.setdefault("LLAMA_ARG_GPU", "auto")
os.environ.setdefault("XOLLAMA_ENGINE", "auto")
os.environ.setdefault("XOLLAMA_ENGINE_FALLBACK", "true")

import uvicorn
import webview
import httpx
from run import app, config_mgr

# Disable opening external browser since we run as native desktop app
config_mgr.set("auto_open_browser", False)

active_server: Optional[uvicorn.Server] = None


def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently free to bind."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 7860, max_tries: int = 50, host: str = "127.0.0.1") -> int:
    """Find the first available free TCP port."""
    for p in range(start_port, start_port + max_tries):
        if is_port_free(p, host):
            return p
    return start_port


def is_modeldock_backend(url: str, timeout: float = 0.8) -> bool:
    """Check if an ModelDock backend is already responding at URL."""
    try:
        r = httpx.get(f"{url}/api/system/status", timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            return "software" in data or "host" in data
    except Exception:
        pass
    return False


def start_server_thread(host: str, port: int):
    """Run FastAPI in a background thread."""
    global active_server
    server_config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
    active_server = uvicorn.Server(server_config)
    active_server.run()


def wait_for_server(url: str, timeout: float = 8.0) -> bool:
    """Wait until local backend is responding."""
    start = time.time()
    while time.time() - start < timeout:
        if is_modeldock_backend(url, timeout=0.5):
            return True
        time.sleep(0.1)
    return False


def on_window_closed():
    """Cleanly terminate backend server and engine when desktop window closes."""
    global active_server
    try:
        from core.engine_manager import NativeEngineManager
        NativeEngineManager.get_instance().stop_server()
    except Exception:
        pass
    if active_server:
        active_server.should_exit = True
    # Terminate process cleanly to prevent lingering background sockets
    os._exit(0)


def main():
    base_port = config_mgr.get("server_port", 7860)
    host = "127.0.0.1"
    default_url = f"http://{host}:{base_port}"
    icon_path = str(CURRENT_DIR / "app.ico")

    # 1. If ModelDock Studio backend is already running on default port, reuse it
    if is_modeldock_backend(default_url):
        url = default_url
    else:
        # 2. Otherwise find an open port (avoids Errno 10048 if port is busy)
        port = find_available_port(start_port=base_port, host=host)
        url = f"http://{host}:{port}"

        server_thread = threading.Thread(
            target=start_server_thread,
            args=(host, port),
            daemon=True,
        )
        server_thread.start()
        wait_for_server(url)

    # 3. Create Native Windows Desktop Window
    window = webview.create_window(
        title="ModelDock Studio",
        url=url,
        width=1240,
        height=820,
        min_size=(1000, 680),
        background_color="#0a0d14",
    )

    # Clean shutdown hook when user closes the window
    window.events.closed += on_window_closed

    # 4. Start Windows native GUI loop (WebView2 runtime)
    webview.start(
        debug=False,
        icon=icon_path if os.path.isfile(icon_path) else None,
        private_mode=False,
    )

    on_window_closed()


if __name__ == "__main__":
    main()
