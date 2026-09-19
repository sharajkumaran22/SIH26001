"""
LAND-SAFE AI — Localhost Launcher
Run with: python run_localhost.py
"""
import webbrowser
import threading
import time
import uvicorn

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 65)
    print("  LAND-SAFE AI: NER Landslide Risk Monitoring & Early Warning System")
    print("  Starting local host server at http://127.0.0.1:8000 ...")
    print("=" * 65)
    
    # Auto-open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Uvicorn ASGI server
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
