import requests
from os import getenv
from dotenv import load_dotenv
import json
import os
import zipfile
import subprocess
import sys

# Add the parent directory to the system path (otherwise the send_json.py can't be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tasks.common.send_json import send_json

load_dotenv()

ai_devs_3_api_key = getenv("AI_DEVS_3_API_KEY")
openai_api_key = getenv("OPEN_AI_API_KEY")
download_url = getenv("TASK_6_DOWNLOAD_URL")
submission_url = getenv("TASK_6_SUBMISSION_URL")
task_name = getenv("TASK_6_TASK_NAME")


def download_and_save_file(url, directory):
    """Download data from a URL and save it as a zip file, then extract it."""
    try:
        # Step 1: Download data from URL
        response = requests.get(url)
        response.raise_for_status()

        # Get original filename from URL or Content-Disposition header
        if "Content-Disposition" in response.headers:
            filename = response.headers["Content-Disposition"].split("filename=")[-1].strip('"')
        else:
            filename = url.split("/")[-1]

        # Step 2: Save the zip file with original name
        zip_path = os.path.join(directory, filename)
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Step 3: Create extraction directory using zip file name without extension
        extract_dir_name = os.path.splitext(filename)[0]
        extract_path = os.path.join(directory, extract_dir_name)
        os.makedirs(extract_path, exist_ok=True)
        
        # Step 4: Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            
        # Optional: Remove the zip file after extraction
        # os.remove(zip_path)
        
    except requests.RequestException as e:
        print(f"Error downloading data: {e}")
    except zipfile.BadZipFile as e:
        print(f"Error extracting zip file: {e}")


def run_bash_command(command):
    """Execute a bash command and return its output."""
    try:
        # Run the command and capture output
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e.stderr}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def process_files_in_directory(directory):
    """
    Run insanely-fast-whisper command for each .m4a file in the specified directory.
    """
    try:
        # Ensure translations directory exists
        os.makedirs("tasks/task_6/translations", exist_ok=True)
        
        # Get list of files in directory
        files = [f for f in os.listdir(directory) if f.endswith('.m4a')]
        
        # Process each file sequentially
        for filename in files:
            # Get filename without extension for the output file
            file_name_without_ext = os.path.splitext(filename)[0]
            
            # Create the command
            command = (
                f"insanely-fast-whisper "
                f"--device-id 0 "
                f"--transcript-path {os.getcwd()}/tasks/task_6/translations/{file_name_without_ext}.txt"
                f"--file-name {os.getcwd()}/tasks/task_6/przesluchania/{filename}"
            )
            
            print(f"Processing file: {filename}")
            output = run_bash_command(command)
            
            if output is not None:
                print(f"Successfully processed {filename}")
                print(output)
            else:
                print(f"Failed to process {filename}")
                
    except Exception as e:
        print(f"Error processing directory: {e}")


def collect_translations(translations_dir):
    """
    Collect translations from all .txt files in the translations directory
    and combine them into a single file with proper formatting.
    """
    try:
        # Get all .txt files in the translations directory
        files = [f for f in os.listdir(translations_dir) if f.endswith('.txt')]
        
        # Path for the collected translations file
        output_file = os.path.join(translations_dir, "translations_collected.txt")
        
        # Write all translations to the output file
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for filename in files:
                if filename == "translations_collected.txt":
                    continue
                    
                # Get the name without extension as the person's name
                name = os.path.splitext(filename)[0].capitalize()
                
                # Read the content of each translation file
                file_path = os.path.join(translations_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read().strip().split("\"text\": \"")[-1].replace("\"}", "")
                
                # Write formatted content to the output file
                outfile.write(f"{name}:\n\n{content}\n\n")
                
        print("Successfully collected all translations into translations_collected.txt")
        
    except Exception as e:
        print(f"Error collecting translations: {e}")


def call_openai(prompt: str):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}",
    }
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()

    # Extract the actual answer content
    answer_content = response_data["choices"][0]["message"]["content"]

    # Create directory if it doesn't exist
    os.makedirs("tasks/task_6", exist_ok=True)

    # Save response to a JSON file
    with open("tasks/task_6/GPT_response.json", "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    return answer_content


def create_submission_file(answer: str):
    # Create the submission structure
    submission_data = {
        "task": task_name,
        "apikey": ai_devs_3_api_key,
        "answer": answer
    }
    
    # Save the submission data to a new file
    with open("tasks/task_6/submission_file.json", "w") as file:
        json.dump(submission_data, file, indent=4)


def main():
    # download the zip file
    zip_voice_file_dir = "tasks/task_6/"
    download_and_save_file(download_url, zip_voice_file_dir)

    # process the voice files   
    voice_files_dir = "tasks/task_6/przesluchania"
    process_files_in_directory(voice_files_dir)

    # collect translations
    translations_dir = "tasks/task_6/translations"
    collect_translations(translations_dir)

    # Get the prompt instructions from the prompt.txt file
    with open('tasks/task_6/prompt.txt', 'r') as file:
        prompt_instructions = file.read()

    with open('tasks/task_6/translations/translations_collected.txt', 'r') as file:
        prompt_content = file.read()    

    prompt = prompt_instructions + "/n/n" + prompt_content

    # Ask OpenAI to answer the question
    answer = call_openai(prompt)
    print(answer)

    # Create the submission file
    create_submission_file(answer)

    # Path to the submission JSON file
    json_file_path = "tasks/task_6/submission_file.json"
    # Send the final version file to the submission URL
    send_json(submission_url, json_file_path)


if __name__ == "__main__":
    main()