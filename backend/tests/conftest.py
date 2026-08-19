"""Pytest configuration for the backend test suite.

Ensures the backend/ directory (which contains the `app` package) is on
sys.path so `from app...` imports resolve when running `pytest` directly
(not just `python -m pytest`, which adds the cwd to sys.path automatically).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
