import os
import sys

# Put the app root (where `server/` and `app.py` live) on the import path so tests
# and `uvicorn app:app` resolve the same modules.
sys.path.insert(0, os.path.dirname(__file__))
