#!/usr/bin/env python3
"""
Main entry point for the Agent API.
Run this file to start the FastAPI server.

Usage:
    python main.py
"""

import uvicorn
import sys
import os

# Add the parent directory to Python path so we can import the agent module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

if __name__ == "__main__":
    uvicorn.run(
        "task_22:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
