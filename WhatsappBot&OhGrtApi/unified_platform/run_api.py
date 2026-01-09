#!/usr/bin/env python3
"""
Entry point for OhGrt API.

Usage:
    python run_api.py

Or with uvicorn:
    uvicorn ohgrt_api.main:app --host 0.0.0.0 --port 9002 --reload
"""

import sys
from pathlib import Path

# Add the project root to Python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn


def main():
    """Run the OhGrt API server."""
    uvicorn.run(
        "ohgrt_api.main:app",
        host="0.0.0.0",
        port=9002,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
