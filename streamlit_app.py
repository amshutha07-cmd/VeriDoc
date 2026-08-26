from pathlib import Path
import os
import runpy
import sys

backend = Path(__file__).resolve().parent / "backend"
os.chdir(backend)
sys.path.insert(0, str(backend))
runpy.run_path(str(backend / "streamlit_app.py"), run_name="__main__")
