from typing import List, Dict, Any
import json
import os
import zipfile
import requests
from pathlib import Path
import subprocess
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import shutil
from urllib.parse import urljoin, urlsplit
from os import listdir
import json


def save_txt_file(content: str, file_path: str) -> None:
    """Save content to a text file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    

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
    
    # Check if the file is JSON
    is_json = file_path.suffix.lower() == '.json'
    
    if is_json:
        # Parse and save JSON with proper encoding
        content = response.json()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
    else:
        # Handle other text files
        content_type = response.headers.get('Content-Type', '').lower()
        is_text = 'text' in content_type or file_path.suffix.lower() == '.txt'
        
        if is_text:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
        else:
            with open(file_path, 'wb') as f:
                f.write(response.content)
    
    return str(file_path)


def extract_file(zip_path: Path, password: str | None = None) -> Path:
    extract_dir = os.path.splitext(zip_path)[0]
    os.makedirs(extract_dir, exist_ok=True)
    
    # Convert password to bytes if provided
    pwd_bytes = password.encode() if password else None
    
    with zipfile.ZipFile(zip_path) as zip_ref:
        zip_ref.extractall(
            path=extract_dir,
            pwd=pwd_bytes
        )
    
    extract_dir = Path(extract_dir)
    return extract_dir


def copy_files_to_directory(files: List[Path], import_dir: Path) -> None:
    """Copy files to a directory.
    
    Args:
        files: List of paths to files
        import_dir: Path to a directory
    """
    try:
        import_dir.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            destination = import_dir / file.name
            try:
                shutil.copy2(file, destination)
            except PermissionError:
                print(f"Permission denied: Unable to copy {file} to {destination}")
                print("Please ensure you have write permissions to the destination directory")
                raise
            except Exception as e:
                print(f"Error copying {file} to {destination}: {e}")
                raise
    except PermissionError:
        print(f"Permission denied: Unable to create directory {import_dir}")
        print("Please ensure you have write permissions to create the directory")
        raise


def download_website_source(url: str, save_path: str) -> None:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f"Website source code saved to {save_path}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")


def process_audio_files(audio_files: List[str], output_dir: str) -> None:
    """Process audio files using Whisper."""
    os.makedirs(output_dir, exist_ok=True)
    
    for input_file in audio_files:
        output_file = Path(output_dir) / f"{Path(input_file).stem}.json"
        command = (
            f"insanely-fast-whisper "
            f"--device-id 0 "
            f"--transcript-path {output_file} "
            f"--file-name {input_file}"
        )
        
        try:
            subprocess.run(command, shell=True, check=True, text=True)
            print(f"Successfully processed {input_file}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to process {input_file}: {e}")


def extract_text_from_translated_audio_files(audio_dir: str) -> Dict[str, str]:
    result = {}
     
    # Add audio transcriptions
    for path in Path(audio_dir).glob("*.json"):
        audio_content = read_json(path)
        result[f"{path.stem}.mp3"] = audio_content["text"]

    print(result)
    return result


def download_files_from_website(url, file_tag_str, save_directory, rename_files=False):
    # Ensure the save directory exists
    os.makedirs(save_directory, exist_ok=True)
    
    try:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch the website: {e}")
        return 0
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all file tags
    if file_tag_str == "audio":
        # Find all audio elements and their source tags
        file_tags = []
        audio_elements = soup.find_all('audio')
        for audio in audio_elements:
            # Check for source tags within audio
            source_tags = audio.find_all('source')
            file_tags.extend(source_tags)
    else:
        file_tags = soup.find_all(file_tag_str)
    
    print(f"Found {len(file_tags)} files.")
    
    # Download each file
    file_count = 0
    for file_tag in file_tags:
        # Get the file URL
        file_url = file_tag.get('src')
        if not file_url:
            continue
        
        # Resolve relative URLs
        full_url = urljoin(url, file_url)
        
        try:
            # Fetch the file
            file_response = requests.get(full_url, stream=True)
            file_response.raise_for_status()
            
            if rename_files == False:
                file_url = Path(file_url).name
                filename = os.path.join(save_directory, file_url)   
            else:
                # Name files in order of their appearance in the document
                suffix = Path(file_url).suffix
                filename = file_tag_str + "_" + str(file_count + 1) + str(suffix)
                filename = os.path.join(save_directory, filename) 

            
            # Save the file
            with open(filename, 'wb') as f:
                for chunk in file_response.iter_content(1024):
                    f.write(chunk)
            
            print(f"Downloaded: {filename}")
            file_count += 1
        except requests.RequestException as e:
            print(f"Failed to download {full_url}: {e}")
    
    print(f"Successfully downloaded {file_count} files.")
    return file_count


def combine_json_files(file_1_content, file_2_content, output_file):
    """
    Combines two JSON file contents into a single JSON file with a flexible structure.

    :param file_1_content: JSON content from the first file as a string or dictionary.
    :param file_2_content: JSON content from the second file as a string or dictionary.
    :param output_file: Path to save the combined JSON file.
    """
    # Load JSON data from the inputs
    if isinstance(file_1_content, str):
        data1 = json.loads(file_1_content)
    else:
        data1 = file_1_content

    if isinstance(file_2_content, str):
        data2 = json.loads(file_2_content)
    else:
        data2 = file_2_content

    # Ensure both inputs are dictionaries
    if not isinstance(data1, dict) or not isinstance(data2, dict):
        raise ValueError("Both input files must be JSON objects (dictionaries).")

    # Combine the data flexibly
    combined_data = {}

    # Combine keys that exist in both inputs
    for key in set(data1.keys()).union(data2.keys()):
        if key in data1 and key in data2:
            # If both keys have lists as values, combine element-wise
            if isinstance(data1[key], list) and isinstance(data2[key], list):
                if len(data1[key]) != len(data2[key]):
                    raise ValueError(f"The lists under the key '{key}' must have the same length.")
                combined_data[key] = [{**elem1, **elem2} for elem1, elem2 in zip(data1[key], data2[key])]
            else:
                # If the values are not lists, create a tuple of both values
                combined_data[key] = (data1[key], data2[key])
        elif key in data1:
            combined_data[key] = data1[key]
        elif key in data2:
            combined_data[key] = data2[key]

    # Write the combined data to the output file
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=4)

    print(f"Combined JSON has been saved to {output_file}")
    return combined_data


def get_file_paths_from_dir(dir_path):
    return [dir_path / file for file in listdir(dir_path)]


def get_url_path_without_filename(url):
    split_url = urlsplit(url)  # Split the URL into components
    base_url = urljoin(url, split_url.path.rsplit('/', 1)[0] + '/')  # Reconstruct URL without the filename
    return base_url


def send_json(url: str, json_input) -> dict:
    """
    Send JSON data to a URL and return the response.
    
    Args:
        url: The URL to send the request to
        json_input: Either a Path object pointing to a JSON file, or a dict/JSON-serializable object
    """
    # Handle input that's either a file path or direct JSON data
    if isinstance(json_input, (str, Path)):
        with open(json_input) as f:
            data = json.load(f)
    else:
        data = json_input

    response = requests.post(url, json=data)
    return response.json()