#!/usr/bin/env python3
"""
IMpower150 Computable Submission Platform
Entry Point — launches the Streamlit regulatory dashboard from src/

Usage:
    python run_app.py
    python run_app.py --port 8502
"""
import sys
import os
import subprocess

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    port = "8501"
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = sys.argv[idx + 1]

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join("src", "app.py"),
        "--server.port", port,
        "--server.headless", "true"
    ]
    subprocess.run(cmd)
