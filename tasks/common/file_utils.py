from typing import List, Dict, Any
import json
import os
import zipfile
import requests
from pathlib import Path

def read_file_content(file_path: str) -> str:
    """Read and return content of a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def save_json(data: Dict[str, Any], file_path: str) -> None:
    """Save dictionary as JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def read_json(file_path: str) -> Dict[str, Any]:
    """Read JSON file and return dictionary."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def download_file(url: str, save_path: str) -> str:
    """Download file from URL and save it locally."""
    response = requests.get(url)
    response.raise_for_status()
    
    filename = response.headers.get("Content-Disposition", "").split("filename=")[-1].strip('"') or url.split("/")[-1]
    file_path = Path(save_path) / filename
    
    with open(file_path, 'wb') as f:
        f.write(response.content)
    
    return str(file_path) 

def extract_file(zip_path):
    try:
        # Create extraction directory using zip file name without extension
        extract_path = os.path.splitext(zip_path)[0]
        os.makedirs(extract_path, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            
        # Optional: Remove the zip file after extraction
        # os.remove(zip_path)

        return extract_path

    except zipfile.BadZipFile as e:
        print(f"Error extracting zip file: {e}")