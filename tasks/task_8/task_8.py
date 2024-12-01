import requests
from os import getenv
from dotenv import load_dotenv
import json
import os
import sys
from openai import OpenAI

# Add the parent directory to the system path (otherwise the send_json.py can't be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tasks.common.send_json import send_json

load_dotenv()

download_url = getenv("TASK_8_DOWNLOAD_URL")
openai_api_key = getenv("OPEN_AI_API_KEY")
ai_devs_3_api_key = getenv("AI_DEVS_3_API_KEY")
submission_url = getenv("TASK_8_SUBMISSION_URL")
task_name = getenv("TASK_8_TASK_NAME")
image_file_url = getenv("TASK_8_IMAGE_URL")

# Path to the submission JSON file
submission_file_path = "tasks/task_8/submission_file.json"


def get_json_content(url, key_name):
    try:
        # Request the page content
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for failed requests

        # Get original filename from URL or Content-Disposition header
        if "Content-Disposition" in response.headers:
            filename = response.headers["Content-Disposition"].split("filename=")[-1].strip('"')
        else:
            filename = url.split("/")[-1]
        # Decode the response content to a string
        decoded_content = response.content.decode('utf-8')
        
        # Save the decoded content to a file
        with open(os.path.join(os.path.dirname(__file__), filename), "w") as file:
            json.dump(json.loads(decoded_content), file, indent=4)  # Parse JSON and dump to file

        # Extract the value associated with key_name
        json_content = json.loads(decoded_content).get(key_name)  # Get the value for key_name
        return json_content  # Return the extracted content

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

client = OpenAI()

def call_openai(prompt: str, response_file_name: str):

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

    print(response.choices[0])

    with open(os.path.join(os.path.dirname(__file__), response_file_name), "w", encoding="utf-8") as f:
        response_data = response.model_dump_json()
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    response_content = response.choices[0].message.content
    return response_content


def call_dalle(prompt: str, image_name: str):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url

    # Download the image from the image_url
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        # Save the image to a file
        with open(os.path.join(os.path.dirname(__file__), image_name), "wb") as img_file:
            img_file.write(image_response.content)  # Write the image content to the file
    else:
        print(f"Failed to download image: {image_response.status_code}")

    return image_url


def create_submission_file(answer: str):
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
    # Get image description
    image_description = get_json_content(download_url, "description")
    print(image_description)
    # Get the prompt instructions from the prompt.txt file
    with open(os.path.join(os.path.dirname(__file__), 'prompt.txt'), 'r') as file:
        prompt_instructions = file.read()

    prompt = prompt_instructions + "\n\n" + image_description
    keywords = call_openai(prompt, "GPT_image_keywords.json")

    image_url = call_dalle(keywords, "robot_image.png")

    # Create the submission file
    create_submission_file(image_url)
    # Send the submission file
    send_json(submission_url, submission_file_path)


if __name__ == "__main__":
    main()