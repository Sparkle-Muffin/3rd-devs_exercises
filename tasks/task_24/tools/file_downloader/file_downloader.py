import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, parent_dir)
from common.file_utils import download_file
from pathlib import Path


def download_file_tool(file_url: str, downloads_dir: Path):
    return download_file(file_url, downloads_dir)