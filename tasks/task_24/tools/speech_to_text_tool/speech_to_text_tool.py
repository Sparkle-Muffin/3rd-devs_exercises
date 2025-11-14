import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, parent_dir)
from common.file_utils import process_audio_files, extract_text_from_translated_audio_files
from pathlib import Path


def speech_to_text_tool(file_path: str, output_dir: Path):
    mp3_file = Path(file_path)
    process_audio_files(mp3_file, output_dir)
    audio_texts = extract_text_from_translated_audio_files(output_dir)
    return audio_texts