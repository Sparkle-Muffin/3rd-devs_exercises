import requests
from os import getenv
from dotenv import load_dotenv
import json
import os
import sys

# Add the parent directory to the system path (otherwise the send_json.py can't be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tasks.common.send_json import send_json

load_dotenv()

ai_devs_3_api_key = getenv("AI_DEVS_3_API_KEY")
download_url = getenv("TASK_5_DOWNLOAD_URL")
task_name = getenv("TASK_5_TASK_NAME")
submission_url = getenv("TASK_5_SUBMISSION_URL")


def download_and_save_file(url, uncensored_file_path):
    """Download data from a URL, save it as JSON with an array of strings."""
    try:
        # Step 1: Download data from URL
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors

        # Step 2: Save as text file
        with open(uncensored_file_path, "w") as text_file:
            text_file.write(response.text)

        print(f"Data saved to {uncensored_file_path}")

    except requests.RequestException as e:
        print(f"Error downloading data: {e}")


def call_llama(prompt: str):
    url = "http://localhost:11434/api/generate"
# 
    payload = {
        "model": "llama3.1:8b",
        "stream": False,
        "format": "json",
        "system": "respond in this format: {\"result\": \"...\"}",
        "prompt": prompt
    }

    response = requests.post(url, json=payload)
    response_data = response.json()

    # Extract the actual answer content
    answer_content = response_data["response"].split("\"result\": \"")[1].split("\"")[0]
    print(answer_content)
    
    with open("tasks/task_5/censored.txt", "w") as text_file:
        text_file.write(answer_content)
    
    # Create directory if it doesn't exist
    os.makedirs("tasks/task_5", exist_ok=True)

    # Save response to a numbered JSON file
    filename = f"tasks/task_5/LLAMA_response.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)


def create_submission_file():
    # Read the content of calibration_final_version.json
    with open("tasks/task_5/censored.txt", "r") as file:
        censored_data = file.read()
    
    # Create the submission structure
    submission_data = {
        "task": task_name,
        "apikey": ai_devs_3_api_key,
        "answer": censored_data
    }
    
    # Save the submission data to a new file
    with open("tasks/task_5/submission_file.json", "w") as file:
        json.dump(submission_data, file, indent=4)


def main():
    # Path to the JSON file where we'll save the strings
    uncensored_file_path = "tasks/task_5/uncensored.txt"
    # Download and save the JSON file
    download_and_save_file(download_url, uncensored_file_path)

    # Get the prompt instructions from the prompt.txt file
    with open('tasks/task_5/prompt.txt', 'r') as file:
        prompt_instructions = file.read()
    # Get the uncensored data from the uncensored.txt file
    with open('tasks/task_5/uncensored.txt', 'r') as file:
        uncensored_data = file.read()  
    # Combine the prompt instructions and the uncensored data
    prompt = prompt_instructions + "\n\n" + uncensored_data
    
    call_llama(prompt)

    # Create the submission file
    create_submission_file()

    # Path to the submission JSON file
    json_file_path = "tasks/task_5/submission_file.json"
    # Send the final version file to the submission URL
    send_json(submission_url, json_file_path)
    

if __name__ == "__main__":
    main()