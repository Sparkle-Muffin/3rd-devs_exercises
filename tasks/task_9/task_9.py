import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import read_file_content, save_json, read_json, download_file, extract_file, process_audio_files
from tasks.common.openai_utils import call_openai

from os import getenv
from dotenv import load_dotenv
import json
from openai import OpenAI
from typing import List, Dict, Any
from pathlib import Path


def process_files(extract_path: str) -> tuple[List[str], List[str], List[str]]:
    """Find all files of specific types in directory."""
    def find_files(path: str, extension: str) -> List[str]:
        files = []
        for root, _, filenames in os.walk(path):
            files.extend([
                os.path.join(root, f) for f in filenames 
                if f.endswith(extension)
            ])
            break
        return files

    return (
        find_files(extract_path, ".txt"),
        find_files(extract_path, ".mp3"),
        find_files(extract_path, ".png")
    )


def merge_files(txt_files: List[str], png_files: List[str], audio_dir: str, images_json: str) -> Dict:
    """Merge content from all file types into single dictionary."""
    result = {}
    
    # Add text files
    for path in txt_files:
        result[Path(path).name] = read_file_content(path)
    
    # Add audio transcriptions
    for path in Path(audio_dir).glob("*.json"):
        audio_content = read_json(path)
        result[f"{path.stem}.mp3"] = audio_content["text"]

    # Add image descriptions
    image_content = read_json(images_json)
    for i, (_, value) in enumerate(image_content.items()):
        file_name = Path(png_files[i]).name
        file_content = value
        result.update({file_name: file_content})
    
    return result


def main():
    # Initialize
    load_dotenv()
    client = OpenAI()
    
    # Download and extract files
    zip_path = download_file(getenv("TASK_9_DOWNLOAD_URL"), Path(__file__).parent)
    extract_path = extract_file(zip_path)
    
    # Process files
    txt_files, mp3_files, png_files = process_files(extract_path)
    
    # Process audio files
    audio_output_dir = Path(__file__).parent / "translated_mp3_files"
    process_audio_files(mp3_files, audio_output_dir)
    
    # Process images
    prompt_dir = Path(__file__).parent / "images_to_text_prompt.txt"
    images_prompt = read_file_content(prompt_dir)
    images_response = call_openai(
        client,
        images_prompt,
        images=png_files,
        response_format={"type": "json_object"}
    )
    GPT_images_to_text = Path(__file__).parent / "GPT_images_to_text.json"
    save_json(json.loads(images_response), GPT_images_to_text)
    
    # Merge all files
    merged_content = merge_files(txt_files, png_files, audio_output_dir, GPT_images_to_text)
    all_files_merged = Path(__file__).parent / "all_files_merged.json"
    save_json(merged_content, all_files_merged)
    
    # Classify files
    prompt_dir = Path(__file__).parent / "files_classification_prompt.txt"
    classification_prompt = read_file_content(prompt_dir)
    files_content = read_file_content(all_files_merged)
    classification_response = call_openai(
        client,
        f"{classification_prompt}\n\n{files_content}",
        response_format={"type": "json_object"}
    )
    GPT_files_classification_path = Path(__file__).parent / "GPT_files_classification.json"
    save_json(json.loads(classification_response), GPT_files_classification_path)
    
    # Create and send submission
    submission = {
        "task": getenv("TASK_9_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": json.loads(classification_response)
    }
    submission_file = Path(__file__).parent / "submission_file.json"
    save_json(submission, submission_file)
    send_json(getenv("TASK_9_SUBMISSION_URL"), submission_file)


if __name__ == "__main__":
    main()