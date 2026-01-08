#!/usr/bin/env python3
"""
Entry point for WhatsApp Bot.

Usage:
    python run_bot.py

Or with uvicorn:
    uvicorn whatsapp_bot.main:app --host 0.0.0.0 --port 9003 --reload
"""

import sys
from pathlib import Path

# Add the project root to Python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn


def main():
    """Run the WhatsApp Bot server."""
    uvicorn.run(
        "whatsapp_bot.main:app",
        host="0.0.0.0",
        port=9003,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
