import requests
import json
from pathlib import Path

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
