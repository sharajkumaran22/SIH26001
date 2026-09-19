"""
LAND-SAFE AI — Native Desktop Application Launcher
Runs the FastAPI decision-support server in a background thread and opens
a standalone native desktop window (no browser tabs, no URL bar).
"""

import os
import sys
import time
import threading
import subprocess
import urllib.request
import uvicorn

# Set project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from backend.main import app


def run_server():
    """Start Uvicorn ASGI server in background thread."""
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="warning"
    )
    server = uvicorn.Server(config)
    server.run()


def wait_for_server(timeout=10):
    """Wait until FastAPI is responsive."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def launch_edge_app_mode():
    """Fallback: launch native standalone app window via Windows Edge/Chrome app mode."""
    url = "http://127.0.0.1:8000"
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    ]
    for exe in edge_paths:
        if os.path.exists(exe):
            print(f"Launching standalone desktop window using {os.path.basename(exe)}...")
            subprocess.run([exe, f"--app={url}", "--window-size=1440,920"])
            return True
    
    # Generic browser fallback
    import webbrowser
    webbrowser.open(url)
    return True


def main():
    print("=====================================================================")
    print(" LAND-SAFE AI: Launching Desktop Application")
    print(" AI-Based Early Warning & Landslide Risk Monitoring System (NER)")
    print("=====================================================================")

    # 1. Start backend server in daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("Starting background telemetry engine...")
    if not wait_for_server():
        print("[ERROR] Server failed to initialize within timeout.")
        sys.exit(1)

    print("Backend ready. Initializing native application window...")

    # 2. Try pywebview for true native window
    try:
        import webview
        window = webview.create_window(
            title="LAND-SAFE AI — Early Warning & Landslide Risk Monitoring System",
            url="http://127.0.0.1:8000",
            width=1440,
            height=920,
            min_size=(1024, 700),
            resizable=True,
            confirm_close=False,
            text_select=True
        )
        webview.start()
        print("Application window closed.")
    except Exception as e:
        print(f"Native webview fallback triggered: {e}")
        launch_edge_app_mode()


if __name__ == "__main__":
    main()
