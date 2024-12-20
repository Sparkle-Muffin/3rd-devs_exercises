import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import save_txt_file, read_file_content, save_json, download_file, read_json
from tasks.common.openai_utils import call_openai

from os import getenv
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import json


def main():
    # Initialize
    load_dotenv()
    openai_client = OpenAI()

    os.makedirs(Path(__file__).parent / "queries", exist_ok=True)
    os.makedirs(Path(__file__).parent / "responses", exist_ok=True)

    # Get information about photos
    query = {
        "task": getenv("TASK_16_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": "START"
    }
    photos_description_query_path = Path(__file__).parent / "queries" / "0_photos_description.json"
    save_json(query, photos_description_query_path)
    photos_description_response = send_json(getenv("TASK_16_PHOTOS_API"), photos_description_query_path)

    # Save response
    photos_description_response_path = Path(__file__).parent / "responses" / "0_photos_description.json"
    save_json(photos_description_response, photos_description_response_path)


    prompt = read_file_content(Path(__file__).parent / "queries" / "1_get_photos_urls_prompt.txt")
    photos_description = photos_description_response["message"]

    # Extract photos urls
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': photos_description}
    ]
    # response = call_openai(openai_client, messages)
    
    get_photos_urls_GPT_response_path = Path(__file__).parent / "responses" / "1_get_photos_urls_GPT_response.json"
    # response = json.loads(response.replace("```json", "").replace("```", ""))
    # save_json(response, get_photos_urls_GPT_response_path)


    original_photos_path = Path(__file__).parent / "original_photos"
    os.makedirs(original_photos_path, exist_ok=True)

    photo_urls = read_json(get_photos_urls_GPT_response_path)["photos"]
    photo_urls = [photo["photo_url"] for photo in photo_urls]
    
    # # Download photos
    # for photo_url in photo_urls:
    #     download_file(photo_url, original_photos_path)

    # Get action labels for photos
    prompt = read_file_content(Path(__file__).parent / "queries" / "2_photos_actions_prompt.txt")
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': "Images are attached."}
    ]
    photo_names = read_json(get_photos_urls_GPT_response_path)["photos"]
    photo_names = [photo["photo_name"] for photo in photo_names]
    photos = [str(original_photos_path / photo_name) for photo_name in photo_names]

    # response = call_openai(openai_client, messages, images=photos)

    photos_actions_GPT_response_path = Path(__file__).parent / "responses" / "2_photos_actions_GPT_response.json"
    # response = json.loads(response.replace("```json", "").replace("```", ""))
    # save_json(response, photos_actions_GPT_response_path)

    # Combine data from both JSON files
    photos_urls = read_json(get_photos_urls_GPT_response_path)["photos"]
    photos_actions = read_json(photos_actions_GPT_response_path)["photos"]
    
    combined_data = {
        "photos": [
            {
                "photo_name": url_data["photo_name"],
                "photo_url": url_data["photo_url"],
                "photo_action": action_data["photo_action"]
            }
            for url_data, action_data in zip(photos_urls, photos_actions)
        ]
    }
    
    photos_and_actions_path = Path(__file__).parent / "responses" / "3_photos_and_actions.json"
    # save_json(combined_data, photos_and_actions_path)


    # os.makedirs(Path(__file__).parent / "fixed_photos", exist_ok=True)

    fixed_photos = combined_data

    for photo in fixed_photos["photos"]:
        if photo["photo_action"] != "OK":
            query = {
                "task": getenv("TASK_16_TASK_NAME"),
                "apikey": getenv("AI_DEVS_3_API_KEY"),
                "answer": photo["photo_action"] + " " + photo["photo_name"]
            }
            response = send_json(getenv("TASK_16_PHOTOS_API"), query)
            print(response)

            prompt = read_file_content(Path(__file__).parent / "queries" / "1_get_photos_urls_prompt.txt")
            photos_description = response["message"]

            messages = [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': photos_description}
            ]
            response = call_openai(openai_client, messages)
            response = json.loads(response.replace("```json", "").replace("```", ""))
            photo["photo_name"] = response["photos"][0]["photo_name"]
            photo["photo_url"] = response["photos"][0]["photo_url"]


    fixed_photos_path = Path(__file__).parent / "responses" / "4_fixed_photos.json"
    save_json(fixed_photos, fixed_photos_path)


if __name__ == "__main__":
    main()
