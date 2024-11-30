import requests
from os import getenv
from dotenv import load_dotenv
import json
import os
import sys
import zipfile
import subprocess
import base64
from openai import OpenAI

# Add the parent directory to the system path (otherwise the send_json.py can't be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from send_json import send_json

load_dotenv()
client = OpenAI()

download_url = getenv("TASK_9_DOWNLOAD_URL")
ai_devs_3_api_key = getenv("AI_DEVS_3_API_KEY")
submission_url = getenv("TASK_9_SUBMISSION_URL")
task_name = getenv("TASK_9_TASK_NAME")

list_of_txt = []
list_of_mp3 = []
list_of_png = []


def download_zip_file(url):
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
        zip_path = os.path.join(os.path.dirname(__file__), filename)
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        return zip_path

    except requests.RequestException as e:
        print(f"Error downloading data: {e}")


def extract_file(zip_path):
    try:
        # Step 3: Create extraction directory using zip file name without extension
        extract_path = os.path.splitext(zip_path)[0]
        os.makedirs(extract_path, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            
        # Optional: Remove the zip file after extraction
        # os.remove(zip_path)

        return extract_path

    except zipfile.BadZipFile as e:
        print(f"Error extracting zip file: {e}")


def prepare_list_of_files(directory, file_type, list_of_files):
    # Step 4: Find all .txt files in the directory and save them in list_of_txt
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(file_type):
                list_of_files.append(os.path.join(root, file))

        print(f"List of {file_type} files: ")
        for file in list_of_files:
            print(file)
        break


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


def transform_mp3_to_txt_files(list_of_files, output_dir):
    """
    Run insanely-fast-whisper command for each .m4a file in the specified directory.
    """
    try:
        # Ensure translations directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each file sequentially
        for input_file_path in list_of_files:
            # Remove path's head
            input_file_name = os.path.split(input_file_path)[1]
            # Get file name without .mp3 extension and add .txt extension
            output_file_name = os.path.splitext(input_file_name)[0] + ".json"
            # Create a whole path for an output file
            output_file_path = os.path.join(output_dir, output_file_name)

            # Create the command
            command = (
                f"insanely-fast-whisper "
                f"--device-id 0 "
                f"--transcript-path {output_file_path} "
                f"--file-name {input_file_path}"
            )
            
            print(f"Processing file: {input_file_name}")
            output = run_bash_command(command)
            
            if output is not None:
                print(f"Successfully processed {input_file_name}")
                print(output)
            else:
                print(f"Failed to process {input_file_name}")
                
    except Exception as e:
        print(f"Error processing directory: {e}")


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  

def encode_images(image_paths):
    images = []
    for image_path in image_paths:
        base64_image = encode_image(image_path)
        images.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
            },
        )
    return images


def call_openai_with_images(prompt: str, images_dir: str, answer_file_path):
    image_paths = [
        os.path.join(images_dir, file)
        for file in os.listdir(images_dir)
        if file.endswith(('.png', '.jpg', '.jpeg'))
    ]

    print(image_paths)
    images = encode_images(image_paths)

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        *images
                    ],
                }
            ],
        )

    response_data = response.choices[0].message.content
    # Replace and assign back to original content
    response_data = response_data.replace("```json", "")
    response_data = response_data.replace("```", "")

    # Don't forget to convert to JSON as it is a string right now:
    json_result = json.loads(response_data)

    with open(answer_file_path, "w", encoding="utf-8") as f:
        json.dump(json_result, f, indent=2, ensure_ascii=False)

    return response_data


def call_openai(prompt: str, response_file_path: str):

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },                      
                    ],
                }
            ],
        )
    
    response_data = response.choices[0].message.content
    # Replace and assign back to original content
    response_data = response_data.replace("```json", "")
    response_data = response_data.replace("```", "")

    # Don't forget to convert to JSON as it is a string right now:
    json_result = json.loads(response_data)

    with open(response_file_path, "w", encoding="utf-8") as f:
        json.dump(json_result, f, indent=2, ensure_ascii=False)

    return response_data


def merge_all_files_into_json(translated_mp3_files_dir, images_to_text_file_path, all_files_merged_path):
    # Create a json file that gathers all downloaded files' content in it
    json_file = {}
    # Add txt files first
    for txt_file_path in list_of_txt:
        with open(txt_file_path, "r") as file:
            txt_file_name = os.path.split(txt_file_path)[1]
            txt_file_content = file.read()
            txt_file = {txt_file_name: txt_file_content}
            json_file.update(txt_file)

    # Then add mp3 files
    for root, dirs, files in os.walk(translated_mp3_files_dir):
        for filename in files:
            file = os.path.join(translated_mp3_files_dir, filename)
            with open(file, "r") as file:
                mp3_file_name = os.path.split(filename)[1]
                mp3_file_name = os.path.splitext(mp3_file_name)[0] + ".mp3"
                mp3_file_content = json.load(file)
                mp3_file = {mp3_file_name: mp3_file_content["text"]}
                json_file.update(mp3_file)
        break

    # Ultimately add png files
    with open(images_to_text_file_path, "r") as file:
        png_files_content = json.load(file)
        for i, key in enumerate(png_files_content):
            png_file_name = os.path.split(list_of_png[i])[1]
            png_file_content = png_files_content[key]
            png_file = {png_file_name: png_file_content}
            json_file.update(png_file)

    with open(all_files_merged_path, "w") as file:
        json.dump(json_file, file, indent=2, ensure_ascii=False)


def create_submission_file(files_classification_file_path, submission_file_path):
    with open(files_classification_file_path, "r") as file:
        answer = json.load(file)
    # Create the submission structure
    submission_data = {
        "task": task_name,
        "apikey": ai_devs_3_api_key,
        "answer": answer
    }
    
    # Save the submission data to a new file
    with open(submission_file_path, "w") as file:
        json.dump(submission_data, file, indent=4)


def main():
    # Download and extract zip file
    zip_path = download_zip_file(download_url)
    extract_path = extract_file(zip_path)
    
    # Create a list of all txt files
    prepare_list_of_files(extract_path, ".txt", list_of_txt)
    # Create a list of all mp3 files
    prepare_list_of_files(extract_path, ".mp3", list_of_mp3)
    # Create a list of all png files
    prepare_list_of_files(extract_path, ".png", list_of_png)

    # Use Whisper to translate audio files
    translated_mp3_files_dir = os.path.join(os.path.dirname(__file__), "translated_mp3_files")
    transform_mp3_to_txt_files(list_of_mp3, translated_mp3_files_dir)

    # Get the prompt instructions from the images_to_text_prompt.txt file
    with open(os.path.join(os.path.dirname(__file__), "images_to_text_prompt.txt"), 'r') as file:
        prompt = file.read()

    # Ask OpenAI to read text from images
    images_dir = os.path.join(os.path.dirname(__file__), "pliki_z_fabryki")
    images_to_text_file_path = os.path.join(os.path.dirname(__file__), "GPT_images_to_text.json")
    response = call_openai_with_images(prompt, images_dir, images_to_text_file_path)
    print(response)

    all_files_merged_path = os.path.join(os.path.dirname(__file__), "all_files_merged.json")
    merge_all_files_into_json(translated_mp3_files_dir, images_to_text_file_path, all_files_merged_path)

    # Get the prompt instructions from files_classification_prompt.txt file
    with open(os.path.join(os.path.dirname(__file__), "files_classification_prompt.txt"), 'r') as file:
        system_prompt = file.read()
    # Get the prompt content from all_files_merged.json file
    with open(os.path.join(os.path.dirname(__file__), "all_files_merged.json"), 'r') as file:
        user_prompt = file.read()
    # Ask OpenAI to classify the files
    response = call_openai(system_prompt, user_prompt, "GPT_files_classification.json")
    print(response)

    # Get the prompt instructions from files_classification_prompt.txt file
    with open(os.path.join(os.path.dirname(__file__), "files_classification_prompt.txt"), 'r') as file:
        system_prompt = file.read()
    # Get the prompt content from all_files_merged.json file
    with open(os.path.join(os.path.dirname(__file__), "all_files_merged.json"), 'r') as file:
        user_prompt = file.read()

    prompt = system_prompt + "/n/n" + user_prompt
    # Call OpenAI
    files_classification_file_path = os.path.join(os.path.dirname(__file__), "GPT_files_classification.json")
    response = call_openai(prompt, files_classification_file_path)
    print(response)

    submission_file_path = os.path.join(os.path.dirname(__file__), "submission_file.json")
    create_submission_file(files_classification_file_path, submission_file_path)

    # Send the submission file
    send_json(submission_url, submission_file_path)


if __name__ == "__main__":
    main()