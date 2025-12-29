#!/usr/bin/env python3
"""
Wrapper script to run Chainlit with correct Python path.
Usage: python run_chainlit.py
"""

import os
import sys
import subprocess

# Get the directory where this script is located
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Set environment variables
env = os.environ.copy()
env['PYTHONPATH'] = PROJECT_ROOT

# Run chainlit with the correct environment
cmd = [
    sys.executable,  # Use the same Python that runs this script
    '-m', 'chainlit',
    'run',
    os.path.join(PROJECT_ROOT, 'chainlit_app.py'),
    '-w',
    '--port', '8000'
]

print(f"Project root: {PROJECT_ROOT}")
print(f"Python: {sys.executable}")
print(f"Running: {' '.join(cmd)}")
print("=" * 50)

os.execve(sys.executable, cmd, env)
