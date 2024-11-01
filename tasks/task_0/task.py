import requests
import json
from dotenv import load_dotenv
import sys
import os
# Add the parent directory to the system path (otherwise the send_json.py can't be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from send_json import send_json


# Load environment variables from the .env file
load_dotenv()


def download_and_save_json(url, json_file_path, api_key):
    """Download data from a URL, save it as JSON with an array of strings."""
    try:
        # Step 1: Download data from URL
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors

        # Step 2: Parse data (assuming each line is a string you want in the array)
        strings = response.text.strip().splitlines()

        # Step 3: Save as JSON file
        with open(json_file_path, "w") as json_file:
            # a Python object (dict):
            json_content = {"task": "POLIGON", 
                            "apikey": api_key, 
                            "answer": strings}
            # convert into JSON:
            json.dump(json_content, json_file)
        print(f"Data saved to {json_file_path}")

    except requests.RequestException as e:
        print(f"Error downloading data: {e}")


def main():
    # URL of the data file
    download_url = "https://poligon.aidevs.pl/dane.txt"
    # submission URL
    submission_url = "https://poligon.aidevs.pl/verify"
    # Path to the JSON file where we'll save the strings
    json_file_path = "tasks/task_0/result.json"

    # Load API key from environment variables
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("API key is missing. Please set it in the .env file.")
        return
    
    # Download and save the JSON file
    download_and_save_json(download_url, json_file_path, api_key)

    # Send the JSON file to the course creator's URL
    send_json(submission_url, json_file_path)


if __name__ == "__main__":
    main()
