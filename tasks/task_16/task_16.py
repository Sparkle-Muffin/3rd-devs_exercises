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
from os import listdir


def ask_centrala_aidevs(message, query_path, response_path):
    query = {
        "task": getenv("TASK_16_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": message
    }
    # Save query
    if query_path:  
        save_json(query, query_path)
    # Send query
    response = send_json(getenv("TASK_16_PHOTOS_API"), query)
    # Save response
    if response_path:
        save_json(response, response_path)

    print(response)
    return json.loads(response)


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


def main():
    # 0. Initialize
    load_dotenv()
    openai_client = OpenAI()

    prompts_dir = os.makedirs(Path(__file__).parent / "prompts", exist_ok=True)
    openai_responses_dir = os.makedirs(Path(__file__).parent / "openai_responses", exist_ok=True)
    centrala_queries_dir = os.makedirs(Path(__file__).parent / "centrala_queries", exist_ok=True)
    centrala_responses_dir = os.makedirs(Path(__file__).parent / "centrala_responses", exist_ok=True)
    program_files_dir = os.makedirs(Path(__file__).parent / "program_files", exist_ok=True)
    original_photos_dir = os.makedirs(Path(__file__).parent / "original_photos", exist_ok=True)
    fixed_photos_dir = os.makedirs(Path(__file__).parent / "fixed_photos", exist_ok=True)

    photos_description_path = program_files_dir / "photos_description.json"
    person_description_path = program_files_dir / "person_description.json"
    queries_counter = 0


    # 1. Get photos description from Centrala AI_devs
    query_path = centrala_queries_dir / f"{queries_counter}_photos_description.json"
    response_path = centrala_responses_dir / f"{queries_counter}_photos_description.json"
    centrala_photos_description = ask_centrala_aidevs("START", query_path, response_path)
    queries_counter += 1


    # 2. Get photos names and urls using OpenAI
    prompt = read_file_content(prompts_dir / "get_photos_urls.txt")
    centrala_photos_description = centrala_photos_description["message"]
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': centrala_photos_description}
    ]
    response_path = openai_responses_dir / f"{queries_counter}_get_photos_urls.json"
    response = call_openai(openai_client, messages, response_format={"type": "json_object"}, response_path=response_path)
    save_json(response, photos_description_path)
    queries_counter += 1
    

    # 3. Download photos
    photos = read_json(photos_description_path)["photos"]
    for photo in photos:
        download_file(photo["photo_url"], original_photos_dir / photo["photo_name"])
        download_file(photo["photo_url"], fixed_photos_dir / photo["photo_name"])


    while True:
        # 4. Get action labels for photos
        prompt = read_file_content(prompts_dir / "assess_photos_quality.txt")
        photos = [photo for photo in listdir(original_photos_dir)]
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': None}
        ]
        response_path = openai_responses_dir / f"{queries_counter}_assess_photos_quality.json"
        response = call_openai(openai_client, messages, images=photos, response_format={"type": "json_object"}, response_path=response_path)
        queries_counter += 1


        # 5. Combine data from both JSON files
        photos_description = read_json(photos_description_path)
        photos_actions = response
        combined_data = combine_json_files(photos_description, photos_actions, photos_description_path)
        website_url = combined_data["photos"][0]["photo_url"]


        # 6. Check if all photos are OK
        all_photos_are_ok = True
        for photo in combined_data["photos"]:
            if photo["photo_action"] != "OK":
                all_photos_are_ok = False
                break

        if all_photos_are_ok == True:
            break


        # 7. Ask Centrala AI_devs to fix photos one by one
        for photo in combined_data["photos"]:
            if photo["photo_action"] != "OK":   
                query_path = centrala_queries_dir / f"{queries_counter}_photos_description.json"
                response_path = centrala_responses_dir / f"{queries_counter}_photos_description.json"
                centrala_photos_description = ask_centrala_aidevs("START", query_path, response_path)
                queries_counter += 1

                # 8. Get photos names and urls using OpenAI
                prompt = read_file_content(prompts_dir / "get_photos_urls.txt")
                centrala_photos_description = centrala_photos_description["message"]
                centrala_photos_description = f"The website url is {website_url}. The photos description is: {centrala_photos_description}."
                messages = [
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': centrala_photos_description}
                ]
                response_path = openai_responses_dir / f"{queries_counter}_get_photos_urls.json"
                response = call_openai(openai_client, messages, response_format={"type": "json_object"}, response_path=response_path)
                photo["photo_name"] = response["photos"][0]["photo_name"]
                photo["photo_url"] = response["photos"][0]["photo_url"]
                queries_counter += 1


                # 9. Download photos
                download_file(photo["photo_url"], fixed_photos_dir / photo["photo_name"])


    # 10. Use OpenAI to assess if the photo shows the face
    prompt = read_file_content(prompts_dir / "assess_if_photos_show_faces.txt")
    photos = [photo for photo in listdir(fixed_photos_dir)]
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': None}
    ]
    response_path = openai_responses_dir / f"{queries_counter}_assess_if_photos_show_faces.json"
    response = call_openai(openai_client, messages, images=photos, response_format={"type": "json_object"}, response_path=response_path)
    queries_counter += 1


    # 11. Combine data from both JSON files
    photos_description = read_json(photos_description_path)
    photos_faces = response
    combined_data = combine_json_files(photos_description, photos_faces, photos_description_path)


    # 12. Ask OpenAI to make a person description
    prompt = read_file_content(prompts_dir / "make_person_description.txt")
    photos = [photo for photo in listdir(fixed_photos_dir)]
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': "Images are attached."}
    ]
    response_path = openai_responses_dir / f"{queries_counter}_make_person_description.txt"
    response = call_openai(openai_client, messages, images=photos, response_path=response_path)
    queries_counter += 1


    # 13. Send submission to Centrala AI_devs
    query_path = centrala_queries_dir / f"{queries_counter}_submission.json"
    response_path = centrala_responses_dir / f"{queries_counter}_submission.json"
    ask_centrala_aidevs(response, query_path, response_path)


if __name__ == "__main__":
    main()
