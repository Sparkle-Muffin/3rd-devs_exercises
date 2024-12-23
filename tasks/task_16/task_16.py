from pathlib import Path
from common.file_utils import read_file_content, save_json, download_file, read_json, get_url_path_without_filename
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler
import os

task_name = os.getenv("TASK_16_TASK_NAME")
task_path = Path(__file__).parent
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
openai_msg_handler = OpenaiClient(task_path)


def main():
    # 0. Initialize
    prompts_dir = task_path / "prompts"
    program_files_dir = task_path / "program_files"
    program_files_dir.mkdir(parents=True, exist_ok=True)
    original_photos_dir = task_path / "original_photos"
    original_photos_dir.mkdir(parents=True, exist_ok=True)
    fixed_photos_dir = task_path / "fixed_photos"
    fixed_photos_dir.mkdir(parents=True, exist_ok=True)
    photos_description_path = program_files_dir / "photos_description.json"


    # 1. Get photos description from Centrala AI_devs
    centrala_photos_description = aidevs_msg_handler.ask_centrala_aidevs("START")


    # 2. Get photos names and urls using OpenAI
    prompt = read_file_content(prompts_dir / "get_photos_urls.txt")
    centrala_photos_description = centrala_photos_description["message"]
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': centrala_photos_description}
    ]
    response = openai_msg_handler.call_openai(messages, response_format={"type": "json_object"})
    save_json(response, photos_description_path)
    

    # 3. Download photos
    photos = read_json(photos_description_path)
    for photo in photos["photos"]:
        download_file(photo["photo_url"], original_photos_dir)
        photo["local_photo_path"] = download_file(photo["photo_url"], fixed_photos_dir)
    save_json(photos, photos_description_path)


    # 4. Set placeholder action for all photos
    for photo in photos["photos"]:
        photo["photo_action"] = "Placeholder"
    save_json(photos, photos_description_path)


    website_url = get_url_path_without_filename(photos["photos"][0]["photo_url"])
    while True:
        # 5. Get action labels for photos
        prompt = read_file_content(prompts_dir / "assess_photo_quality.txt")
        for photo in photos["photos"]:
            if photo["photo_action"] != "OK":
                photo_path = [photo["local_photo_path"]]
                messages = [
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': "Photo is attached."}
                ]
                response = openai_msg_handler.call_openai(messages, images=photo_path, response_format={"type": "json_object"})
                photo["photo_action"] = response["photo_action"]
        save_json(photos, photos_description_path)


        # 6. Check if all photos are OK
        all_photos_are_ok = True
        for photo in photos["photos"]:
            if photo["photo_action"] != "OK":
                all_photos_are_ok = False
                break
        if all_photos_are_ok == True:
            break


        # 7. Ask Centrala AI_devs to fix photos one by one
        for photo in photos["photos"]:
            if photo["photo_action"] != "OK":   
                query = photo["photo_action"] + " " + photo["photo_name"]
                centrala_photos_description = aidevs_msg_handler.ask_centrala_aidevs(query)

                # 8. Get photos names and urls using OpenAI
                prompt = read_file_content(prompts_dir / "get_photos_urls.txt")
                centrala_photos_description = centrala_photos_description["message"]
                centrala_photos_description = f"The website url is {website_url}. The photos description is: {centrala_photos_description}."
                messages = [
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': centrala_photos_description}
                ]
                response = openai_msg_handler.call_openai(messages, response_format={"type": "json_object"})
                photo["photo_name"] = response["photos"][0]["photo_name"]
                photo["photo_url"] = response["photos"][0]["photo_url"]


                # 9. Download photos
                photo["local_photo_path"] = download_file(photo["photo_url"], fixed_photos_dir)
        save_json(photos, photos_description_path)


    # 10. Use OpenAI to assess if the photo shows the face
    prompt = read_file_content(prompts_dir / "assess_if_photos_show_face.txt")
    for photo in photos["photos"]:
        photo_path = [photo["local_photo_path"]]
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': "Photo is attached."}
        ]
        response = openai_msg_handler.call_openai(messages, images=photo_path, response_format={"type": "json_object"})
        photo["photo_shows_face"] = response["photo_shows_face"]
    save_json(photos, photos_description_path)


    # 11. Ask OpenAI to make a person description
    prompt = read_file_content(prompts_dir / "make_person_description.txt")
    photos = [photo["local_photo_path"] for photo in photos["photos"] if photo["photo_shows_face"] == "1"]
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': "Photos are attached."}
    ]
    response = openai_msg_handler.call_openai(messages, images=photos)


    # 12. Send submission to Centrala AI_devs
    aidevs_msg_handler.ask_centrala_aidevs(response)


if __name__ == "__main__":
    main()
